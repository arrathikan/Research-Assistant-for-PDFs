"""Explicitly opted-in paid provider smoke test using a generated public test PDF."""

import os
from io import BytesIO

import pytest
from backend.services.document_processor.llamaparse_client import parse_with_llamaparse
from backend.shared.config import get_settings
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject


@pytest.mark.live_parser
def test_live_llamaparse_synthetic_pdf():
    if os.environ.get("RESEARCHAI_RUN_LLAMAPARSE_LIVE") != "1":
        pytest.skip("Set RESEARCHAI_RUN_LLAMAPARSE_LIVE=1 to opt into a paid provider call")
    settings = get_settings()
    if not settings.llama_cloud_api_key.strip() or settings.llama_cloud_api_key.startswith("your_"):
        pytest.skip("LLAMA_CLOUD_API_KEY is not configured")
    writer = PdfWriter()
    page = writer.add_blank_page(width=595, height=842)
    font = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/Type1"),
            NameObject("/BaseFont"): NameObject("/Helvetica"),
        }
    )
    page[NameObject("/Resources")] = DictionaryObject(
        {NameObject("/Font"): DictionaryObject({NameObject("/F1"): writer._add_object(font)})}
    )
    content = DecodedStreamObject()
    content.set_data(b"BT /F1 18 Tf 72 760 Td (ResearchAI synthetic parser test) Tj ET")
    page[NameObject("/Contents")] = writer._add_object(content)
    output = BytesIO()
    writer.write(output)
    result = parse_with_llamaparse("507f1f77bcf86cd799439011", output.getvalue(), 1, settings)
    assert len(result.pages) == 1 and result.pages[0].page_number == 1
    assert "ResearchAI" in result.pages[0].markdown
