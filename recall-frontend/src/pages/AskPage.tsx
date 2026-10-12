import { useMemo, useState, type FormEvent } from 'react';
import { ArrowUp, CircleHelp, Lightbulb, Loader2, Plus, SlidersHorizontal, TriangleAlert, X } from 'lucide-react';
import type { AskResponse, LibraryDocument } from '@/types';
import { ask } from '@/lib/api';
import { citedSourceIndexes } from '@/lib/citations';
import { cn, documentTitle } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Textarea } from '@/components/ui/textarea';
import GroundedAnswer from '@/components/GroundedAnswer';
import SourcePanel from '@/components/SourcePanel';

const REFUSAL = "I don't know.";

// Questions from the evaluation benchmark, answerable from the demo notes.
const EXAMPLE_QUESTIONS = [
  'What happens if the learning rate is too large during gradient descent?',
  'How do processes and threads differ in memory sharing and communication?',
  'How does partial dependency differ from transitive dependency, and which normal form removes each?',
];

type Answered = {
  question: string;
  scope: string[];
  response: AskResponse;
  elapsedMs: number;
};

export default function AskPage({
  documents,
  libraryLoaded,
  scope,
  onScopeChange,
  onAddNotes,
}: {
  documents: LibraryDocument[];
  // True once /documents has loaded, so an empty list really means an empty library.
  libraryLoaded: boolean;
  scope: string[];
  onScopeChange: (scope: string[]) => void;
  onAddNotes: () => void;
}) {
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [answered, setAnswered] = useState<Answered | null>(null);
  const [activeSource, setActiveSource] = useState<number | null>(null);
  const [flashKey, setFlashKey] = useState(0);

  async function submit(text = question) {
    const trimmed = text.trim();
    if (!trimmed || loading) return;

    setQuestion(trimmed);
    setLoading(true);
    setError(null);
    try {
      const startedAt = performance.now();
      const response = await ask({ question: trimmed, ...(scope.length && { document_ids: scope }) });
      setAnswered({ question: trimmed, scope, response, elapsedMs: performance.now() - startedAt });
      setActiveSource(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Request failed.');
    } finally {
      setLoading(false);
    }
  }

  function showSource(index: number) {
    setActiveSource(index);
    setFlashKey((key) => key + 1);
  }

  return (
    <div className="container max-w-6xl space-y-6 py-6 sm:py-8">
      {!answered && !loading ? (
        <div className="mx-auto max-w-2xl pt-6 text-center sm:pt-12">
          <h1 className="text-3xl font-bold tracking-tight sm:text-4xl">Ask your notes.</h1>
          <p className="mt-3 text-muted-foreground">
            Every answer comes from your own notes and cites them, or Recall says it doesn't know.
          </p>
        </div>
      ) : null}

      <Composer
        question={question}
        onQuestionChange={setQuestion}
        onSubmit={() => void submit()}
        loading={loading}
        documents={documents}
        scope={scope}
        onScopeChange={onScopeChange}
        compact={Boolean(answered) || loading}
      />

      {error ? (
        <p className="mx-auto flex max-w-3xl items-start gap-2 rounded-md bg-destructive/10 px-4 py-3 text-sm text-destructive">
          <TriangleAlert className="mt-0.5 h-4 w-4 shrink-0" />
          {error}
        </p>
      ) : null}

      {loading ? <LoadingState /> : null}

      {/* The examples target the demo notes, so they only make sense when searching everything. */}
      {!answered && !loading && documents.length > 0 && !scope.length ? (
        <div className="mx-auto max-w-3xl">
          <p className="mb-2 text-xs font-medium uppercase tracking-wide text-muted-foreground">Try asking</p>
          <div className="grid gap-2">
            {EXAMPLE_QUESTIONS.map((example) => (
              <button
                key={example}
                type="button"
                onClick={() => void submit(example)}
                className="rounded-lg border bg-card px-4 py-3 text-left text-sm transition-colors hover:bg-accent"
              >
                {example}
              </button>
            ))}
          </div>
        </div>
      ) : null}

      {!answered && !loading && libraryLoaded && !documents.length ? (
        <Card className="mx-auto max-w-3xl">
          <CardContent className="flex flex-col items-center gap-3 p-8 text-center">
            <p className="font-medium">Your library is empty.</p>
            <p className="text-sm text-muted-foreground">Add some notes first; Recall can only answer from them.</p>
            <Button onClick={onAddNotes}>
              <Plus />
              Add notes
            </Button>
          </CardContent>
        </Card>
      ) : null}

      {answered && !loading ? (
        <Result
          answered={answered}
          activeSource={activeSource}
          flashKey={flashKey}
          onShowSource={showSource}
          onSelectSource={(i) => setActiveSource((current) => (current === i ? null : i))}
          onAddNotes={onAddNotes}
          onClearScope={() => onScopeChange([])}
        />
      ) : null}
    </div>
  );
}

function Composer({
  question,
  onQuestionChange,
  onSubmit,
  loading,
  documents,
  scope,
  onScopeChange,
  compact,
}: {
  question: string;
  onQuestionChange: (value: string) => void;
  onSubmit: () => void;
  loading: boolean;
  documents: LibraryDocument[];
  scope: string[];
  onScopeChange: (scope: string[]) => void;
  compact: boolean;
}) {
  const [choosing, setChoosing] = useState(false);

  function toggle(documentId: string) {
    onScopeChange(scope.includes(documentId) ? scope.filter((id) => id !== documentId) : [...scope, documentId]);
  }

  return (
    <form
      onSubmit={(event: FormEvent) => {
        event.preventDefault();
        onSubmit();
      }}
      className="mx-auto max-w-3xl rounded-xl border bg-card shadow-sm focus-within:ring-2 focus-within:ring-ring/30"
    >
      <Textarea
        value={question}
        onChange={(e) => onQuestionChange(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing) {
            e.preventDefault();
            onSubmit();
          }
        }}
        rows={compact ? 2 : 3}
        placeholder="Ask a question about your notes..."
        aria-label="Question"
        className="resize-none border-0 bg-transparent px-4 pt-4 text-base shadow-none focus-visible:ring-0 focus-visible:ring-offset-0"
      />

      <div className="flex flex-wrap items-center gap-2 px-3 pb-3">
        <Button
          type="button"
          variant="ghost"
          size="sm"
          onClick={() => setChoosing((value) => !value)}
          aria-expanded={choosing}
          className="text-muted-foreground"
        >
          <SlidersHorizontal />
          {scope.length ? `${scope.length} note${scope.length === 1 ? '' : 's'}` : `All notes${documents.length ? ` (${documents.length})` : ''}`}
        </Button>

        {scope.map((documentId) => (
          <Badge key={documentId} variant="secondary" className="gap-1 font-medium">
            {documentTitle(documentId)}
            <button type="button" onClick={() => toggle(documentId)} aria-label={`Remove ${documentId} from scope`}>
              <X className="h-3 w-3" />
            </button>
          </Badge>
        ))}

        <Button type="submit" size="icon" className="ml-auto h-9 w-9 rounded-full" disabled={loading || !question.trim()} aria-label="Send question">
          {loading ? <Loader2 className="animate-spin" /> : <ArrowUp />}
        </Button>
      </div>

      {choosing ? (
        <div className="border-t px-4 py-3">
          <div className="mb-2 flex items-center justify-between">
            <p className="text-xs text-muted-foreground">Search only the selected notes, or leave all unselected to search everything.</p>
            {scope.length ? (
              <Button type="button" variant="link" size="sm" className="h-auto p-0 text-xs" onClick={() => onScopeChange([])}>
                Clear
              </Button>
            ) : null}
          </div>
          <div className="flex max-h-40 flex-wrap gap-1.5 overflow-y-auto">
            {documents.map((doc) => {
              const selected = scope.includes(doc.document_id);
              return (
                <button
                  key={doc.document_id}
                  type="button"
                  onClick={() => toggle(doc.document_id)}
                  aria-pressed={selected}
                  className={cn(
                    'rounded-full border px-3 py-1 text-xs transition-colors',
                    selected ? 'border-primary bg-primary text-primary-foreground' : 'hover:bg-accent',
                  )}
                >
                  {documentTitle(doc.document_id)}
                </button>
              );
            })}
          </div>
        </div>
      ) : null}
    </form>
  );
}

