import type { AskRequest, AskResponse, IngestRequest, IngestResponse, LibraryDocument } from '@/types';

export const BACKEND_URL: string = import.meta.env.VITE_BACKEND_URL || 'http://127.0.0.1:8000';

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${BACKEND_URL}${path}`, {
      ...init,
      headers: { 'Content-Type': 'application/json', ...init?.headers },
    });
  } catch {
    throw new Error(`Can't reach the Recall API at ${BACKEND_URL}. Is the backend running?`);
  }

  if (!response.ok) {
    const text = await response.text();
    let message = text;
    try {
      // FastAPI errors look like {"detail": "..."}.
      const detail = JSON.parse(text).detail;
      if (typeof detail === 'string') message = detail;
    } catch {
      // Not JSON; keep the raw text.
    }
    throw new Error(message || `Request failed with ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export function ask(payload: AskRequest) {
  return request<AskResponse>('/ask', { method: 'POST', body: JSON.stringify(payload) });
}

export function ingest(payload: IngestRequest) {
  return request<IngestResponse>('/ingest', { method: 'POST', body: JSON.stringify(payload) });
}

export function deleteDocument(documentId: string) {
  return request<{ status: string; vector_chunks_deleted: number; bm25_chunks_deleted: number }>(
    `/documents/${encodeURIComponent(documentId)}`,
    { method: 'DELETE' },
  );
}

export async function listDocuments() {
  const data = await request<{ documents: LibraryDocument[] }>('/documents');
  return data.documents ?? [];
}
