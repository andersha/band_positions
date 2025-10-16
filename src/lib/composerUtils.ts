export function normalizeComposerName(name: string): string {
  return name.replace(/\s+/g, ' ').trim();
}

const ARRANGEMENT_PATTERN = /(,?\s*(arr\.?|arrangement|arrang\.?|bearb\.?|bearbeidet|trans\.?|transcribed|transkr\.?|transponert)\b[^,;]*)/gi;

function removeArrangementInfo(raw: string): string {
  return raw.replace(ARRANGEMENT_PATTERN, '').trim();
}

export function extractComposerNames(raw: string | null | undefined): string[] {
  if (!raw) return [];
  const cleanedArrangement = removeArrangementInfo(raw);
  if (!cleanedArrangement) return [];

  const replacedDelimiters = cleanedArrangement
    .replace(/\s+(?:og|and)\s+/gi, ',')
    .replace(/[&/·]/g, ',');

  const parts = replacedDelimiters
    .split(/[;,]/)
    .map((part) => normalizeComposerName(part))
    .filter((part) => part.length > 0);

  const unique = new Map<string, string>();
  for (const name of parts) {
    const key = name.toLowerCase();
    if (!unique.has(key)) {
      unique.set(key, name);
    }
  }

  return Array.from(unique.values());
}

export function getPrimaryComposer(raw: string | null | undefined): string | null {
  const names = extractComposerNames(raw);
  return names.length > 0 ? names[0] : null;
}
