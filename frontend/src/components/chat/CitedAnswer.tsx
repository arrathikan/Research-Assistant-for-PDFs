import type { ReactNode } from 'react';
import type { ChatCitation } from '../../types/chat';

interface Props { answer: string; citations: ChatCitation[]; onCitationClick?: (citation: ChatCitation) => void; }

/** Small safe Markdown renderer: no HTML, scripts, images or model-supplied links. */
export function CitedAnswer({ answer, citations, onCitationClick }: Props) {
  function inline(text: string, prefix: string): ReactNode[] {
    return text.split(/(\[\d+\]|\*\*[^*]+\*\*|`[^`]+`|\*[^*\n]+\*)/g).map((part, index) => {
      const key = prefix + '-' + index;
      const match = /^\[(\d+)\]$/.exec(part);
      const source = match ? citations[Number(match[1]) - 1] : undefined;
      if (source && onCitationClick) return <button key={key} type="button"
        className="mx-0.5 inline-flex min-h-6 min-w-6 items-center justify-center rounded-md ui-citation px-1.5 font-medium focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-600"
        aria-label={'Open citation ' + match![1] + ', page ' + source.page_number}
        onClick={event => { event.currentTarget.focus(); onCitationClick(source); }}>[Page {source.page_number}]</button>;
      if (source) return <span key={key} className="font-medium text-brand-700">[Page {source.page_number}]</span>;
      if (part.startsWith('**') && part.endsWith('**')) return <strong key={key} className="font-semibold text-stone-900">{inline(part.slice(2, -2), key)}</strong>;
      if (part.startsWith('`') && part.endsWith('`')) return <code key={key} className="rounded bg-stone-100 px-1 py-0.5 text-xs">{part.slice(1, -1)}</code>;
      if (part.startsWith('*') && part.endsWith('*')) return <em key={key}>{inline(part.slice(1, -1), key)}</em>;
      return part;
    });
  }
  const lines = answer.split(/\r?\n/);
  const blocks: ReactNode[] = [];
  const cells = (line: string) => line.trim().replace(/^\||\|$/g, '').split('|').map(cell => cell.trim());
  let index = 0;
  while (index < lines.length) {
    const line = lines[index];
    if (!line.trim()) { index++; continue; }
    const key = 'block-' + index;
    if (line.startsWith('```')) {
      const code: string[] = [];
      index++;
      while (index < lines.length && !lines[index].startsWith('```')) code.push(lines[index++]);
      index++;
      blocks.push(<pre key={key} className="overflow-x-auto rounded-lg bg-stone-100 p-3 text-xs"><code>{code.join('\n')}</code></pre>);
      continue;
    }
    const heading = /^(#{1,3})\s+(.+)$/.exec(line);
    if (heading) {
      blocks.push(<h3 key={key} className="pt-1 text-sm font-semibold text-stone-900">{inline(heading[2], key)}</h3>);
      index++; continue;
    }
    if (line.includes('|') && /^\s*\|?[\s:|\-]+\|?\s*$/.test(lines[index + 1] || '') && (lines[index + 1] || '').includes('---')) {
      const headings = cells(line); const rows: string[][] = [];
      index += 2;
      while (index < lines.length && lines[index].includes('|')) rows.push(cells(lines[index++]));
      blocks.push(<div key={key} className="overflow-x-auto rounded-lg border border-stone-200">
        <table className="w-full border-collapse text-left text-xs"><thead className="bg-stone-50"><tr>{headings.map((cell, n) => <th key={n} scope="col" className="border-b border-stone-200 px-3 py-2 font-semibold">{inline(cell, key + '-h' + n)}</th>)}</tr></thead>
          <tbody>{rows.map((row, n) => <tr key={n}>{headings.map((_, c) => <td key={c} className="border-t border-stone-100 px-3 py-2 align-top">{inline(row[c] || '', key + '-' + n + '-' + c)}</td>)}</tr>)}</tbody></table>
      </div>);
      continue;
    }
    const list = /^\s*(?:[-*]|\d+[.)])\s+/.exec(line);
    if (list) {
      const ordered = /^\s*\d/.test(line);
      const items: string[] = [];
      const pattern = ordered ? /^\s*\d+[.)]\s+(.+)$/ : /^\s*[-*]\s+(.+)$/;
      while (index < lines.length) {
        const item = pattern.exec(lines[index]);
        if (!item) break;
        items.push(item[1]); index++;
      }
      const List = ordered ? 'ol' : 'ul';
      blocks.push(<List key={key} className={'ml-5 space-y-1 ' + (ordered ? 'list-decimal' : 'list-disc')}>{items.map((item, n) => <li key={n}>{inline(item, key + n)}</li>)}</List>);
      continue;
    }
    const paragraph = [line]; index++;
    while (index < lines.length && lines[index].trim() && !/^(#{1,3}\s|```|\s*(?:[-*]|\d+[.)])\s)/.test(lines[index])) {
      if (lines[index].includes('|') && (lines[index + 1] || '').includes('---')) break;
      paragraph.push(lines[index++]);
    }
    blocks.push(<p key={key} className="whitespace-pre-line">{inline(paragraph.join('\n'), key)}</p>);
  }
  return <div className="space-y-3 text-sm leading-7 text-stone-700">{blocks}</div>;
}
