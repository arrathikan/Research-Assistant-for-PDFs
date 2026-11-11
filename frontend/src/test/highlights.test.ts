import { describe, expect, it } from 'vitest';
import { findTextRange, normalizedQuote, rangeRects, regionRects, type PageFrame } from '../components/pdf/highlights';
import { PDF_CITATION } from './pdfFixtures';
const frame: PageFrame = { width: 600, height: 800, rotation: 0, cropX: 0, cropY: 0, userUnit: 1 };
function layer(parts: string[]) {
  const root = document.createElement('div');
  for (const part of parts) { if (part === '\n') root.append(document.createElement('br')); else { const span = document.createElement('span'); span.textContent = part; root.append(span); } }
  return root;
}
describe('rendered source text', () => {
  it('matches split spans and line breaks without changing the text layer', () => {
    const root = layer(['Synthetic ', 'evi', 'dence.', '\n', 'Second line.']);
    const before = root.innerHTML;
    const match = findTextRange(root, 'evidence. Second line.');
    expect(match.reason).toBe('exact');
    expect(match.range?.startContainer.textContent).toBe('evi');
    expect(match.range?.endContainer.textContent).toBe('Second line.');
    expect(root.innerHTML).toBe(before);
  });
  it('normalizes ligatures and soft hyphens while retaining valid DOM offsets', () => {
    const root = layer(['The ﬁnal co\u00adoperation 😀 result.']);
    const match = findTextRange(root, 'final cooperation 😀');
    expect(match.range?.toString()).toBe('ﬁnal co\u00adoperation 😀');
    expect(normalizedQuote('  a\n b  ')).toBe('a b');
  });
  it('does not choose between repeated occurrences or use a partial case match', () => {
    expect(findTextRange(layer(['same phrase. same phrase.']), 'same phrase.').reason).toBe('ambiguous');
    expect(findTextRange(layer(['Evidence']), 'evidence').reason).toBe('missing');
    expect(findTextRange(layer(['Evidence']), '').range).toBeNull();
  });
  it('treats angle brackets as text and never injects source HTML', () => {
    const root = layer(['<script>alert(1)</script>']);
    expect(findTextRange(root, '<script>alert(1)</script>').reason).toBe('exact');
    expect(root.querySelector('script')).toBeNull();
  });
  it('keeps unique, in-page nonempty rectangles relative to the rendered page', () => {
    const rect = new DOMRect(30, 40, 50, 10);
    const range = { getClientRects: () => [rect, rect, new DOMRect(500, 500, 10, 10), new DOMRect(30, 40, 0, 0)] } as unknown as Range;
    expect(rangeRects(range, new DOMRect(10, 20, 100, 100))).toEqual([{ left: 20, top: 20, width: 50, height: 10 }]);
  });
});
describe('confirmed source regions', () => {
  it('converts PDF points to fractions that scale with the rendered page', () => {
    expect(regionRects(PDF_CITATION, frame)).toEqual([{ left: .1, top: .1, width: .3, height: .025 }]);
  });
  it('supports explicitly normalized regions', () => {
    expect(regionRects({ ...PDF_CITATION, bounding_boxes: [{ ...PDF_CITATION.bounding_boxes![0], coordinate_system: 'normalized', x: .1, y: .1, width: .3, height: .025 }] }, frame)).toEqual([{ left: .1, top: .1, width: .3, height: .025 }]);
  });
  it.each([{ rotation: 90 }, { cropX: 1 }, { cropY: 1 }, { userUnit: 2 }, { width: 900 }, { height: 900 }])('rejects incompatible PDF frames %j', change => {
    expect(regionRects(PDF_CITATION, { ...frame, ...change })).toEqual([]);
  });
  it.each([{ renderable: false }, { origin: 'unknown' as const }, { coordinate_system: 'provider' as const }, { rotation_degrees: 90 }, { rotation_degrees: null }, { x: -1 }, { x: 600 }, { width: 0 }, { y: Number.NaN }])('rejects unconfirmed or invalid geometry %j', change => {
    expect(regionRects({ ...PDF_CITATION, bounding_boxes: [{ ...PDF_CITATION.bounding_boxes![0], ...change }] }, frame)).toEqual([]);
  });
  it('uses a page fallback without dimensions or geometry', () => {
    expect(regionRects({ ...PDF_CITATION, page_width: null }, frame)).toEqual([]);
    expect(regionRects({ ...PDF_CITATION, bounding_boxes: [] }, frame)).toEqual([]);
  });
});
