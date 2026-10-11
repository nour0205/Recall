import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

const ACRONYMS = new Set(['ai', 'api', 'cpu', 'db', 'ml', 'nlp', 'os', 'sql']);

// "db_normalization_intro" -> "DB Normalization Intro"
export function documentTitle(documentId: string) {
  return documentId
    .split(/[_\-\s]+/)
    .filter(Boolean)
    .map((word) => (ACRONYMS.has(word.toLowerCase()) ? word.toUpperCase() : word.charAt(0).toUpperCase() + word.slice(1)))
    .join(' ');
}

// "Normalization Notes.md" -> "normalization_notes"
export function slugFromFilename(filename: string) {
  return filename
    .replace(/\.[^.]+$/, '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '_')
    .replace(/^_+|_+$/g, '');
}

export function routeLabel(route?: string | null) {
  const labels: Record<string, string> = {
    concept_explanation: 'Concept explanation',
    source_recall: 'Source recall',
    exam_preparation: 'Exam preparation',
  };
  return route ? labels[route] : undefined;
}
