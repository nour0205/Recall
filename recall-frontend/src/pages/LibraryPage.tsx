import { useMemo, useState } from 'react';
import { BookOpen, MessageSquareText, Plus, RefreshCw, Search, TriangleAlert } from 'lucide-react';
import type { LibraryDocument } from '@/types';
import { cn, documentTitle } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';

export default function LibraryPage({
  documents,
  loading,
  error,
  onRefresh,
  onAddNotes,
  onAskAbout,
}: {
  documents: LibraryDocument[];
  loading: boolean;
  error: string | null;
  onRefresh: () => void;
  onAddNotes: () => void;
  onAskAbout: (documentId: string) => void;
}) {
  const [query, setQuery] = useState('');

  const totalChunks = documents.reduce((sum, doc) => sum + doc.chunks, 0);
  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return documents;
    return documents.filter((doc) => `${doc.document_id} ${doc.preview ?? ''}`.toLowerCase().includes(q));
  }, [documents, query]);

  return (
    <div className="container max-w-6xl space-y-6 py-6 sm:py-8">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Library</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            {documents.length} note{documents.length === 1 ? '' : 's'} · {totalChunks} searchable chunk
            {totalChunks === 1 ? '' : 's'}. Recall answers only from these.
          </p>
        </div>
        <Button onClick={onAddNotes}>
          <Plus />
          Add notes
        </Button>
      </div>

      <div className="flex gap-2">
        <div className="relative flex-1">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Filter notes by title or content..."
            className="pl-9"
            aria-label="Filter notes"
          />
        </div>
        <Button variant="outline" size="icon" onClick={onRefresh} aria-label="Refresh library">
          <RefreshCw className={cn(loading && 'animate-spin')} />
        </Button>
      </div>

      {error ? (
        <p className="flex items-start gap-2 rounded-md bg-destructive/10 px-4 py-3 text-sm text-destructive">
          <TriangleAlert className="mt-0.5 h-4 w-4 shrink-0" />
          {error}
        </p>
      ) : null}

      {filtered.length ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {filtered.map((doc) => (
            <Card key={doc.document_id} className="flex flex-col">
              <CardHeader className="space-y-2 pb-3">
                <CardTitle className="text-base">{documentTitle(doc.document_id)}</CardTitle>
                <div className="flex flex-wrap gap-1.5">
                  <Badge variant="secondary" className="font-medium">
                    {doc.chunks} chunk{doc.chunks === 1 ? '' : 's'}
                  </Badge>
                  <Badge variant="outline" className="font-mono text-[10px] font-normal text-muted-foreground">
                    {doc.document_id}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent className="flex-1 pb-4">
                <p className="line-clamp-4 text-sm leading-6 text-muted-foreground">{doc.preview || 'No preview available.'}</p>
              </CardContent>
              <CardFooter>
                <Button variant="outline" size="sm" className="w-full" onClick={() => onAskAbout(doc.document_id)}>
                  <MessageSquareText />
                  Ask about this note
                </Button>
              </CardFooter>
            </Card>
          ))}
        </div>
      ) : !loading && !error ? (
        <Card>
          <CardContent className="flex flex-col items-center gap-3 p-10 text-center">
            <BookOpen className="h-8 w-8 text-muted-foreground" />
            {documents.length ? (
              <p className="text-sm text-muted-foreground">No notes match "{query}".</p>
            ) : (
              <>
                <p className="font-medium">No notes yet</p>
                <p className="text-sm text-muted-foreground">Add lecture notes to start asking questions about them.</p>
                <Button onClick={onAddNotes}>
                  <Plus />
                  Add notes
                </Button>
              </>
            )}
          </CardContent>
        </Card>
      ) : null}
    </div>
  );
}
