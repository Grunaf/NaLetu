// static/js/render.js

/**
 * Рендерит первый шаг — выбор POI-варинатов (из main.js → renderStep1)
 * @param {object} itinerary
 */
export function renderStep1(itinerary) {
  const container = document.getElementById('poiOptions');
  container.innerHTML = '';

  // Заголовок тура
  document.getElementById('tourTitle').textContent = itinerary.title;

  // Карточка «Варианты маршрутов (POI)»
  const headerCard = document.createElement('div');
  headerCard.className = 'card';
  headerCard.innerHTML = `<div class="card-header">Варианты маршрутов (POI)</div>`;
  container.appendChild(headerCard);

  // Для каждого дня
  itinerary.day_variants.forEach(day => {
    const dayTitle = document.createElement('div');
    dayTitle.className = 'section-title';
    dayTitle.textContent = `День ${day.day}`;
    container.appendChild(dayTitle);

    day.variants.forEach((v, idx) => {
      const pois = v.segments
        .filter(s => s.poi)
        .slice(0,3)
        .map(s => s.poi.name)
        .join(' → ');

      const div = document.createElement('div');
      div.className = 'route-card';
      div.innerHTML = `
        <div class="marker">${day.day}.${idx+1}</div>
        <div style="flex:1">
          <label class="route-radio">
            <input type="radio" name="day${day.day}" value="${v.variant_id}" ${idx===0?'checked':''}>
            <span class="route-title">${v.name}</span>
          </label>
          <div class="route-pois">${pois}${v.segments.length>3?' …':''}</div>
        </div>
        <span class="cost-pill">от ${v.est_budget} ₽</span>
      `;
      container.appendChild(div);
    });
  });

  // Минимальная стоимость
  const mc = computeMinCost(itinerary);
  const costEl = document.createElement('div');
  costEl.className = 'small';
  costEl.style.margin = '12px';
  costEl.textContent = `Минимальная стоимость: от ${mc} ₽`;
  container.appendChild(costEl);

  // Активируем кнопку «Далее»
  function checkReady() {
    const ready = itinerary.day_variants.every(d =>
      !!document.querySelector(`input[name="day${d.day}"]:checked`)
    );
    document.getElementById('goToItinerary').disabled = !ready;
  }
  container.addEventListener('change', checkReady);
  checkReady();
}

/**
 * Вычисляет минимальную стоимость поездки
 */
function computeMinCost(itinerary) {
  const tThere = Math.min(...itinerary.transport.options.map(o => o.there.cost_rub));
  const tBack  = Math.min(...itinerary.transport.options.map(o => o.back.cost_rub));
  const daily  = itinerary.day_variants
    .reduce((sum, d) =>
      sum + Math.min(...d.variants.map(v => v.est_budget))
    , 0);
  return tThere + tBack + daily;
}

/**
 * Рендерит детальный маршрут (из main.js → renderItinerary)
 */
export function renderItinerary(itinerary) {
  const app = document.getElementById('itineraryApp');
  app.innerHTML = ''; // очищаем

  // Заголовок
  const header = document.createElement('div');
  header.className = 'card';
  header.innerHTML = `<div class="card-header">${itinerary.title}</div>`;
  app.appendChild(header);

  // Транспорт
  const transCard = document.createElement('div');
  transCard.className = 'card';
  renderTransportOptions(itinerary, transCard);
  app.appendChild(transCard);

  // Погодный фильтр
  const weatherCard = document.createElement('div');
  weatherCard.className = 'card';
  weatherCard.innerHTML = `
    <div class="card-header">Погода</div>
    <div class="list-item">
      <label><input type="radio" name="weather" value="good" checked> С прогулками</label><br>
      <label><input type="radio" name="weather" value="bad"> Без прогулок</label>
    </div>`;
  app.appendChild(weatherCard);

  // Контейнер для маршрута
  const routeContainer = document.createElement('div');
  app.appendChild(routeContainer);

  // Карточка с итоговой выборкой
  const costCard = document.createElement('div');
  costCard.className = 'card';
  app.appendChild(costCard);

  // Флаги
  let goodWeather = true;
  document.querySelectorAll('input[name="weather"]').forEach(i =>
    i.addEventListener('change', e => {
      goodWeather = e.target.value === 'good';
      renderRoute();
      renderSummary();
    })
  );

  // Основные функции
  function renderRoute() {
    routeContainer.innerHTML = '';
    const optThere = itinerary.transport.options[selectedThere];
    const baseHour = 9 + Math.floor(optThere.there.time_min/60);
    let currH = baseHour;

    itinerary.day_variants.forEach(day => {
      const v = day.variants.find(v => v.variant_id === chosenVariants[day.day-1]);
      const dayCard = document.createElement('div');
      dayCard.className = 'card';
      dayCard.innerHTML = `<div class="card-header">День ${day.day}</div>`;
      v.segments.forEach(seg => {
        if (!goodWeather && seg.poi?.weather_constraints) return;
        const item = document.createElement('div');
        item.className = 'list-item';
        if (seg.poi) {
          item.innerHTML = `<strong>${seg.poi.name}</strong> ${seg.arrival_window||''}`;
          currH += 2;
        }
        if (seg.meal) {
          item.innerHTML = `<strong>${seg.meal.type==='lunch'?'Обед':'Ужин'}</strong>`;
          currH += 1;
        }
        dayCard.appendChild(item);
      });
      routeContainer.appendChild(dayCard);
    });
  }

  function renderSummary() {
    let total = 0;
    const there = itinerary.transport.options[selectedThere].there;
    const back  = itinerary.transport.options[selectedBack].back;
    total += there.cost_rub + back.cost_rub;
    // варианты дня
    itinerary.day_variants.forEach(d => {
      const v = d.variants.find(v=>v.variant_id===chosenVariants[d.day-1]);
      total += v.est_budget;
    });
    costCard.innerHTML = `
      <div class="card-header">Итого:</div>
      <div class="list-item"><strong>${total} ₽</strong></div>`;
  }

  // Состояние
  let selectedThere = 0, selectedBack = 0;
  const chosenVariants = itinerary.day_variants.map(d=>d.variants[0].variant_id);

  // Рендер транспорта
  function renderTransportOptions(itin, container) {
    container.innerHTML = `<div class="card-header">Транспорт</div>`;
    ['there','back'].forEach(dir => {
      const title = document.createElement('div');
      title.className = 'section-title';
      title.textContent = dir === 'there' ? 'Туда' : 'Обратно';
      container.appendChild(title);
      itin.transport.options.forEach((opt, idx) => {
        const side = dir==='there'?'there':'back';
        const o = opt[side];
        const li = document.createElement('div');
        li.className = 'list-item';
        li.innerHTML = `
          <label>
            <input type="radio" name="trans_${dir}" value="${idx}" 
              ${((dir==='there'?selectedThere:selectedBack) === idx)?'checked':''}>
            ${opt.mode}: ${o.from}→${o.to} (~${o.time_min}мин, ${o.cost_rub}₽)
          </label>`;
        li.querySelector('input').addEventListener('change', ()=> {
          if (dir==='there') selectedThere = idx;
          else selectedBack = idx;
          renderRoute();
          renderSummary();
        });
        container.appendChild(li);
      });
    });
  }

  renderRoute();
  renderSummary();
}

/**
 * Подвешивает кнопки Export/Invite (из main.js)
 */
export function attachExtraButtonHandlers() {
  // copy your existing handlers from main.js here...
}
