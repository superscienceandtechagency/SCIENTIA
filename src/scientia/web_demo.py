"""Local-only Streamlit demo for SCIENTIA PDF retrieval."""

from html import escape
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4

import streamlit as st
import streamlit.components.v1 as components

from scientia.pdf_ingestion import PdfIngestionError
from scientia.synthesis import ResearchQuestion
from scientia.workflow import MAX_RESEARCH_PDF_COUNT, prepare_research

st.set_page_config(
    page_title="SCIENTIA | Research Intelligence",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    :root {
        color-scheme: dark;
    }

    .stApp {
        background:
            radial-gradient(ellipse at 8% 0%, rgba(34, 211, 238, .10), transparent 30%),
            radial-gradient(ellipse at 95% 12%, rgba(99, 102, 241, .12),
                            transparent 28%),
            #080d19;
        color: #e8eef8;
    }

    .block-container {
        max-width: 1220px;
        padding-top: 2.5rem;
        padding-bottom: 3rem;
    }

    [data-testid="stSidebar"] {
        background: #0b1220;
        border-right: 1px solid #1e293b;
    }

    .hero {
        position: relative;
        overflow: hidden;
        padding: 2.6rem 2.5rem;
        border: 1px solid rgba(103, 232, 249, .20);
        border-radius: 24px;
        background:
            radial-gradient(ellipse at 100% 0%, rgba(34, 211, 238, .13),
                            transparent 42%),
            linear-gradient(135deg, #111d35 0%, #0d1526 70%, #111827 100%);
        margin-bottom: 2rem;
        box-shadow: 0 20px 60px rgba(0, 0, 0, .18);
    }

    .eyebrow {
        display: inline-block;
        color: #67e8f9;
        font-size: .76rem;
        font-weight: 750;
        letter-spacing: .18em;
        text-transform: uppercase;
    }

    .hero h1 {
        font-size: clamp(2.5rem, 6vw, 4rem);
        font-weight: 800;
        letter-spacing: -.055em;
        line-height: 1.08;
        margin: .75rem 0;
        color: #f8fafc;
    }

    .hero p {
        max-width: 700px;
        color: #b7c5dc;
        font-size: 1.06rem;
        line-height: 1.8;
        margin-bottom: 0;
    }

    h2, h3 {
        letter-spacing: -.025em;
        color: #f1f5f9;
    }

    div[data-testid="stTextArea"] textarea,
    div[data-testid="stTextInput"] input {
        background: #0d1628;
        border: 1px solid #2a3952;
        border-radius: 12px;
        color: #e8eef8;
    }

    div[data-testid="stFileUploader"] section {
        background: rgba(13, 22, 40, .72);
        border: 1px dashed #3b506e;
        border-radius: 16px;
    }

    div[data-testid="stSlider"] [data-baseweb="slider"] {
        padding-top: .35rem;
    }

    div.stButton > button[kind="primary"] {
        min-height: 3rem;
        border: 1px solid #67e8f9;
        border-radius: 12px;
        background: linear-gradient(110deg, #0891b2, #2563eb);
        color: white;
        font-weight: 700;
        transition: filter .2s ease, transform .2s ease;
    }

    div.stButton > button[kind="primary"]:hover {
        filter: brightness(1.12);
        transform: translateY(-1px);
    }

    div[data-testid="stMetric"] {
        background: linear-gradient(145deg, #111d35, #0d1628);
        padding: 1.2rem;
        border: 1px solid #263752;
        border-radius: 16px;
    }

    div[data-testid="stMetricLabel"] {
        color: #9fb0ca;
    }

    div[data-testid="stMetricValue"] {
        color: #f8fafc;
        font-weight: 750;
    }

    .result-card {
        border: 1px solid #263752;
        border-radius: 17px;
        padding: 1.35rem 1.45rem;
        margin: .9rem 0;
        background: linear-gradient(
            145deg, rgba(17, 29, 53, .92), rgba(11, 18, 32, .92)
        );
        box-shadow: 0 10px 30px rgba(0, 0, 0, .12);
    }

    .result-meta {
        display: flex;
        flex-wrap: wrap;
        gap: .45rem;
        color: #67e8f9;
        font-size: .76rem;
        font-weight: 750;
        letter-spacing: .065em;
        line-height: 1.8;
    }

    .result-card h4 {
        color: #f1f5f9;
        font-size: 1.08rem;
        font-weight: 700;
        margin: .85rem 0;
        overflow-wrap: anywhere;
    }

    .result-text {
        color: #cbd5e1;
        font-size: .96rem;
        line-height: 1.9;
        white-space: pre-wrap;
        overflow-wrap: anywhere;
    }

    .result-card h4 {
        color: #f1f5f9;
        font-size: 1.05rem;
        margin: .8rem 0;
        overflow-wrap: anywhere;
    }

    .result-text {
        color: #cbd5e1;
        line-height: 1.85;
        white-space: pre-wrap;
        overflow-wrap: anywhere;
    }

    div[data-testid="stAlert"] {
        border-radius: 12px;
    }

    hr {
        border-color: #243249;
    }

    @media (max-width: 640px) {
        .block-container {
            padding-top: 1.2rem;
            padding-left: 1rem;
            padding-right: 1rem;
        }

        .hero {
            padding: 1.6rem 1.25rem;
            border-radius: 18px;
        }

        .hero h1 {
            font-size: 2.5rem;
        }

        .hero p {
            font-size: .98rem;
        }

        .result-card {
            padding: 1rem;
        }
    }

    @media (prefers-reduced-motion: reduce) {
        *, *::before, *::after {
            transition-duration: 0.01ms !important;
            animation-duration: 0.01ms !important;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
      <div class="eyebrow">Research intelligence · Local demo</div>
      <h1>SCIENTIA</h1>
      <p>Explore your research PDFs. Retrieve ranked passages with page-level
      references using SCIENTIA's existing retrieval engine.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("## 🔬 SCIENTIA")
    st.caption("Research workspace")
    st.markdown("---")
    st.markdown("**How it works**")
    st.markdown(
        "1. Upload research PDFs\n"
        "2. Ask a focused question\n"
        "3. Inspect ranked passages\n"
        "4. Follow the source page"
    )
    st.markdown("---")
    st.caption("Local demo · No account required")
    st.caption("Results are retrieval matches, not verified scientific conclusions.")

st.markdown(
    """
    <div style="margin: 2rem 0 1.25rem;">
      <div class="eyebrow">Your workspace</div>
      <h2 style="margin: .4rem 0; font-size: 1.7rem;">
        Search your documents
      </h2>
      <p style="color: #9fb0ca; line-height: 1.7; margin-bottom: 0;">
        Upload your PDFs, ask a focused question, and explore ranked
        passages with page-level source references.
      </p>
    </div>
    """,
    unsafe_allow_html=True,
)

uploaded_files = st.file_uploader(
    "Research PDFs",
    type=["pdf"],
    accept_multiple_files=True,
    help=(
        f"Up to {MAX_RESEARCH_PDF_COUNT} PDFs. "
        "Each file must be no larger than 64 MB."
    ),
)

question = st.text_area(
    "Research question",
    placeholder="e.g. How can I toggle the last three bits of an integer?",
    height=100,
    max_chars=2000,
)

limit = st.slider("Maximum results", min_value=1, max_value=10, value=3)

run_search = st.button(
    "Search documents",
    type="primary",
    use_container_width=True,
)

if run_search:
    if not uploaded_files:
        st.error("Upload at least one PDF before searching.")
    elif len(uploaded_files) > MAX_RESEARCH_PDF_COUNT:
        st.error(f"Upload no more than {MAX_RESEARCH_PDF_COUNT} PDFs.")
    elif not question.strip():
        st.error("Enter a research question.")
    else:
        oversized = [
            item.name for item in uploaded_files
            if item.size > 64 * 1024 * 1024
        ]
        if oversized:
            st.error("These files exceed the 64 MB limit: " + ", ".join(oversized))
        else:
            try:
                with st.spinner("Extracting PDF text and ranking passages..."):
                    with TemporaryDirectory(prefix="scientia-demo-") as temp_dir:
                        pdf_paths = []
                        for index, item in enumerate(uploaded_files):
                            safe_name = Path(item.name).name
                            destination = Path(temp_dir) / str(index) / safe_name
                            destination.parent.mkdir(parents=True, exist_ok=True)
                            destination.write_bytes(item.getvalue())
                            pdf_paths.append(destination)

                        prepared = prepare_research(
                            ResearchQuestion(uuid4(), question.strip()),
                            pdf_paths,
                            limit=limit,
                        )

                        filenames = {
                            result.source.source_id: result.original_filename
                            for result in prepared.ingestion_results
                        }
                        hits = [
                            {
                                "rank": rank,
                                "source": filenames[hit.passage.source_id],
                                "page": (
                                    hit.passage.location.page_start
                                    if hit.passage.location is not None
                                    else None
                                ),
                                "score": hit.score,
                                "text": hit.passage.text,
                            }
                            for rank, hit in enumerate(
                                prepared.retrieval_hits, start=1
                            )
                        ]

                st.session_state["scientia_demo_result"] = {
                    "question": question.strip(),
                    "document_count": len(uploaded_files),
                    "hits": hits,
                }
            except PdfIngestionError as exc:
                st.error(f"PDF processing failed ({exc.stage}): {exc}")
                st.session_state.pop("scientia_demo_result", None)
            except Exception as exc:
                st.error(
                    "Search failed. No results were produced. "
                    f"Error type: {type(exc).__name__}"
                )
                st.session_state.pop("scientia_demo_result", None)

result = st.session_state.get("scientia_demo_result")

if result:
    st.markdown("---")
    st.subheader("Search results")
    st.caption(f"Question: {result['question']}")

    first, second, third = st.columns(3)
    first.metric("Documents searched", result["document_count"])
    second.metric("Passages retrieved", len(result["hits"]))
    third.metric(
        "Top relevance score",
        result["hits"][0]["score"] if result["hits"] else "—",
    )

    if not result["hits"]:
        st.info(
            "No matching passages were found for this query. "
            "Try different wording or another PDF."
        )
    else:
        for hit in result["hits"]:
            page = hit["page"] if hit["page"] is not None else "Unknown"
            safe_source = escape(hit["source"])
            safe_text = escape(hit["text"])
            st.markdown(
                f"""
                <div class="result-card">
                  <div class="result-meta">
                    RANK {hit['rank']} &nbsp;·&nbsp;
                    SCORE {hit['score']} &nbsp;·&nbsp;
                    PAGE {page}
                  </div>
                  <h4>{safe_source}</h4>
                  <div class="result-text">{safe_text}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            import json

            passage_json = json.dumps(hit["text"])
            components.html(
                f"""
                <div style="font-family: sans-serif; padding: 4px 0 12px;">
                  <button id="copy-passage"
                    style="background: linear-gradient(110deg, #0891b2, #2563eb);
                           color: white; border: 0; border-radius: 9px;
                           padding: 10px 16px; font-weight: 700;
                           cursor: pointer;">
                    Copy Passage
                  </button>
                  <span id="copy-status"
                    style="color: #67e8f9; margin-left: 10px;
                           font-size: 13px;"></span>
                </div>
                <script>
                  const passage = {passage_json};
                  const button = document.getElementById("copy-passage");
                  const status = document.getElementById("copy-status");
                  button.addEventListener("click", async () => {{
                    try {{
                      await navigator.clipboard.writeText(passage);
                      status.textContent = "Copied!";
                    }} catch (error) {{
                      status.textContent = "Copy unavailable in this browser.";
                    }}
                  }});
                </script>
                """,
                height=65,
            )

st.markdown("---")
st.caption(
    "SCIENTIA demo · Local PDF retrieval · "
    "Ranked passages are not a substitute for reviewing the original source."
)
