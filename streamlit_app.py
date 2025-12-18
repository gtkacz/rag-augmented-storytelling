from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import streamlit as st

from app.core.settings import settings
from app.db import crud
from app.db.session import SessionLocal, init_db
from app.llms.gemini import GeminiClient
from app.rag.prompting import build_storyteller_system_prompt, build_user_prompt


@dataclass
class ChatTurn:
    role: str  # "user" | "assistant"
    content: str
    contexts: list[dict[str, Any]] | None = None


@st.cache_resource
def _bootstrap() -> None:
    """Initialize local storage + DB once per Streamlit session.

    IMPORTANT: Avoid importing heavy/fragile deps at module import time.
    """
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.kb_files_dir.mkdir(parents=True, exist_ok=True)
    settings.chroma_dir.mkdir(parents=True, exist_ok=True)
    init_db()


@st.cache_resource
def _get_retriever():
    """Create RetrievalService lazily (may fail if vectorstore deps are misinstalled)."""
    from app.rag.retriever import RetrievalService  # local import on purpose

    return RetrievalService()


def _list_kbs() -> list[dict[str, Any]]:
    with SessionLocal() as session:
        kbs = crud.list_kbs(session)
        return [
            {
                "id": kb.id,
                "name": kb.name,
                "description": kb.description,
                "created_at": kb.created_at,
            }
            for kb in kbs
        ]


def _create_kb(name: str, description: str | None) -> str:
    with SessionLocal() as session:
        kb = crud.create_kb(session, name=name, description=description)
        return kb.id


def _render_contexts(contexts: list[dict[str, Any]]) -> None:
    if not contexts:
        st.caption("No retrieved contexts.")
        return

    for i, c in enumerate(contexts, start=1):
        citation = c.get("citation") or c.get("id")
        score = c.get("score")
        with st.expander(f"Context {i} — {citation} (score: {score})"):
            st.write(c.get("text", ""))
            meta = c.get("meta")
            if meta:
                st.json(meta)


def main() -> None:
    st.set_page_config(page_title="RAG Storyteller", layout="wide")

    _bootstrap()

    if "messages" not in st.session_state:
        st.session_state.messages: list[ChatTurn] = []

    st.sidebar.title("RAG Storyteller")

    # KB selection / creation
    kbs = _list_kbs()
    if not kbs:
        st.sidebar.info("No knowledge bases yet. Create one to start chatting.")
        name = st.sidebar.text_input("New KB name", value="my-kb")
        desc = st.sidebar.text_area("Description (optional)", value="")
        if st.sidebar.button("Create KB", type="primary"):
            kb_id = _create_kb(name=name.strip(), description=desc.strip() or None)
            st.session_state.kb_id = kb_id
            st.sidebar.success(f"Created KB: {kb_id}")
            st.rerun()
        st.title("Chat")
        st.write("Create a knowledge base from the sidebar to begin.")
        return

    kb_options = {f"{kb['name']} ({kb['id']})": kb["id"] for kb in kbs}
    default_label = next(iter(kb_options.keys()))
    kb_label = st.sidebar.selectbox("Knowledge base", options=list(kb_options.keys()), index=0)
    kb_id = kb_options.get(kb_label, kb_options[default_label])
    st.session_state.kb_id = kb_id

    top_k = st.sidebar.slider("Top K contexts", min_value=1, max_value=20, value=6, step=1)
    show_contexts = st.sidebar.toggle("Show retrieved contexts", value=True)

    if st.sidebar.button("Clear chat"):
        st.session_state.messages = []
        st.rerun()

    st.title("Chat")
    st.caption(f"Using KB: {kb_label}")

    # Render chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg.role):
            st.write(msg.content)
            if show_contexts and msg.role == "assistant" and msg.contexts is not None:
                _render_contexts(msg.contexts)

    user_text = st.chat_input("Ask for a story, a scene, or a rewrite...")
    if not user_text:
        return

    st.session_state.messages.append(ChatTurn(role="user", content=user_text))

    # Generate response (no internal API calls; direct backend imports)
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                # Retrieval is optional: if vectorstore/embedding deps fail, still let chat work.
                try:
                    retriever = _get_retriever()
                    contexts = retriever.retrieve(kb_id=kb_id, question=user_text, top_k=top_k, where=None)
                except Exception as e:  # noqa: BLE001
                    contexts = []
                    st.warning(f"Retrieval disabled (vectorstore init failed): {e}")
                system = build_storyteller_system_prompt()
                user_prompt = build_user_prompt(user_text, contexts=contexts)
                client = GeminiClient()
                answer = client.generate(system=system, user=user_prompt)
            except Exception as e:  # noqa: BLE001
                answer = f"Error: {e}"
                contexts = []

            st.write(answer)
            if show_contexts:
                _render_contexts(contexts)

    st.session_state.messages.append(ChatTurn(role="assistant", content=answer, contexts=contexts))


if __name__ == "__main__":
    main()
