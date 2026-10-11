// Parses grounded answers, which cite sources as [S1], [S2], ... (app/orchestration/prompts.py).

export type AnswerSegment =
  | { kind: 'text'; text: string }
  | { kind: 'bold'; text: string }
  | { kind: 'cite'; sourceIndex: number; label: string };

// Matches [S1] and, defensively, grouped forms such as [S1, S3].
const CITATION = /\[(S\d+(?:\s*,\s*S\d+)*)\]/g;
const INLINE = /(\*\*[^*]+\*\*|\[S\d+(?:\s*,\s*S\d+)*\])/g;

export function parseInline(line: string, sourceCount: number): AnswerSegment[] {
  const segments: AnswerSegment[] = [];

  for (const part of line.split(INLINE)) {
    if (!part) continue;

    if (part.startsWith('**') && part.endsWith('**') && part.length > 4) {
      segments.push({ kind: 'bold', text: part.slice(2, -2) });
      continue;
    }

    const citation = part.match(/^\[(S\d+(?:\s*,\s*S\d+)*)\]$/);
    if (citation) {
      for (const label of citation[1].split(/\s*,\s*/)) {
        const sourceIndex = Number(label.slice(1)) - 1;
        // A label the API didn't return a source for stays visible as plain text.
        if (sourceIndex >= 0 && sourceIndex < sourceCount) {
          segments.push({ kind: 'cite', sourceIndex, label });
        } else {
          segments.push({ kind: 'text', text: `[${label}]` });
        }
      }
      continue;
    }

    segments.push({ kind: 'text', text: part });
  }

  return segments;
}

export function citedSourceIndexes(answer: string, sourceCount: number): Set<number> {
  const cited = new Set<number>();
  for (const match of answer.matchAll(CITATION)) {
    for (const label of match[1].split(/\s*,\s*/)) {
      const index = Number(label.slice(1)) - 1;
      if (index >= 0 && index < sourceCount) cited.add(index);
    }
  }
  return cited;
}
