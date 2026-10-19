const KEY = 'arecalens-scans-v1';

export function readHistory() {
  try {
    const data = JSON.parse(localStorage.getItem(KEY) || '[]');
    return Array.isArray(data) ? data : [];
  } catch { return []; }
}

export function saveHistory(result, name) {
  // Resized images only. Cap history to keep browser storage predictable.
  const entry = { id: crypto.randomUUID(), createdAt: new Date().toISOString(), name, result };
  const items = [entry, ...readHistory()].slice(0, 8);
  try { localStorage.setItem(KEY, JSON.stringify(items)); return { items, saved: true }; }
  catch { return { items: readHistory(), saved: false }; }
}

export function clearHistory() { localStorage.removeItem(KEY); }
