"""Tests for shared Pydantic schemas and domain models."""

from backend.shared.models import (
    DocumentStatus,
    DocumentMetadata,
    StructuredSummary,
    CitationReference,
    ChatQueryRequest,
    ChatQueryResponse,
)


def test_document_status_enum():
    """Verify all valid document lifecycle statuses."""
    assert DocumentStatus.PENDING == "PENDING"
    assert DocumentStatus.PARSING == "PARSING"
    assert DocumentStatus.EMBEDDING == "EMBEDDING"
    assert DocumentStatus.SUMMARIZING == "SUMMARIZING"
    assert DocumentStatus.READY == "READY"
    assert DocumentStatus.FAILED == "FAILED"


def test_document_metadata_model():
    """Verify DocumentMetadata instantiation and validation."""
    doc = DocumentMetadata(
        sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        filename="attention_is_all_you_need.pdf",
        file_size_bytes=1024000,
    )
    assert doc.status == DocumentStatus.PENDING
    assert doc.filename == "attention_is_all_you_need.pdf"
    assert doc.file_size_bytes == 1024000
    assert doc.page_count is None


def test_structured_summary_model():
    """Verify StructuredSummary 5-section schema."""
    summary = StructuredSummary(
        document_id="doc_123",
        title="Attention Is All You Need",
        authors=["Ashish Vaswani", "Noam Shazeer"],
        abstract="The dominant sequence transduction models...",
        problem_statement="Recurrent neural networks compute sequentially...",
        methodology="The Transformer architecture is based on self-attention...",
        key_results="Achieves 28.4 BLEU on English-to-German translation...",
        conclusion="Attention-based models train significantly faster...",
    )
    assert summary.document_id == "doc_123"
    assert len(summary.authors) == 2
    assert "Transformer" in summary.methodology


def test_citation_reference_model():
    """Verify CitationReference model validation."""
    citation = CitationReference(
        page_number=3,
        quote_snippet="Multi-Head Attention allows the model to jointly attend...",
        chunk_id="chunk_456",
    )
    assert citation.page_number == 3
    assert citation.chunk_id == "chunk_456"


def test_chat_query_models():
    """Verify ChatQueryRequest and ChatQueryResponse models."""
    req = ChatQueryRequest(message="What is the BLEU score achieved?")
    assert req.message == "What is the BLEU score achieved?"

    resp = ChatQueryResponse(
        answer="The model achieved a 28.4 BLEU score.",
        citations=[
            CitationReference(page_number=5, quote_snippet="28.4 BLEU score on WMT 2014")
        ],
        document_id="doc_123",
    )
    assert resp.answer.startswith("The model achieved")
    assert len(resp.citations) == 1
    assert resp.citations[0].page_number == 5
