// static/js/catalog_routes.js
/**
 * Возвращает строку вида "1 час", "2 часа", "5 часов"
 * @param {number} hours — количество часов (может быть дробным)
 */
function formatHours(hours) {
  const n = Math.round(hours);
  const rem100 = n % 100;
  const rem10  = n % 10;
  let word;
  if (rem100 >= 11 && rem100 <= 14) {
    word = 'часов';
  } else if (rem10 === 1) {
    word = 'час';
  } else if (rem10 >= 2 && rem10 <= 4) {
    word = 'часа';
  } else {
    word = 'часов';
  }
  return `${n} ${word}`;
}

// 1) получаем геолокацию
let userCoords = [55.75, 37.61];
document.getElementById('geoBtn').onclick = () => {
  navigator.geolocation.getCurrentPosition(p=> {
    userCoords = [p.coords.latitude, p.coords.longitude];
    updateDistances();
  });
};
document.getElementById('manualLocation').onchange = e => {
  const [, lat, lon] = e.target.value.split(',');
  userCoords = [parseFloat(lat), parseFloat(lon)];
  updateDistances();
};
// 2) рассчитываем haversine
function haversine(lat1, lon1, lat2, lon2) {
  const toRad = deg => deg * Math.PI / 180;
  const R = 6371;
  const dLat = toRad(lat2 - lat1);
  const dLon = toRad(lon2 - lon1);
  const a = Math.sin(dLat/2)**2 + Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLon/2)**2;
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}
// 3) для каждой карточки берём data-атрибуты
function updateDistances() {
  document.querySelectorAll('.route-card').forEach(card => {
    const lat = parseFloat(card.dataset.startLat);
    const lon = parseFloat(card.dataset.startLon);
    if (!isNaN(lat)) {
      const km = haversine(userCoords[0],userCoords[1],lat,lon);
      card.querySelector('.route-meta .road_time').textContent = 
        `${formatHours(km / 60)}`;
    }
  });
}


function updateBudget() {
  let total = 0;
  
  // Парсим отмеченные radio
  document.querySelectorAll('input[type=radio]:checked').forEach(input => {
    const cost = parseInt(input.dataset.cost || 0);
    if (!isNaN(cost)) total += cost;
  });
  
  document.getElementById('budgetAmount').textContent = total;
}
window.updateBudget = updateBudget;

// 4) при загрузке сразу запустить
updateDistances();
// const app = document.getElementById('app');
// //let userCoords = null;
// let userCoords = [parseFloat(55.75), parseFloat(37.61)];
// app.innerHTML = `
//   <div id="cards"></div>
// `;
// const cards = document.getElementById('cards');
// document.getElementById('geoBtn').onclick = () => {
//   if (!navigator.geolocation) return alert("Геолокация не поддерживается");
//   navigator.geolocation.getCurrentPosition(pos => {
//     userCoords = [pos.coords.latitude, pos.coords.longitude];
//     loadRoutes();
//   }, () => alert("Не удалось определить местоположение"));
// };
// // async function createSession(routeId) {
// //   const payload = {
// //     routeId,
// //     checkIn: new Date().toISOString().slice(0,10),  // или пользователь выберет позже
// //     checkOut: new Date(Date.now() + 86400000*2).toISOString().slice(0,10), // +2 дня по умолчанию
// //     departure: {
// //       name: 'Москва', // потом заменишь на выбор юзера
// //       lat: 55.7558,
// //       lon: 37.6173
// //     },
// //     choices: [] // пока пустой массив, пользователь заполнит позже
// //   };

// //   const res = await fetch('http://127.0.0.1:3000/api/session', {
// //     method: 'POST',
// //     headers: {'Content-Type': 'application/json'},
// //     body: JSON.stringify(payload)
// //   });

// //   if (!res.ok) throw new Error(`Ошибка сервера: ${res.status}`);
// //   const { sessionId } = await res.json();
// //   return sessionId;
// // }

// document.getElementById('manualLocation').onchange = e => {
//   const val = e.target.value;
//   if (!val) return;
//   const [, lat, lon] = val.split(',');
//   userCoords = [parseFloat(lat), parseFloat(lon)];
//   loadRoutes();
// };

// 

// function renderRouteCard(route) {
//   const card = document.createElement('div');
//   card.className = 'route-card';

//   let trackTimeText = '–';
//   if (route.start_coords && userCoords) {
//     const [lat, lon] = route.start_coords;
//     const km = haversine(userCoords[0], userCoords[1], lat, lon);
//     const hours = Math.round(km / 60); // если считать 60 км/ч
//     //const dist = haversine(userCoords[0], userCoords[1], lat, lon);
//     trackTimeText = `${hours} часов`;
//   }

//   card.innerHTML = `
//     <img src="${route.img}" alt="${route.title}">
//     <div class="route-info">
//       <h2 class="route-title">${route.title}</h2>
//       <div class="route-meta">${route.days} дня • ${trackTimeText} • Бюджет: ${route.budget}₽</div>
//       <p class="route-description">${route.description}</p>
//       <div class="route-actions">
//         <a href="trip-setup.html?routeId=${route.id}" class="btn">
//           Настроить поездку
//         </a>
//       </div>
//     </div>
//   `;
//   return card;
// }

// function loadRoutes() {
//   fetch('http://127.0.0.1:3000/api/routes')
//     .then(res => res.json())
//     .then(routes => {
//       cards.innerHTML = ''; // Очищаем перед отрисовкой
//       routes.forEach(route => {
//         const card = renderRouteCard(route);
//         cards.appendChild(card);
//       });
//     })
//     .catch(err => {
//       app.innerHTML = `<div class="error">Не удалось загрузить маршруты: ${err.message}</div>`;
//     });
// }

// // при загрузке страницы:
// loadRoutes();
