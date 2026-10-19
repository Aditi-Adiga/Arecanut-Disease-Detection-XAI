export async function getJson(path, options = {}) {
  const response = await fetch(path, options);
  let body;
  try { body = await response.json(); } catch { throw new Error('The server returned an unreadable response. Check that FastAPI is running.'); }
  if (!response.ok) throw new Error(typeof body.detail === 'string' ? body.detail : 'The request could not be completed.');
  return body;
}

export function analyseImage(file, signal) {
  const data = new FormData();
  data.append('file', file);
  return getJson('/api/predict', { method: 'POST', body: data, signal });
}
