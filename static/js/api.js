// static/js/api.js
export const API_BASE = 'http://127.0.0.1:3000';

export async function apiFetch(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, options);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res;
}
