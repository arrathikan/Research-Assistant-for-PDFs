import type { ChatCitation } from '../../types/chat';

export interface Rect { left: number; top: number; width: number; height: number; }
export interface PageFrame { width: number; height: number; rotation: number; cropX: number; cropY: number; userUnit: number; }
interface Point { node: Text; start: number; end: number; }

export function normalizedQuote(value: string): string {
  return value.normalize('NFKC').replace(/\u00ad/g, '').replace(/\s+/g, ' ').trim();
}

/** Match the rendered PDF text across spans/line breaks without injecting HTML. */
export function findTextRange(root: HTMLElement, quote: string): { range: Range | null; reason: 'exact' | 'missing' | 'ambiguous' } {
  let text = '';
  const points: (Point | null)[] = [];
  function append(value: string, point: Point | null) {
    for (const char of value.normalize('NFKC')) {
      if (char === '\u00ad') continue;
      const next = /\s/.test(char) ? ' ' : char;
      if (next === ' ' && (!text || text.endsWith(' '))) continue;
      text += next;
      // Index by UTF-16 offsets, matching String.indexOf and DOM Range offsets.
      for (let index = 0; index < next.length; index++) points.push(point);
    }
  }
  const walker = root.ownerDocument.createTreeWalker(root, NodeFilter.SHOW_ELEMENT | NodeFilter.SHOW_TEXT);
  let current = walker.nextNode();
  while (current) {
    if (current.nodeType === Node.TEXT_NODE) {
      const node = current as Text;
      let offset = 0;
      for (const char of node.data) {
        append(char, { node, start: offset, end: offset + char.length });
        offset += char.length;
      }
    } else if ((current as Element).tagName === 'BR') append(' ', null);
    current = walker.nextNode();
  }
  const needle = normalizedQuote(quote);
  const start = needle ? text.indexOf(needle) : -1;
  if (start < 0) return { range: null, reason: 'missing' };
  if (text.indexOf(needle, start + 1) >= 0) return { range: null, reason: 'ambiguous' };
  const first = points[start];
  const last = points[start + needle.length - 1];
  if (!first || !last) return { range: null, reason: 'missing' };
  const range = root.ownerDocument.createRange();
  range.setStart(first.node, first.start);
  range.setEnd(last.node, last.end);
  return { range, reason: 'exact' };
}

export function rangeRects(range: Range, page: DOMRect): Rect[] {
  const result: Rect[] = [];
  for (const rect of Array.from(range.getClientRects())) {
    const next = { left: rect.left - page.left, top: rect.top - page.top, width: rect.width, height: rect.height };
    if (next.width <= 0 || next.height <= 0 || next.left < -1 || next.top < -1 || next.left + next.width > page.width + 1 || next.top + next.height > page.height + 1) continue;
    if (!result.some(item => Math.abs(item.left - next.left) < .5 && Math.abs(item.top - next.top) < .5 && Math.abs(item.width - next.width) < .5 && Math.abs(item.height - next.height) < .5)) result.push(next);
  }
  return result;
}

/** Return page-relative fractions only for a confirmed, compatible source frame. */
export function regionRects(source: ChatCitation, frame: PageFrame): Rect[] {
  if (!source.page_width || !source.page_height || frame.rotation % 360 !== 0 || frame.cropX !== 0 || frame.cropY !== 0 || frame.userUnit !== 1 || Math.abs(source.page_width - frame.width) > 1 || Math.abs(source.page_height - frame.height) > 1) return [];
  return (source.bounding_boxes ?? []).flatMap(box => {
    if (!box.renderable || box.origin !== 'top_left' || box.rotation_degrees !== 0 || box.coordinate_system === 'provider') return [];
    const x = box.coordinate_system === 'points' ? box.x / source.page_width! : box.x;
    const y = box.coordinate_system === 'points' ? box.y / source.page_height! : box.y;
    const width = box.coordinate_system === 'points' ? box.width / source.page_width! : box.width;
    const height = box.coordinate_system === 'points' ? box.height / source.page_height! : box.height;
    if (![x, y, width, height].every(Number.isFinite) || x < 0 || y < 0 || width <= 0 || height <= 0 || x + width > 1.000001 || y + height > 1.000001) return [];
    return [{ left: x, top: y, width, height }];
  });
}
