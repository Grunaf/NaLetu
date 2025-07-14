import { START_VIEW_LOCATION } from "./variables.js";

var map;

export function InitMap() {
  if (!map) {
    map = L.map("map", { attributionControl: false }).setView(
      [START_VIEW_LOCATION.lat, START_VIEW_LOCATION.lon], // Change to Ci
      13,
    );
  }
  return map;
}
