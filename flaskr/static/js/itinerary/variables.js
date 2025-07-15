export const GEOCODING_URL =
  "https://geocode-maps.yandex.ru/1.x/?apikey=2cf712cf-75d8-4bbf-9611-9bccf9ccc15a&format=json&lang=ru_RU";
export const POIS = [];

let totalLats = 0;
let totalLons = 0;

Array.from(document.getElementsByClassName("poi")).forEach(element => {
  let posit = { lon: element.dataset.lon, lat: element.dataset.lat };
  if (element.dataset.lat != "None" && element.dataset.lon != "None") {
    POIS.push({ name: element.dataset.name, location: posit });
    totalLats += parseFloat(element.dataset.lat);
    totalLons += parseFloat(element.dataset.lon);
  }
});

const centerLats = totalLats / POIS.length;
const centerLons = totalLons / POIS.length;

export const START_VIEW_LOCATION = {
  lon: centerLons,
  lat: centerLats,
};
