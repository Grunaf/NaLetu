// static/js/session-api.js

/**
 * Создаёт новую сессию на сервере.
 * @param {{routeId:string, departure:{name:string,lat:number,lon:number}, checkIn:string, checkOut:string, choices:string[]}} data
 * @returns {Promise<string>} sessionId
 */
export async function createSession(data) {
  const res = await fetch('/api/session', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      routeId:      data.routeId,
      departure:    data.departure,
      checkIn:      data.checkIn,
      checkOut:     data.checkOut,
      choices:      data.choices
    })
  });
  if (!res.ok) {
    throw new Error(`Ошибка при создании сессии: ${res.status}`);
  }
  const { sessionId } = await res.json();
  return sessionId;
}