function Result({
  answered,
  activeSource,
  flashKey,
  onShowSource,
  onSelectSource,
  onAddNotes,
  onClearScope,
}: {
  answered: Answered;
  activeSource: number | null;
  flashKey: number;
  onShowSource: (index: number) => void;
  onSelectSource: (index: number) => void;
  onAddNotes: () => void;
  onClearScope: () => void;
}) {
  const { question, response, elapsedMs, scope } = answered;
  const sources = response.sources ?? [];
  const cited = useMemo(() => citedSourceIndexes(response.answer, sources.length), [response.answer, sources.length]);

  if (response.answer.trim() === REFUSAL) {
    return (
      <Card className="mx-auto max-w-3xl">
        <CardContent className="space-y-4 p-6">
          <p className="text-sm text-muted-foreground">{question}</p>
          <div className="flex items-start gap-3">
            <CircleHelp className="mt-0.5 h-5 w-5 shrink-0 text-muted-foreground" />
            <div>
              <p className="text-lg font-semibold">I don't know.</p>
              <p className="mt-1 text-sm text-muted-foreground">
                {scope.length ? 'The selected notes' : 'Your notes'} don't contain enough to answer this. Recall
                only answers from your notes, so it doesn't guess.
              </p>
            </div>
          </div>
          <div className="flex flex-wrap gap-2">
            {scope.length ? (
              <Button variant="outline" size="sm" onClick={onClearScope}>
                Search all notes
              </Button>
            ) : null}
            <Button variant="outline" size="sm" onClick={onAddNotes}>
              <Plus />
              Add notes on this topic
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="grid items-start gap-6 lg:grid-cols-[minmax(0,1fr)_380px]">
      <div className="space-y-4">
        <Card>
          <CardContent className="space-y-4 p-6">
            <p className="text-sm font-medium text-muted-foreground">{question}</p>
            <GroundedAnswer text={response.answer} sourceCount={sources.length} activeSource={activeSource} onCite={onShowSource} />
            <div className="flex flex-wrap items-center gap-x-3 gap-y-1 border-t pt-3 text-xs text-muted-foreground">
              <span>
                Cites {cited.size} of {sources.length} retrieved passage{sources.length === 1 ? '' : 's'}
              </span>
              <span>{(elapsedMs / 1000).toFixed(1)}s</span>
            </div>
          </CardContent>
        </Card>

        {response.study_hint ? (
          <div className="flex items-start gap-3 rounded-lg border border-dashed px-4 py-3 text-sm">
            <Lightbulb className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" />
            <p>
              <span className="font-medium">Study tip: </span>
              <span className="text-muted-foreground">{response.study_hint}</span>
            </p>
          </div>
        ) : null}
      </div>

      <aside className="lg:sticky lg:top-20 lg:flex lg:max-h-[calc(100vh-6rem)] lg:flex-col">
        <SourcePanel sources={sources} cited={cited} active={activeSource} flashKey={flashKey} onSelect={onSelectSource} />
      </aside>
    </div>
  );
}

function LoadingState() {
  return (
    <div className="mx-auto max-w-3xl space-y-3" aria-live="polite">
      <p className="flex items-center gap-2 text-sm text-muted-foreground">
        <Loader2 className="h-4 w-4 animate-spin" />
        Searching your notes and writing a grounded answer...
      </p>
      <div className="space-y-2 rounded-lg border p-6">
        {[100, 92, 70].map((width) => (
          <div key={width} className="h-3 animate-pulse rounded bg-muted" style={{ width: `${width}%` }} />
        ))}
      </div>
    </div>
  );
}
