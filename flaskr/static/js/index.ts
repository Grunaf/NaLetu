import {TRANSLATIONS, LOCATION, MARKER_LOCATION, POIS} from '../variables';
import {InfoMessage, fetchGeoObject} from '../common';
import {MarkerPopupProps} from '@yandex/ymaps3-default-ui-theme';

async function main() {
    // Wait for ymaps3 and import required resources
    await ymaps3.ready;

    const {YMap, YMapDefaultSchemeLayer, YMapDefaultFeaturesLayer, YMapControls} = ymaps3;

    const {YMapDefaultMarker} = await ymaps3.import('@yandex/ymaps3-default-ui-theme');

    let show = false;

    // Initialize the map
    const map = new YMap(document.getElementById('map'), {location: LOCATION, showScaleInCopyrights: true}, [
        new YMapDefaultSchemeLayer({}),
        new YMapDefaultFeaturesLayer({})
    ]);
console.log(POIS)
 POIS.forEach(p=> {  // Create and set the marker popup content
    console.log(p);
    const createPopupContent = () => {
        const content = document.createElement('div');
        content.classList.add('balloon');
        content.id = `balloon-${p.name}`;
        content.innerHTML = `
      <p class="skeleton-title"></p>
      <div class="description-container">
        <p class="skeleton-description w60"></p>
        <p class="skeleton-description w80"></p>
        <p class="skeleton-description w70"></p>
        <p class="skeleton-description w40"></p>
      </div>
    `;
        return content;
    };

    // Update popup content with real data
    const updatePopupContent = async () => {
        const object = await fetchGeoObject(p.location);
        const popupContent = document.getElementById(`balloon-${p.name}`);
        if (object && popupContent) {
            popupContent.innerHTML = `
        <p class="title">${p.name}</p>
        <p class="description">
          ${TRANSLATIONS.address}: ${object.metaDataProperty.GeocoderMetaData.Address.formatted}
        </p>
      `;
        }
    };

    const handleMarkerClick = () => {
        show = !show;
        marker.update({popup: {show} as MarkerPopupProps});
        setTimeout(updatePopupContent, 3000);
    };

    const marker = new YMapDefaultMarker({
        coordinates: p.location,
        size: 'normal',
        iconName: 'fallback',
        onClick: handleMarkerClick,
        popup: {
            show,
            content: createPopupContent
        }
    });
    map.addChild(marker);
});
}

main();


// const {YMap, YMapDefaultSchemeLayer} = ymaps3;

// // Иницилиазируем карту
// const map = new YMap(
//     // Передаём ссылку на HTMLElement контейнера
//     document.getElementById('map'),

//     // Передаём параметры инициализации карты
//     {
//         location: {
//             // Координаты центра карты
//             center: [37.588144, 55.733842],

//             // Уровень масштабирования
//             zoom: 10
//         }
//     }
// );

// // Добавляем слой для отображения схематической карты
// map.addChild(new YMapDefaultSchemeLayer());

