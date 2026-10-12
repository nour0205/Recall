import { useCallback, useEffect, useState } from 'react';
import type { LibraryDocument, View } from '@/types';
import { listDocuments } from '@/lib/api';
import AppHeader from '@/components/AppHeader';
import AddNotesDialog from '@/components/AddNotesDialog';
import DeleteNoteDialog from '@/components/DeleteNoteDialog';
import AskPage from '@/pages/AskPage';
import LibraryPage from '@/pages/LibraryPage';

export default function App() {
  const [view, setView] = useState<View>('ask');
  const [addingNotes, setAddingNotes] = useState(false);
  const [scope, setScope] = useState<string[]>([]);
  const [deleting, setDeleting] = useState<string | null>(null);

  const [documents, setDocuments] = useState<LibraryDocument[]>([]);
  const [libraryLoading, setLibraryLoading] = useState(false);
  const [libraryError, setLibraryError] = useState<string | null>(null);
  const [libraryLoaded, setLibraryLoaded] = useState(false);

  const refreshLibrary = useCallback(async () => {
    setLibraryLoading(true);
    setLibraryError(null);
    try {
      const docs = await listDocuments();
      setDocuments(docs.sort((a, b) => a.document_id.localeCompare(b.document_id)));
      setLibraryLoaded(true);
    } catch (err) {
      setLibraryError(err instanceof Error ? err.message : 'Could not load the library.');
    } finally {
      setLibraryLoading(false);
    }
  }, []);

  useEffect(() => {
    void refreshLibrary();
  }, [refreshLibrary]);

  return (
    <div className="min-h-screen">
      <AppHeader view={view} onNavigate={setView} onAddNotes={() => setAddingNotes(true)} />

      <main>
        {view === 'ask' ? (
          <AskPage
            documents={documents}
            libraryLoaded={libraryLoaded}
            scope={scope}
            onScopeChange={setScope}
            onAddNotes={() => setAddingNotes(true)}
          />
        ) : (
          <LibraryPage
            documents={documents}
            loading={libraryLoading}
            error={libraryError}
            onRefresh={() => void refreshLibrary()}
            onAddNotes={() => setAddingNotes(true)}
            onAskAbout={(documentId) => {
              setScope([documentId]);
              setView('ask');
            }}
            onDelete={setDeleting}
          />
        )}
      </main>

      <AddNotesDialog open={addingNotes} onOpenChange={setAddingNotes} onIngested={() => void refreshLibrary()} />
      <DeleteNoteDialog
        documentId={deleting}
        onClose={() => setDeleting(null)}
        onDeleted={(documentId) => {
          setScope((current) => current.filter((id) => id !== documentId));
          void refreshLibrary();
        }}
      />
    </div>
  );
}
