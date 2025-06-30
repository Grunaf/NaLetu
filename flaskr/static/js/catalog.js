const checkedCityName = document.getElementById("cityName")
const citiesModal = document.getElementsByClassName("cities-modal")[0]
document.getElementById("departureCity").addEventListener('click', async() => {
  citiesModal.classList.remove("hidden");
});
Array.from(citiesModal.children).forEach(element => {
  element.onclick = async () => {
    const cityId = element.dataset.cityId;
    checkedCityName.innerText = element.innerText;
    checkedCityName.dataset.cityId = cityId;

    const coords = element.dataset.coords;
    checkedCityName.dataset.coords = coords;
    citiesModal.classList.add("hidden");
    updateDistances();
  }; 
});

Array.from(document.getElementsByClassName("btn-to-itinerary")).forEach(element => {
  element.onclick = async() => {
    const departureCityId = checkedCityName.dataset.cityId
    routeId = element.dataset.routeId;
    const res = await fetch('/api/session/create_or_get', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({"routeId": routeId, "departureCityId": departureCityId})
    });
    const data = await res.json();
    location.replace(`/trip-setup?sessionId=${data.sessionId}`);
  }
});


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
  const userCoords = checkedCityName.dataset.coords.split(",");
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