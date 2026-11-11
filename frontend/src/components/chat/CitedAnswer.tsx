import type { ChatCitation } from '../../types/chat';

interface Props { answer: string; citations: ChatCitation[]; onCitationClick?: (citation: ChatCitation) => void; }

/** Render model text safely; only known numeric source references become buttons. */
export function CitedAnswer({ answer, citations, onCitationClick }: Props) {
  return <p>{answer.split(/(\[\d+\])/g).map((text, index) => {
    const match = /^\[(\d+)\]$/.exec(text);
    const source = match ? citations[Number(match[1]) - 1] : undefined;
    return source && onCitationClick
      ? <button key={index} type="button" className="rounded px-1 font-semibold text-blue-700 underline" aria-label={`Open citation ${match![1]}, page ${source.page_number}`} onClick={() => onCitationClick(source)}>{text}</button>
      : text;
  })}</p>;
}
