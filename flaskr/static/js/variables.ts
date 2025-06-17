import {LngLat, type YMapLocationRequest} from '@yandex/ymaps3-types';

export const GEOCODING_URL = 'https://geocode-maps.yandex.ru/1.x/?apikey=2cf712cf-75d8-4bbf-9611-9bccf9ccc15a&format=json&lang=ru_RU';
export const POIS = []
let totalLats = 0
let totalLons = 0
Array.from(document.getElementsByClassName("poi")).forEach(element =>{
  let posit: LngLat = [element.dataset.lon, element.dataset.lat]
  if (element.dataset.lat != "None" && element.dataset.lon != "None") {
    POIS.push({ "name": element.dataset.name, "location": posit});
    totalLats += parseFloat(element.dataset.lat);
    totalLons += parseFloat(element.dataset.lon);
  }
});
const centerLats = totalLats / POIS.length;
const centerLons = totalLons / POIS.length;
console.log(totalLats, POIS.length)
export const LOCATION: YMapLocationRequest = {
  center: [centerLons, centerLats], // starting position [lng, lat]
  zoom: 14 // starting zoom
};
console.log(POIS);
export const TRANSLATIONS = {
  infoText: 'Нажмите иконку «Парк Стрелка»',
  balloonTitle: 'Парк «Стрелка»',
  balloonDescription:
    'Одна из главных достопримечательностей Ярославля. Он расположен на стрелке рек Волги и Которосли.',
  address: 'Адрес'
};
