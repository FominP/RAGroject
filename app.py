from __future__ import annotations

import hashlib
import logging
import os

import streamlit as st

from src.chunking import chunk_pages
from src.embeddings import FastEmbedder
from src.generation import GeminiClient, GenerationError, answer_question
from src.pdf_parser import PDFError, parse_pdf
from src.retrieval import VectorIndex

DEFAULT_EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
DEFAULT_GEMINI_MODEL = "gemini-2.5-flash-lite"
MAX_QUESTIONS_PER_SESSION = 10
logger = logging.getLogger(__name__)


def get_setting(name: str, default: str = "") -> str:
    """Read configuration without requiring a local Streamlit secrets file."""
    environment_value = os.getenv(name)
    if environment_value:
        return environment_value.strip()
    try:
        value = st.secrets.get(name, default)
    except (FileNotFoundError, AttributeError):
        value = default
    return str(value).strip()


@st.cache_resource(show_spinner=False)
def load_embedder(model_name: str) -> FastEmbedder:
    return FastEmbedder(model_name=model_name)


def reset_document() -> None:
    for key in (
        "document_fingerprint",
        "document_name",
        "index",
        "messages",
        "page_count",
        "question_count",
    ):
        st.session_state.pop(key, None)


def show_sources(sources: list[dict[str, object]]) -> None:
    if not sources:
        return
    with st.expander("Sources used", expanded=False):
        for source in sources:
            st.markdown(
                f"**Page {source['page']} · relevance {source['score']:.2f}**"
            )
            st.caption(str(source["text"]))


st.set_page_config(
    page_title="Grounded PDF Q&A",
    page_icon="📚",
    layout="wide",
)

st.title("📚 Grounded PDF Q&A")
st.markdown(
    "Ask questions about a PDF and get answers grounded in retrieved passages, "
    "with page-level citations."
)

embedding_model = get_setting("EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL)
gemini_model = get_setting("GEMINI_MODEL", DEFAULT_GEMINI_MODEL)
hosted_api_key = get_setting("GEMINI_API_KEY")

with st.sidebar:
    st.header("Document")
    uploaded_file = st.file_uploader("Upload a PDF", type=("pdf",))

    current_fingerprint = (
        hashlib.sha256(uploaded_file.getvalue()).hexdigest()
        if uploaded_file is not None
        else None
    )
    if (
        current_fingerprint
        and st.session_state.get("document_fingerprint")
        and current_fingerprint != st.session_state.document_fingerprint
    ):
        reset_document()

    process_document = st.button(
        "Build retrieval index",
        type="primary",
        use_container_width=True,
        disabled=uploaded_file is None,
    )
    if st.button(
        "Clear document from session",
        use_container_width=True,
        disabled=st.session_state.get("index") is None,
    ):
        reset_document()
        st.rerun()

    st.divider()
    st.header("Generation")
    if hosted_api_key:
        api_key = hosted_api_key
        st.success("Hosted Gemini key configured")
    else:
        api_key = st.text_input(
            "Gemini API key",
            type="password",
            help="Kept only in the active app session and never written to disk.",
        ).strip()

    top_k = st.slider("Retrieved passages", min_value=3, max_value=10, value=6)
    st.caption(f"LLM: `{gemini_model}`")
    st.caption(f"Embeddings: `{embedding_model}`")

    st.divider()
    st.warning(
        "Do not upload confidential documents. Retrieved passages are sent to "
        "the configured Gemini API when an answer is generated."
    )

if process_document and uploaded_file is not None:
    try:
        with st.spinner("Extracting and chunking the PDF..."):
            pdf_bytes = uploaded_file.getvalue()
            pages = parse_pdf(pdf_bytes)
            chunks = chunk_pages(pages)

        with st.spinner("Loading the embedding model and building the index..."):
            embedder = load_embedder(embedding_model)
            index = VectorIndex.build(chunks, embedder)

        st.session_state.document_fingerprint = hashlib.sha256(pdf_bytes).hexdigest()
        st.session_state.document_name = uploaded_file.name
        st.session_state.index = index
        st.session_state.messages = []
        st.session_state.page_count = len(pages)
        st.session_state.question_count = 0
        st.success("Retrieval index is ready.")
    except (PDFError, ValueError) as exc:
        st.error(str(exc))
    except Exception:
        logger.exception("Failed to build the document retrieval index")
        st.error(
            "The embedding model could not be loaded. Check the deployment "
            "logs and network access, then try again."
        )

index: VectorIndex | None = st.session_state.get("index")

if index is None:
    st.info(
        "Upload a text-based PDF and build its retrieval index to begin. "
        "Scanned documents require OCR and are not supported yet."
    )
else:
    col1, col2, col3 = st.columns(3)
    col1.metric("Document", st.session_state.document_name)
    col2.metric("Pages with text", st.session_state.page_count)
    col3.metric("Indexed passages", len(index.chunks))

    for message in st.session_state.get("messages", []):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            show_sources(message.get("sources", []))

    limit_reached = st.session_state.get("question_count", 0) >= MAX_QUESTIONS_PER_SESSION
    question = st.chat_input(
        "Ask a question about the document",
        disabled=limit_reached,
    )

    if limit_reached:
        st.info(
            "This session reached the demo limit. Upload the document again to "
            "start a new session."
        )

    if question:
        st.session_state.messages.append({"role": "user", "content": question})
        st.session_state.question_count = st.session_state.get("question_count", 0) + 1

        with st.spinner("Retrieving relevant passages..."):
            retrieved = index.search(question, top_k=top_k)

        source_data = [
            {
                "page": item.chunk.page_number,
                "score": item.score,
                "text": item.chunk.text,
            }
            for item in retrieved
        ]

        if not api_key:
            response_text = (
                "The relevant passages were retrieved below, but no Gemini API "
                "key is configured. Add a key in the sidebar to generate a "
                "grounded answer."
            )
        else:
            try:
                with st.spinner("Generating a grounded answer..."):
                    client = GeminiClient(api_key=api_key, model=gemini_model)
                    response_text = answer_question(client, question, retrieved)
            except GenerationError as exc:
                response_text = f"Generation failed: {exc}"

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": response_text,
                "sources": source_data,
            }
        )
        st.rerun()
