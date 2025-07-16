let index_poi_name = 1;

const route_container = document.getElementById("route");
const days_container = document.getElementById("days");

const dayControlButtonHTML = `
    <div class="dayControlButton">
        <button class="btn bg-primary" type="button" onclick="addDay()">Добавить день</button>
        <button class="btn bg-primary" type="button" onclick="dropDay(this)">Удалить последний день</button>
    </div>
    `;

const variantControlButtonsHTML = `
    <div class="variantsControlButton">
        <button class="btn bg-primary" type="button" onclick="addVariant(this)">Добавить вариант дня</button>
        <button class="btn bg-primary" type="button" onclick="dropVariant(this)">Удалить последний вариант дня</button>
    </div>`;

const segmentAddButtonsHTML = `
    <div class="segmentAddButton">
        <button class="btn bg-primary" type="button" onclick="addSegment(this, 'poi')">Добавить точку</button>
        <button class="btn bg-primary" type="button" onclick="addSegment(this, 'meal')">Добавить время на поесть</button>
    </div>`;

const timeSegmentHTML = `
    <input type="time" name="start-time">
    <input type="time" name="end-time">`;

const poiSegmentHTML = `
    <div class="segment" data-type="poi">
        <label>Название достопримечательности:</label>
        <input type="text" oninput="pausedFetchHint(this)" id="poi-name" name="poi-name" autocomplete="off">
        <div class="poi-hints"></div>
        ${timeSegmentHTML}
        <button class="btn bg-primary" type="button" onclick="this.parentElement.remove()">Удалить</button>
    </div>`;

const mealSegmentHTML = `
    <div class="segment" data-type="meal">
        <strong>Перерыв на поесть</strong>
        ${timeSegmentHTML}
        <button class="btn bg-primary" type="button" onclick="this.parentElement.remove()">Удалить</button>
    </div>`;

const dayVariantHTML = `
    <div class="variant">
    <div class="segments">
        ${poiSegmentHTML}
    </div>
    ${segmentAddButtonsHTML}
    </div>`;

const dayHTML = `
    <div class="day">
    <div class="variants">
        ${dayVariantHTML}
    </div>
    ${variantControlButtonsHTML}
    </div>`;
    
route_container.insertAdjacentHTML("beforeend", dayControlButtonHTML)

function dropDay(buttonSender) {
    const lastDay = buttonSender.parentNode.previousElementSibling.lastChild
    lastDay.remove()
}
function dropVariant(buttonSender) {
    const lastVariant = buttonSender.parentNode.previousElementSibling.lastChild
    lastVariant.remove()
}
function addDay() {
    days_container.insertAdjacentHTML("beforeend", dayHTML)
}

function addVariant(buttonSender) {
    const variants_container = buttonSender.parentNode.previousElementSibling
    variants_container.insertAdjacentHTML("beforeend", dayVariantHTML)
}
function addSegment(buttonSender, type) {
    const segments_container = buttonSender.parentNode.previousElementSibling

    let segmentToAdd;
    switch(type) {
        case "poi":
            segmentToAdd = poiSegmentHTML
            break;
        case "meal":
            segmentToAdd = mealSegmentHTML
            break;
    }
    segments_container.insertAdjacentHTML("beforeend", segmentToAdd)
}
let timeout;
function pausedFetchHint(inputPOIName) {
    clearTimeout(timeout);
    const value = inputPOIName.value;
    timeout = setTimeout(() => {
        fetchHint(value, inputPOIName);
    }, 800);
}

async function fetchHint(query, inputPOIName) {
    const hintBox = inputPOIName.parentNode.querySelector(".poi-hints");
    if (query.length < 2) {
        hintBox.innerHTML = "";
        return;
    }
    const selectCityElement = document.getElementById("city");
    const selectedCityElement = selectCityElement.options[selectCityElement.selectedIndex];
    const cityCoords = selectedCityElement.dataset.coords;

    const resp = await fetch("/api/poi/hints?q=" + encodeURIComponent(query) + "&location=" + encodeURIComponent(cityCoords))
    const data = await resp.json()
    if (resp.status == 200) {
        hintBox.innerHTML = data.map(poi => `<div onclick="selectHint(this, '${poi.name}', '${poi.id}')">${poi.name}</div>`).join("")
    }
    else {
        console.log(resp.code, data.message)
    }
};

function selectHint(hintsElement, name, dgis_id) {
    const inputPOIName = hintsElement.parentNode.previousElementSibling;
    inputPOIName.value = name;
    inputPOIName.dataset.dgisId = dgis_id;

    inputPOIName.parentNode.querySelector(".poi-hints").innerHTML = "";
}

function assembleRoute() {
    const routeTitle = document.getElementById("route_title").value;
    const routeImgURI = document.getElementById("route_img").value;
    const cityId = document.getElementById("city").value;
    const days = assembleDays()
    
    return {
        "city_id": cityId,
        "days": days,
        "img": routeImgURI,
        "title": routeTitle
    }
}
function assembleDays() {
    let days = [];
    const daysList = days_container.children
    for (let day_index = 0; day_index < daysList.length; day_index++) {
        const day = daysList[day_index];
        days.push(assembleDay(day));
    }
    return days;
}
function assembleDay(day_container) {
    let day = [];
    const variantsList = day_container.querySelector(".variants").children
    for (let variant_index = 0; variant_index < variantsList.length; variant_index++) {
        const variant = variantsList[variant_index];
        day.push(assembleDayVariant(variant));
    }
    return day;
}
function assembleDayVariant(variant_container) {
    let variant = [];
    const segmentsList = variant_container.querySelector(".segments").children
    for (let segment_index=0; segment_index < segmentsList.length; segment_index++) {
        const segment = segmentsList[segment_index];
        variant.push(assembleSegment(segment));
    }
    return variant;
}
function assembleSegment(segment_block) {
    const typeSegment = segment_block.dataset.type;
    const startTime = segment_block.querySelector("[name='start-time']").value;
    const endTime = segment_block.querySelector("[name='end-time']").value;
    const cityIdSegment = document.getElementById("city").value;
    const segment = {
        "type": typeSegment,
        "start_time": startTime,
        "end_time": endTime,
        "city_id": cityIdSegment,
    };
    
    if (typeSegment == "poi") {
        const poi_dgis_id = segment_block.querySelector("[name='poi-name']").dataset.dgisId;
        segment["poi_dgis_id"] = poi_dgis_id;
    }

    return segment;
}
document.getElementById("btn-create-route").addEventListener("click", async() => {
    const assembledRoute = assembleRoute();
    const resp = await fetch("/api/route/", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(assembledRoute)
    });
});