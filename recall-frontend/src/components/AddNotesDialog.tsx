import { useMemo, useState, type FormEvent } from 'react';
import { CheckCircle2, ClipboardPaste, FileUp, Loader2, TriangleAlert } from 'lucide-react';
import type { IngestResponse } from '@/types';
import { ingest } from '@/lib/api';
import { slugFromFilename } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Textarea } from '@/components/ui/textarea';

// Ingestion is text-only for now; PDF support is roadmap step 5.
const ACCEPTED_FILES = '.txt,.md,.markdown';

const STATUS_MESSAGES: Record<string, string> = {
  duplicate: 'This exact text is already in your library.',
  conflict: 'A note with this title already exists. Choose another title.',
  'no content': 'Recall could not create any chunks from this text.',
};

const EMPTY_FORM = { title: '', course: '', topics: '', text: '', filename: '' };

export default function AddNotesDialog({
  open,
  onOpenChange,
  onIngested,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onIngested: (documentId: string) => void;
}) {
  const [form, setForm] = useState(EMPTY_FORM);
  const [mode, setMode] = useState<'paste' | 'upload'>('paste');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [added, setAdded] = useState<{ documentId: string; chunks: number } | null>(null);

  const wordCount = useMemo(() => form.text.trim().split(/\s+/).filter(Boolean).length, [form.text]);

  function update(patch: Partial<typeof EMPTY_FORM>) {
    setForm((prev) => ({ ...prev, ...patch }));
    setError(null);
  }

  function reset() {
    setForm(EMPTY_FORM);
    setError(null);
    setAdded(null);
  }

  async function handleFile(file: File | undefined) {
    if (!file) return;
    if (!/\.(txt|md|markdown)$/i.test(file.name)) {
      setError('Only .txt and .md files are supported for now.');
      return;
    }
    const text = await file.text();
    update({ text, filename: file.name, title: form.title || slugFromFilename(file.name) });
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    const documentId = form.title.trim();
    if (!documentId) return setError('Give the note a short title, for example db_normalization_intro.');
    if (!form.text.trim()) return setError(mode === 'upload' ? 'Choose a file first.' : 'Paste the note content first.');

    setSubmitting(true);
    setError(null);
    try {
      const topics = form.topics.split(',').map((tag) => tag.trim()).filter(Boolean);
      const result: IngestResponse = await ingest({
        document_id: documentId,
        document_type: 'lecture_note',
        text: form.text.trim(),
        ...(form.course.trim() && { course: form.course.trim() }),
        ...(topics.length && { topic_tags: topics }),
        ...(mode === 'upload' && form.filename && { source: form.filename }),
      });

      if (result.status === 'ingested') {
        setAdded({ documentId, chunks: result.chunks_added ?? 0 });
        onIngested(documentId);
      } else {
        setError(STATUS_MESSAGES[result.status] ?? `The API returned status "${result.status}".`);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not add the note.');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Dialog
      open={open}
      onOpenChange={(next) => {
        onOpenChange(next);
        if (!next && added) reset();
      }}
    >
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Add notes</DialogTitle>
          <DialogDescription>
            Recall answers only from notes in your library. Paste text or upload a .txt or .md file.
          </DialogDescription>
        </DialogHeader>

        {added ? (
          <div className="space-y-4">
            <div className="flex items-start gap-3 rounded-lg border border-emerald-200 bg-emerald-50 p-4 text-emerald-900">
              <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0" />
              <div>
                <p className="font-medium">Added "{added.documentId}"</p>
                <p className="text-sm">
                  Split into {added.chunks} searchable chunk{added.chunks === 1 ? '' : 's'}.
                </p>
              </div>
            </div>
            <DialogFooter className="gap-2">
              <Button variant="outline" onClick={reset}>
                Add another
              </Button>
              <Button onClick={() => onOpenChange(false)}>Done</Button>
            </DialogFooter>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="note-title">Title</Label>
                <Input
                  id="note-title"
                  value={form.title}
                  onChange={(e) => update({ title: e.target.value })}
                  placeholder="db_normalization_intro"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="note-course">
                  Course <span className="font-normal text-muted-foreground">(optional)</span>
                </Label>
                <Input
                  id="note-course"
                  value={form.course}
                  onChange={(e) => update({ course: e.target.value })}
                  placeholder="Database Systems"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="note-topics">
                Topics <span className="font-normal text-muted-foreground">(optional, comma-separated)</span>
              </Label>
              <Input
                id="note-topics"
                value={form.topics}
                onChange={(e) => update({ topics: e.target.value })}
                placeholder="normalization, 1NF, anomalies"
              />
            </div>

            <Tabs value={mode} onValueChange={(value) => setMode(value as 'paste' | 'upload')}>
              <TabsList>
                <TabsTrigger value="paste">
                  <ClipboardPaste />
                  Paste text
                </TabsTrigger>
                <TabsTrigger value="upload">
                  <FileUp />
                  Upload file
                </TabsTrigger>
              </TabsList>

              <TabsContent value="paste">
                <Textarea
                  rows={10}
                  value={form.text}
                  onChange={(e) => update({ text: e.target.value, filename: '' })}
                  placeholder="Paste a lecture, summary or textbook section..."
                  aria-label="Note content"
                />
              </TabsContent>

              <TabsContent value="upload">
                <label
                  htmlFor="note-file"
                  onDragOver={(e) => e.preventDefault()}
                  onDrop={(e) => {
                    e.preventDefault();
                    void handleFile(e.dataTransfer.files[0]);
                  }}
                  className="flex cursor-pointer flex-col items-center justify-center gap-2 rounded-lg border-2 border-dashed px-6 py-10 text-center transition-colors hover:bg-muted/60"
                >
                  <FileUp className="h-6 w-6 text-muted-foreground" />
                  {form.filename ? (
                    <span className="text-sm font-medium">{form.filename}</span>
                  ) : (
                    <span className="text-sm font-medium">Drop a file here or click to choose</span>
                  )}
                  <span className="text-xs text-muted-foreground">.txt or .md (PDF support is coming)</span>
                  <input
                    id="note-file"
                    type="file"
                    accept={ACCEPTED_FILES}
                    className="sr-only"
                    onChange={(e) => void handleFile(e.target.files?.[0])}
                  />
                </label>
              </TabsContent>
            </Tabs>

            {error ? (
              <p className="flex items-start gap-2 rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
                <TriangleAlert className="mt-0.5 h-4 w-4 shrink-0" />
                {error}
              </p>
            ) : null}

            <DialogFooter className="items-center gap-2">
              <span className="mr-auto text-xs text-muted-foreground">{wordCount} words</span>
              <Button type="submit" disabled={submitting}>
                {submitting ? <Loader2 className="animate-spin" /> : null}
                {submitting ? 'Adding...' : 'Add to library'}
              </Button>
            </DialogFooter>
          </form>
        )}
      </DialogContent>
    </Dialog>
  );
}
