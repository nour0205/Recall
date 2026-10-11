// Mirrors app/schemas/api.py.
export type Source = {
  document_id: string;
  chunk_index?: number | null;
  text: string;
  retrieval_type?: string | null;
  hybrid_score?: number | null;
  rerank_score?: number | null;
};

export type AskRequest = {
  question: string;
  document_ids?: string[];
};

export type AskResponse = {
  answer: string;
  sources: Source[];
  route?: string | null;
  study_hint?: string | null;
};

export type IngestRequest = {
  document_id: string;
  text: string;
  document_type: 'lecture_note';
  source?: string;
  course?: string;
  topic_tags?: string[];
};

export type IngestResponse = {
  status: 'ingested' | 'duplicate' | 'conflict' | 'no content' | string;
  chunks_added?: number;
};

export type LibraryDocument = {
  document_id: string;
  chunks: number;
  preview: string | null;
};

export type View = 'ask' | 'library';
