"""LangChain Markdown chunking with tracked page boundaries and source evidence."""

import json
import re
from bisect import bisect_left
from dataclasses import dataclass, field
from hashlib import sha256
from importlib.metadata import version

from backend.services.document_processor.chunk_models import (
    ChunkingConfig,
    ChunkingError,
    ChunkPageSpan,
    DocumentChunk,
)
from backend.services.document_processor.parsed_models import (
    ParsedDocument,
    ParsedPage,
    SourceElement,
)
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter

ALGORITHM_VERSION = "markdown-pages-v1"
HEADERS = [("#" * level, f"h{level}") for level in range(1, 7)]


@dataclass
class _Fragment:
    page: int
    text: str
    start: int = 0


@dataclass
class _Section:
    headings: dict[str, str]
    fragments: list[_Fragment] = field(default_factory=list)


def _digest(value: object) -> str:
    return sha256(
        json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()
    ).hexdigest()


def chunk_set_id(parsed: ParsedDocument, parse_run_id: str, config: ChunkingConfig) -> str:
    return _digest(
        {
            "document": parsed.model_dump(mode="json"),
            "parse_run_id": parse_run_id,
            "config": config.model_dump(),
            "algorithm": ALGORITHM_VERSION,
            "splitter": version("langchain-text-splitters"),
        }
    )


def _sections(parsed: ParsedDocument) -> list[_Section]:
    expected = list(range(1, len(parsed.pages) + 1))
    if [page.page_number for page in parsed.pages] != expected or any(
        page.document_id != parsed.document_id for page in parsed.pages
    ):
        raise ChunkingError("Parsed pages must belong to one document in original page order")
    marker = "RESEARCHAI_PAGE_" + _digest(parsed.model_dump(mode="json"))
    while any(marker in page.markdown for page in parsed.pages):
        marker += "X"
    pattern = re.compile(r"(?m)^" + re.escape(marker) + r":(\d+)\s*$")
    text = "\n\n".join(f"{marker}:{page.page_number}\n\n{page.markdown}" for page in parsed.pages)
    splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=HEADERS, strip_headers=False, return_each_line=True
    )
    current_page = 0
    seen = []
    sections: list[_Section] = []
    for block in splitter.split_text(text):
        starts_heading = bool(re.match(r"^#{1,6}(?:\s|$)", block.page_content))
        if not sections or sections[-1].headings != block.metadata or starts_heading:
            sections.append(_Section(dict(block.metadata)))
        offset = 0
        for match in pattern.finditer(block.page_content):
            content = block.page_content[offset : match.start()].strip()
            if content:
                if not current_page:
                    raise ChunkingError("Page attribution was lost during Markdown splitting")
                sections[-1].fragments.append(_Fragment(current_page, content))
            current_page = int(match.group(1))
            seen.append(current_page)
            offset = match.end()
        content = block.page_content[offset:].strip()
        if content:
            if not current_page:
                raise ChunkingError("Page attribution was lost during Markdown splitting")
            sections[-1].fragments.append(_Fragment(current_page, content))
    if seen != expected:
        raise ChunkingError("Markdown splitting did not retain all page boundaries")
    return [section for section in sections if section.fragments]


def _normalized(text: str) -> tuple[str, list[int]]:
    """Whitespace-normalized text plus a monotonic map to its input characters."""
    characters, positions = [], []
    pending_space = None
    for index, character in enumerate(text):
        if character.isspace():
            if characters and pending_space is None:
                pending_space = index
            continue
        if pending_space is not None:
            characters.append(" ")
            positions.append(pending_space)
            pending_space = None
        characters.append(character)
        positions.append(index)
    return "".join(characters), positions


def _unique_position(text: str, needle: str) -> int | None:
    position = text.find(needle) if needle else -1
    return position if position >= 0 and text.find(needle, position + 1) == -1 else None


def _sources(page: ParsedPage, fragment: str, start: int, end: int) -> list[SourceElement]:
    page_text, _ = _normalized(page.markdown)
    fragment_text, mapping = _normalized(fragment)
    fragment_position = _unique_position(page_text, fragment_text)
    if fragment_position is None:
        return []
    lower = fragment_position + bisect_left(mapping, start)
    upper = fragment_position + bisect_left(mapping, end)
    matched = []
    for element in page.elements:
        if element.document_id != page.document_id or element.page_number != page.page_number:
            raise ChunkingError("Source element attribution does not match its page")
        for source_text in (element.markdown, element.text):
            needle, _ = _normalized(source_text)
            position = _unique_position(page_text, needle)
            if position is not None and max(lower, position) < min(upper, position + len(needle)):
                matched.append(element.model_copy(deep=True))
                break
    return matched


def chunk_document(
    parsed: ParsedDocument, parse_run_id: str, config: ChunkingConfig | None = None
) -> list[DocumentChunk]:
    """Split within research sections; allow continuation across PDF pages.

    LangChain normalizes Markdown whitespace. Evidence offsets refer to the
    resulting chunk, not guessed PDF coordinates or original Markdown offsets.
    Ambiguous source text retains page attribution without invented element links.
    """
    config = config or ChunkingConfig()
    identifier = chunk_set_id(parsed, parse_run_id, config)
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=config.chunk_size,
        chunk_overlap=config.chunk_overlap,
        add_start_index=True,
        separators=["\n\n", "\n", " ", ""],
    )
    chunks: list[DocumentChunk] = []
    pages = {page.page_number: page for page in parsed.pages}
    for section_index, section in enumerate(_sections(parsed)):
        content = ""
        for fragment in section.fragments:
            if content:
                content += "\n\n"
            fragment.start = len(content)
            content += fragment.text
        for piece in splitter.create_documents([content]):
            start = piece.metadata["start_index"]
            end = start + len(piece.page_content)
            if start < 0 or content[start:end] != piece.page_content:
                raise ChunkingError("Recursive splitting lost its source offsets")
            spans = []
            for fragment in section.fragments:
                low, high = (
                    max(start, fragment.start),
                    min(end, fragment.start + len(fragment.text)),
                )
                if low >= high or not content[low:high].strip():
                    continue
                page = pages[fragment.page]
                spans.append(
                    ChunkPageSpan(
                        page_number=page.page_number,
                        chunk_start=low - start,
                        chunk_end=high - start,
                        text=content[low:high],
                        page_width=page.width,
                        page_height=page.height,
                        source_elements=_sources(
                            page, fragment.text, low - fragment.start, high - fragment.start
                        ),
                    )
                )
            if not spans:
                raise ChunkingError("Chunk has no attributable source page")
            numbers = sorted({span.page_number for span in spans})
            headings = section.headings
            chunk_id = _digest(
                {
                    "set": identifier,
                    "section": section_index,
                    "start": start,
                    "end": end,
                    "content": piece.page_content,
                }
            )
            chunks.append(
                DocumentChunk(
                    id=chunk_id,
                    document_id=parsed.document_id,
                    chunk_index=len(chunks),
                    page_number=numbers[0],
                    page_end=numbers[-1],
                    page_numbers=numbers,
                    section_title=list(headings.values())[-1] if headings else None,
                    heading_path=headings,
                    content=piece.page_content,
                    page_spans=spans,
                    parse_run_id=parse_run_id,
                    chunk_set_id=identifier,
                    chunk_size=config.chunk_size,
                    chunk_overlap=config.chunk_overlap,
                    splitter_version=version("langchain-text-splitters"),
                    algorithm_version=ALGORITHM_VERSION,
                )
            )
    if not chunks:
        raise ChunkingError("Parsed document contains no nonempty Markdown")
    return chunks
