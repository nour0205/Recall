import { useState } from 'react';
import { Loader2, TriangleAlert } from 'lucide-react';
import { deleteDocument } from '@/lib/api';
import { documentTitle } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';

export default function DeleteNoteDialog({
  documentId,
  onClose,
  onDeleted,
}: {
  documentId: string | null;
  onClose: () => void;
  onDeleted: (documentId: string) => void;
}) {
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function confirm() {
    if (!documentId) return;
    setDeleting(true);
    setError(null);
    try {
      await deleteDocument(documentId);
      onDeleted(documentId);
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not delete the note.');
    } finally {
      setDeleting(false);
    }
  }

  return (
    <Dialog
      open={documentId !== null}
      onOpenChange={(open) => {
        if (!open && !deleting) {
          setError(null);
          onClose();
        }
      }}
    >
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Delete "{documentId ? documentTitle(documentId) : ''}"?</DialogTitle>
          <DialogDescription>
            Recall will no longer use this note to answer questions. This can't be undone, but you can add the note
            again later.
          </DialogDescription>
        </DialogHeader>

        {error ? (
          <p className="flex items-start gap-2 rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
            <TriangleAlert className="mt-0.5 h-4 w-4 shrink-0" />
            {error}
          </p>
        ) : null}

        <DialogFooter className="gap-2">
          <Button variant="outline" onClick={onClose} disabled={deleting}>
            Cancel
          </Button>
          <Button variant="destructive" onClick={() => void confirm()} disabled={deleting}>
            {deleting ? <Loader2 className="animate-spin" /> : null}
            {deleting ? 'Deleting...' : 'Delete note'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
