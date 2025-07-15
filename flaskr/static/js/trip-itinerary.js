import { alert } from "./main.js";
import { SERVER_ERROR } from "./constants.js";
import { similarSpotsMarkers } from "./leaflet.js";
import { handleTransports } from "./transport.js";
import { expandeBudgetBlock, expancesBlock } from "./budget.js";
import { diffInDays } from "./utils.js";

const body = document.getElementById("body");
const sessionId = body.dataset.sessionId;
const startDateStr = body.dataset.startDate;
const startDateInput = document.getElementById("start-date");

const startDateSession = new Date(startDateStr);

const budgetAmount = document.getElementById("budgetAmount");
const simularSpots = document.getElementById("similar-spots-block");

handleTransports();
expandeBudgetBlock();

if (startDateInput) {
  startDateInput.addEventListener("change", async () => {
    const startDateValue = startDateInput.value;
    const resp = await fetch("/api/session/update_transports", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ startDate: startDateValue, sessionId }),
    });
    if (resp.status == 200) {
      location.reload();
    } else {
      alert(SERVER_ERROR.message, SERVER_ERROR.color);
    }
  });
}
function openPopupForSpotMarker(spotName) {
  const spotMarker = similarSpotsMarkers.find(
    marker => marker.options.spotName === spotName,
  );
  spotMarker.openPopup();
}

document.addEventListener("DOMContentLoaded", () => {
  const options = document.querySelectorAll("input[type='radio'][data-cost]");

  Array.from(options).forEach(option => {
    let dayOrder = null;
    if (option.closest(".day-block")) {
      dayOrder = option.closest(".day-block").dataset.dayOrder;
    } else {
      dayOrder = diffInDays(new Date(option.dataset.datetime));
    }
    option.addEventListener("click", () => updateBudgetBlock(option, dayOrder));
  });

  simularSpots.addEventListener("click", event => {
    const target = event.target;
    if (target.matches("input[type='radio'][data-cost]")) {
      const dayOrder = simularSpots.dataset.dayOrder;
      const mealType = simularSpots.dataset.mealType;
      const name_input = `meal_place_${dayOrder}_${mealType}`;
      const input = document.querySelectorAll(`input[name=${name_input}]`)[0];

      const spotName = target.dataset.name;

      openPopupForSpotMarker(spotName);
      updateBudgetBlock(target, dayOrder);
    }
  });
});
document.addEventListener("htmx:afterSwap", event => {
  if (event.detail.target === simularSpots) {
    simularSpots.classList.remove("hidden");

    let detailSpots = [];

    let similarSpotsItems = document.getElementById("similar-spots");
    if (similarSpotsItems) {
      Array.from(similarSpotsItems.children).forEach(spot => {
        const dataset = spot.querySelector("input").dataset;
        let location = { lon: dataset.lon, lat: dataset.lat };
        detailSpots.push({ name: dataset.name, location: location });
      });
      const eventShowedSimilarSpots = new CustomEvent("showedSimilarSpots", {
        detail: { detailSpots: detailSpots },
      });
      window.dispatchEvent(eventShowedSimilarSpots);
    }
  }
});

function createExpanceBlock(option, option_name, dayOrder) {
  let icon =
    option.dataset.type == "meal_place" ? "restaurant" : "directions_bus";
  let title = option.dataset.name;
  let avgPrice = option.dataset.cost;

  startDateSession.setDate(startDateSession.getDate() + (dayOrder - 1));
  const options = { day: "numeric", month: "long" };
  const readable_date = startDateSession.toLocaleDateString("ru-RU", options);

  const newExpanceBlock = document.createElement("div");
  newExpanceBlock.classList.add("flex", "gap-3");
  newExpanceBlock.dataset.inputName = option_name;
  newExpanceBlock.innerHTML = `
  <div class="bg-gray-200 rounded-3xl size-10 flex justify-center items-center text-gray-600">
  <i class="material-symbols-outlined">${icon}</i>
  </div>
  <div class="grow-1 text-gray-700">
  <div class="font-medium">${title}</div>
  <div>${readable_date}</div>
  </div>
  <div>${avgPrice} ₽</div>
  `;
  return newExpanceBlock;
}

function addOrUpdateExpanceBlock(option, dayOrder) {
  let option_name = option.name;
  const existExpanceBlock = document.querySelector(
    `div[data-input-name="${option_name}"]`,
  );
  const newExpanceBlock = createExpanceBlock(option, option_name, dayOrder);
  if (existExpanceBlock) {
    existExpanceBlock.replaceWith(newExpanceBlock);
  } else {
    expancesBlock.insertAdjacentElement("beforeend", newExpanceBlock);
  }
}

function initBudgetBlock() {
  const options = document.querySelectorAll(
    'input[type="radio"][data-cost]:checked',
  );
  let total = 0;
  expancesBlock.innerHTML = "";
  options.forEach(option => {
    const cost = parseFloat(option.dataset.cost);
    total += isNaN(cost) ? 0 : cost;
    let dayOrder = null;
    if (option.closest(".day-block")) {
      dayOrder = option.closest(".day-block").dataset.dayOrder;
    } else {
      dayOrder = diffInDays(new Date(option.dataset.datetime)) + 1;
    }
    addOrUpdateExpanceBlock(option, dayOrder);
  });
  budgetAmount.textContent = total;
}

function updateBudgetCount() {
  const options = document.querySelectorAll(
    'input[type="radio"][data-cost]:checked',
  );
  let total = 0;
  options.forEach(option => {
    const cost = parseFloat(option.dataset.cost);
    total += isNaN(cost) ? 0 : cost;
  });
  budgetAmount.textContent = total;
}

function updateBudgetBlock(input, dayOrder) {
  updateBudgetCount();
  addOrUpdateExpanceBlock(input, dayOrder);
}
function checkDefaultMealPlacesInput() {
  document.querySelectorAll("input[data-type='meal_place']").forEach(option => {
    option.checked = true;
  });
}
checkDefaultMealPlacesInput();
initBudgetBlock();
