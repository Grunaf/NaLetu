// static/js/plan-api.js

import { apiFetch } from './api.js';

/**
 * Загружает план поездки по sessionId
 * @param {string} sessionId
 * @returns {Promise<object>} план (itinerary)
 */
export async function loadSessionPlan(sessionId) {
  // GET запрос к /api/session/{sessionId}/plan
  const res = await apiFetch(`/api/session/${sessionId}/plan`, {
    method: 'GET'
  });

  // apiFetch бросит ошибку, если res.ok === false, но на всякий случай:
  if (!res.ok) {
    throw new Error(`Ошибка при загрузке плана: ${res.status}`);
  }

  return await res.json();
}
