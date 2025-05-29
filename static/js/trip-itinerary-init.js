// trip-itinerary-init.js
import { loadSessionPlan }        from './plan-api.js';
import { renderItinerary, attachExtraButtonHandlers } from './render.js';

(async()=>{
  const params    = new URLSearchParams(location.search);
  const sessionId = params.get('sessionId');
  if (!sessionId) {
    document.getElementById('itineraryApp').innerHTML = 
      '<div class="error">Нет sessionId в URL</div>';
    return;
  }

  let plan;
  try {
    plan = await loadSessionPlan(sessionId);
  } catch(e) {
    document.getElementById('itineraryApp').innerHTML =
      `<div class="error">${e.message}</div>`;
    return;
  }

  window.itinerary = plan;
  renderItinerary(plan);
  attachExtraButtonHandlers();
})();
