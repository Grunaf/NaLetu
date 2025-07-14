import { POIS, START_VIEW_LOCATION } from "./variables.js";

var map = L.map("map", { attributionControl: false }).setView(
  [START_VIEW_LOCATION.lat, START_VIEW_LOCATION.lon], // Change to Ci
  13,
);

const yandex = new L.yandex("map");
map.addLayer(yandex);

const markers = POIS.forEach(poi => {
  const location = poi.location;
  const marker = L.marker([location.lat, location.lon]).addTo(map);
  marker.bindPopup(`<div>${poi.name}<div>`);
});
