import type { ReactNode } from 'react';
import { parseInline } from '@/lib/citations';
import { cn } from '@/lib/utils';

// Renders the model's answer: paragraphs, simple lists and headings, with [S#] as buttons.
export default function GroundedAnswer({
  text,
  sourceCount,
  activeSource,
  onCite,
}: {
  text: string;
  sourceCount: number;
  activeSource: number | null;
  onCite: (sourceIndex: number) => void;
}) {
  const renderInline = (line: string) =>
    parseInline(line, sourceCount).map((segment, i) => {
      if (segment.kind === 'bold') return <strong key={i}>{segment.text}</strong>;
      if (segment.kind === 'text') return <span key={i}>{segment.text}</span>;
      return (
        <button
          key={i}
          type="button"
          onClick={() => onCite(segment.sourceIndex)}
          aria-label={`Show source ${segment.label}`}
          className={cn(
            'mx-0.5 inline-flex h-5 -translate-y-px items-center rounded px-1.5 align-middle font-mono text-[11px] font-semibold transition-colors',
            'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring',
            activeSource === segment.sourceIndex
              ? 'bg-cite text-white'
              : 'bg-cite/15 text-cite-foreground hover:bg-cite/30',
          )}
        >
          {segment.label}
        </button>
      );
    });

  const blocks: ReactNode[] = [];
  let list: string[] = [];

  const flushList = () => {
    if (!list.length) return;
    blocks.push(
      <ul key={`ul-${blocks.length}`} className="ml-5 list-disc space-y-1.5 marker:text-muted-foreground">
        {list.map((item, i) => (
          <li key={i}>{renderInline(item)}</li>
        ))}
      </ul>,
    );
    list = [];
  };

  for (const raw of text.replace(/\r/g, '').split('\n')) {
    const line = raw.trim();
    if (!line) {
      flushList();
      continue;
    }
    const heading = line.match(/^#{1,4}\s+(.*)$/);
    if (heading) {
      flushList();
      blocks.push(
        <h3 key={`h-${blocks.length}`} className="pt-2 font-semibold">
          {renderInline(heading[1])}
        </h3>,
      );
      continue;
    }
    const item = line.match(/^(?:[-*•]|\d+[.)])\s+(.*)$/);
    if (item) {
      list.push(item[1]);
      continue;
    }
    flushList();
    blocks.push(<p key={`p-${blocks.length}`}>{renderInline(line)}</p>);
  }
  flushList();

  return <div className="space-y-3 text-[15px] leading-7">{blocks}</div>;
}
