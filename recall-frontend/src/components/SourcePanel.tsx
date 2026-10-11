import { useEffect, useRef } from 'react';
import { ChevronDown, FileText } from 'lucide-react';
import type { Source } from '@/types';
import { Badge } from '@/components/ui/badge';
import { cn, documentTitle } from '@/lib/utils';

export default function SourcePanel({
  sources,
  cited,
  active,
  flashKey,
  onSelect,
}: {
  sources: Source[];
  cited: Set<number>;
  active: number | null;
  // Changes on every citation click so the highlight replays on repeated clicks.
  flashKey: number;
  onSelect: (index: number) => void;
}) {
  const itemRefs = useRef<Array<HTMLLIElement | null>>([]);

  useEffect(() => {
    if (active === null) return;
    itemRefs.current[active]?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }, [active, flashKey]);

  return (
    <section aria-label="Sources" className="flex min-h-0 flex-col">
      <div className="flex items-baseline justify-between pb-3">
        <h2 className="text-sm font-semibold">Sources</h2>
        <span className="text-xs text-muted-foreground">
          {cited.size} of {sources.length} cited
        </span>
      </div>

      <ol className="min-h-0 space-y-2 overflow-y-auto pr-1">
        {sources.map((source, index) => (
          <li key={`${source.document_id}-${source.chunk_index}-${index}`} ref={(el) => (itemRefs.current[index] = el)}>
            <SourceItem
              source={source}
              index={index}
              cited={cited.has(index)}
              active={active === index}
              flashKey={flashKey}
              onSelect={() => onSelect(index)}
            />
          </li>
        ))}
      </ol>
    </section>
  );
}

function SourceItem({
  source,
  index,
  cited,
  active,
  flashKey,
  onSelect,
}: {
  source: Source;
  index: number;
  cited: boolean;
  active: boolean;
  flashKey: number;
  onSelect: () => void;
}) {
  return (
    <article
      key={active ? flashKey : undefined}
      className={cn(
        'rounded-lg border bg-card transition-colors',
        active ? 'animate-flash border-cite bg-cite/[0.08] ring-1 ring-cite' : !cited && 'opacity-70',
      )}
    >
      <button
        type="button"
        onClick={onSelect}
        aria-expanded={active}
        className="flex w-full items-start gap-3 p-3 text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring rounded-lg"
      >
        <span
          className={cn(
            'mt-0.5 rounded px-1.5 font-mono text-[11px] font-semibold',
            cited ? 'bg-cite/15 text-cite-foreground' : 'bg-muted text-muted-foreground',
          )}
        >
          S{index + 1}
        </span>
        <span className="min-w-0 flex-1">
          <span className="flex items-center gap-1.5 text-sm font-medium">
            <FileText className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
            <span className="truncate">{documentTitle(source.document_id)}</span>
          </span>
          <span className="mt-1 flex flex-wrap items-center gap-1.5">
            {source.chunk_index != null ? (
              <span className="text-xs text-muted-foreground">Chunk {source.chunk_index + 1}</span>
            ) : null}
            {!cited ? (
              <Badge variant="outline" className="px-1.5 py-0 text-[10px] font-medium text-muted-foreground">
                Retrieved, not cited
              </Badge>
            ) : null}
          </span>
        </span>
        <ChevronDown className={cn('mt-0.5 h-4 w-4 shrink-0 text-muted-foreground transition-transform', active && 'rotate-180')} />
      </button>

      <p
        className={cn(
          'whitespace-pre-line px-3 pb-3 text-sm leading-6 text-muted-foreground',
          active ? 'text-foreground/90' : 'line-clamp-2',
        )}
      >
        {source.text}
      </p>
    </article>
  );
}
