from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import httpx
import streamlit as st


@dataclass(frozen=True)
class ChatTurn:
    role: str  # "user" | "assistant"
    content: str
    citations: list[dict[str, Any]] | None = None


def _api(base: str) -> httpx.Client:
    return httpx.Client(base_url=base.rstrip("/"), timeout=60.0)


def _list_kbs(client: httpx.Client) -> list[dict[str, Any]]:
    r = client.get("/v1/kbs")
    r.raise_for_status()
    return list(r.json())


def _create_kb(client: httpx.Client, *, name: str, description: str | None) -> dict[str, Any]:
    r = client.post("/v1/kbs", json={"name": name, "description": description})
    r.raise_for_status()
    return dict(r.json())


def _upload_doc(
    client: httpx.Client,
    *,
    kb_id: str,
    uploaded: Any,
    user_meta: dict[str, Any] | None,
) -> dict[str, Any]:
    files = {"file": (uploaded.name, uploaded.getvalue(), uploaded.type or "application/octet-stream")}
    data: dict[str, str] = {}
    if user_meta is not None:
        data["user_meta_json"] = json.dumps(user_meta, ensure_ascii=False)
    r = client.post(f"/v1/kbs/{kb_id}/documents", files=files, data=data)
    r.raise_for_status()
    return dict(r.json())


def _query(
    client: httpx.Client,
    *,
    kb_id: str,
    message: str,
    top_k: int,
    provider: dict[str, Any],
    filters: dict[str, Any] | None,
    system_preamble: str | None,
    temperature: float,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "kb_id": kb_id,
        "message": message,
        "top_k": top_k,
        "provider_config": provider,
        "filters": filters,
        "system_preamble": system_preamble,
        "temperature": temperature,
    }
    r = client.post("/v1/query", json=payload)
    r.raise_for_status()
    return dict(r.json())


def _render_citations(citations: list[dict[str, Any]]) -> None:
    if not citations:
        st.caption("No citations returned.")
        return
    for i, c in enumerate(citations, start=1):
        score = c.get("score")
        doc_id = c.get("doc_id")
        chunk_id = c.get("chunk_id")
        with st.expander(f"Citation {i} — score={score:.4f} doc={doc_id} chunk={chunk_id}"):
            st.write(c.get("snippet", ""))
            st.json(c.get("metadata", {}))


def main() -> None:
    st.set_page_config(page_title="RAG Storyteller", layout="wide")

    st.sidebar.title("RAG Storyteller")

    api_base = st.sidebar.text_input("Backend URL", value="http://127.0.0.1:8000")
    top_k = st.sidebar.slider("Top K", min_value=1, max_value=30, value=6, step=1)
    temperature = st.sidebar.slider("Temperature", min_value=0.0, max_value=2.0, value=0.7, step=0.1)
    show_citations = st.sidebar.toggle("Show citations", value=True)

    st.sidebar.subheader("Provider (OpenAI-compatible)")
    provider_base_url = st.sidebar.text_input("Provider base_url", value="https://api.openai.com")
    provider_api_key = st.sidebar.text_input("Provider api_key", value="", type="password")
    provider_model = st.sidebar.text_input("Model", value="gpt-4o-mini")

    system_preamble = st.sidebar.text_area(
        "System preamble (optional)",
        value="",
        placeholder="Extra instructions to prepend to the storyteller system prompt.",
        height=120,
    )

    st.title("RAG Storyteller")
    st.caption("Create a knowledge base, upload world docs, then chat with RAG-backed citations.")

    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "kb_id" not in st.session_state:
        st.session_state.kb_id = None

    with _api(api_base) as client:
        # KB management
        try:
            kbs = _list_kbs(client)
        except Exception as e:  # noqa: BLE001
            st.error(f"Backend not reachable: {e}")
            st.stop()

        st.sidebar.subheader("Knowledge bases")
        kb_label_to_id = {f"{kb['name']} ({kb['id']})": kb["id"] for kb in kbs}

        if kb_label_to_id:
            labels = list(kb_label_to_id.keys())
            default_idx = 0
            selected = st.sidebar.selectbox("Select KB", options=labels, index=default_idx)
            st.session_state.kb_id = kb_label_to_id[selected]
        else:
            st.sidebar.info("No KBs yet. Create one below.")
            st.session_state.kb_id = None

        with st.sidebar.expander("Create KB", expanded=not bool(kb_label_to_id)):
            new_name = st.text_input("Name", value="my-world")
            new_desc = st.text_area("Description", value="", height=80)
            if st.button("Create", type="primary"):
                created = _create_kb(client, name=new_name.strip(), description=new_desc.strip() or None)
                st.success(f"Created KB: {created['id']}")
                st.rerun()

        kb_id = st.session_state.kb_id
        if not kb_id:
            st.info("Create a knowledge base from the sidebar to continue.")
            st.stop()

        # Upload documents
        st.subheader("Upload documents")
        uploaded = st.file_uploader(
            "Upload .txt/.md/.html/.pdf/.json (any file will be attempted as text fallback)",
            type=None,
        )
        user_meta_text = st.text_area(
            "Optional user metadata (JSON)",
            value="",
            placeholder='{"source":"wiki","tag":"locations"}',
            height=80,
        )
        if st.button("Ingest upload") and uploaded is not None:
            meta = json.loads(user_meta_text) if user_meta_text.strip() else None
            res = _upload_doc(client, kb_id=kb_id, uploaded=uploaded, user_meta=meta)
            st.success(f"Ingested doc_id={res['doc_id']} chunks={res['chunk_count']}")

        st.divider()

        # Chat
        st.subheader("Chat")
        if st.button("Clear chat"):
            st.session_state.messages = []
            st.rerun()

        for msg in st.session_state.messages:
            with st.chat_message(msg.role):
                st.write(msg.content)
                if show_citations and msg.role == "assistant" and msg.citations is not None:
                    _render_citations(msg.citations)

        user_text = st.chat_input("Ask for a story, a scene, or a rewrite…")
        if not user_text:
            return

        st.session_state.messages.append(ChatTurn(role="user", content=user_text))
        with st.chat_message("assistant"):
            with st.spinner("Retrieving + generating…"):
                provider = {
                    "base_url": provider_base_url.strip(),
                    "api_key": provider_api_key,
                    "model": provider_model.strip(),
                    "extra_headers": None,
                }
                out = _query(
                    client,
                    kb_id=kb_id,
                    message=user_text,
                    top_k=top_k,
                    provider=provider,
                    filters=None,
                    system_preamble=system_preamble.strip() or None,
                    temperature=temperature,
                )
                answer = out.get("answer", "")
                citations = out.get("citations", []) or []
                st.write(answer)
                if show_citations:
                    _render_citations(citations)

        st.session_state.messages.append(
            ChatTurn(role="assistant", content=answer, citations=list(citations))
        )


if __name__ == "__main__":
    main()
