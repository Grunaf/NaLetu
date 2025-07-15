import { POIS } from "./variables.js";
import { InitMap } from "./init_map.js";

var map = InitMap();

const mealSpotIcon = new L.Icon({
  iconUrl: "/static/img/marker-icon-meal.png",
  iconSize: [52, 52],
  iconAnchor: [28, 52],
  popupAnchor: [1, -40],
  shadowUrl: null,
  shadowSize: null,
  shadowAnchor: null,
});
const attractionIcon = new L.Icon({
  iconUrl: "/static/img/marker-icon-attraction.png",
  iconSize: [52, 52],
  iconAnchor: [28, 52],
  popupAnchor: [1, -40],
  shadowUrl: null,
  shadowSize: null,
  shadowAnchor: null,
});
const yandex = new L.yandex("map");
map.addLayer(yandex);

function createMarkersForPOIs(POIS, icon, layer = null) {
  const markers = [];
  POIS.forEach(poi => {
    const location = poi.location;
    const spotName = poi.name;
    const marker = L.marker([location.lat, location.lon], {
      icon: icon,
      spotName: spotName,
    });
    if (!layer) {
      marker.addTo(map);
    } else {
      layer.addLayer(marker);
    }
    marker.bindPopup(`<div>${poi.name}<div>`);
    return markers.push(marker);
  });
  return markers;
}

createMarkersForPOIs(POIS, attractionIcon);

function highlightOption(spotName) {
  const spotOption = document.querySelector(`input[data-name='${spotName}']`);
  const label = spotOption.parentElement;
  label.scrollIntoView({
    behavior: "smooth",
    block: "nearest",
  });
  spotOption.click();
}
export let similarSpotsMarkers = [];

let similarsSpotsMarkersLayer = L.layerGroup().addTo(map);
window.addEventListener("showedSimilarSpots", event => {
  similarsSpotsMarkersLayer.clearLayers();
  similarSpotsMarkers = createMarkersForPOIs(
    event.detail.detailSpots,
    mealSpotIcon,
    similarsSpotsMarkersLayer,
  );
  similarSpotsMarkers.forEach(spotMarker => {
    spotMarker.on("click", () => {
      highlightOption(spotMarker.options.spotName);
    });
  });
});
