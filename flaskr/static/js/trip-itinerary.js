import { alert } from "./main.js";
import { SERVER_ERROR } from "./constants.js";

const body = document.getElementById("body");
const sessionId = body.dataset.sessionId;
const startDateInput = document.getElementById("start-date");

const startDateSession = startDateInput
  ? startDateInput.value
  : new Date(body.dataset.startDate);
console.log(startDateSession);

const sentinelBudget = document.getElementById("sentinel_budget");
const budgetAmountBlock = document.getElementById("budget-amount-block");
const budgetAmount = document.getElementById("budgetAmount");
const expancesBlock = document.getElementById("expances-block");

function expandeBudgetBlock() {
  const observer = new IntersectionObserver(([entry]) => {
    if (entry.isIntersecting) {
      budgetAmountBlock.classList.remove("border-t", "mt-6", "shadow");
      expancesBlock.classList.remove("hidden");
    } else {
      budgetAmountBlock.classList.remove("mb-3");
      budgetAmountBlock.classList.add("border-t", "mt-6", "shadow");
      expancesBlock.classList.add("hidden");
    }
  });
  observer.observe(sentinelBudget);
}
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

document.addEventListener("DOMContentLoaded", () => {
  const options = document.querySelectorAll("input[type='radio'][data-cost]");
  Array.from(options).forEach(option => {
    const dayOrder = option.closest(".day-block").dataset.dayOrder;
    option.addEventListener("click", () => updateBudgetBlock(option, dayOrder));
  });

  const simularSpots = document.getElementById("similar-spots");
  simularSpots.addEventListener("click", event => {
    const target = event.target;
    if (target.matches("input[type='radio'][data-cost]")) {
      const dayOrder = simularSpots.dataset.dayOrder;
      const mealType = simularSpots.dataset.mealType;
      const name_input = `meal_place_${dayOrder}_${mealType}`;
      const input = document.querySelectorAll(`input[name=${name_input}]`)[0];

      updateBudgetBlock(target, dayOrder);
    }
  });
  const buttonsShowSimularMPs =
    document.getElementsByClassName("show-simular-spots");

  Array.from(buttonsShowSimularMPs).forEach(btn => {
    btn.addEventListener("click", showSimularMealPlaces);
  });
});

async function showSimularMealPlaces() {
  const dayOrder = this.dataset.dayOrder;
  const mealType = this.dataset.mealType;
  const dayOrderMealType = `${dayOrder}_${mealType}`;

  const mealPlaceId = this.dataset.mealPlaceId;

  const blockSimilarMealPlaces = document.getElementById(`similar-spots-block`);
  blockSimilarMealPlaces.classList.remove("hidden");
  const resp = await fetch(`/api/meal_place/${mealPlaceId}/get_simulars`, {
    method: "GET",
    headers: { "Content-type": "application/json" },
  });
  if (resp.status == 200) {
    const data = await resp.json();
    const simular_meal_places_result = JSON.parse(
      data.simular_meal_places_result,
    );
    blockSimilarMealPlaces.firstElementChild.innerHTML = `Поесть рядом с ${this.dataset.mealPlaceName}`;

    let food_service_avg_price = "";

    const simularSpots = blockSimilarMealPlaces.lastElementChild;
    simularSpots.innerHTML = "";
    simular_meal_places_result.forEach(spot => {
      for (let index_top in spot.data_json.attribute_groups) {
        for (let index_low in spot.data_json.attribute_groups[index_top]
          .attributes) {
          if (
            spot.data_json.attribute_groups[index_top].attributes[index_low]
              .tag == "food_service_avg_price"
          ) {
            food_service_avg_price =
              spot.data_json.attribute_groups[index_top].attributes[index_low]
                .name;
            break;
          }
        }
      }

      let nameMealPlace = `meal_place_${dayOrderMealType}`;
      let avg_price = food_service_avg_price.match(/\d+/)?.[0];
      let address_name = spot.data_json.address_name;
      let img_src = spot.data_json.external_content[0]?.main_photo_url;

      simularSpots.dataset.dayOrder = dayOrder;
      simularSpots.dataset.mealType = mealType;
      simularSpots.innerHTML += `
      <label>
        <input class="peer hidden"
                name="${nameMealPlace}"
                type="radio"
                data-type="meal_place"
                data-cost="${avg_price}"
                data-name="${spot.data_json.name}"
                data-general-rating="${spot.data_json.reviews.general_rating}"
                data-general-review-count="${spot.data_json.reviews.general_review_count}"
                data-img-src="${img_src}"
                data-address-name="${address_name}">
        <div class="item flex w-full h-30 bg-gray-100 gap-4 rounded-xl peer-checked:ring-inset peer-checked:ring-2 peer-checked:ring-blue-500">
          <div class="flex flex-col gap-3 grow-1 p-3">
            <div class="header">${spot.data_json.name}</div>
            <div class="text-gray-600 flex flex-col gap-1 text-sm">
              <div class="attributes flex gap-2">
                <div class="flex">
                  <i class="material-icons-round">star</i>
                  ${spot.data_json.reviews.general_rating}
                </div>
                ${spot.data_json.reviews.general_review_count} отзывов ${food_service_avg_price}
              </div>
              <div class="second-line">${address_name}</div>
            </div>
          </div>
          <img class="w-40 rounded-xl object-cover" src="${img_src}">
        </div>
      </label>
      `;
    });
  } else {
    alert(resp.status);
  }
}

function createExpanceBlock(option, option_name, dayOrder) {
  let icon =
    option.dataset.type == "meal_place" ? "restaurant" : "directions_bus";
  let title = option.dataset.name;
  let avgPrice = option.dataset.cost;

  let date = new Date(startDateSession);
  date.setDate(date.getDate() + (dayOrder - 1));
  const options = { day: "numeric", month: "long" };
  const readable_date = date.toLocaleDateString("ru-RU", options);

  const newExpanceBlock = document.createElement("div");
  newExpanceBlock.classList.add("flex", "gap-3");
  newExpanceBlock.dataset.inputName = option_name;
  newExpanceBlock.innerHTML = `
  <div class="bg-gray-200 rounded-3xl size-10 flex justify-center items-center">
  <i class="material-icons-round">${icon}</i>
  </div>
  <div class="grow-1 text-gray-700">
  <div class="font-medium">${title}</div>
  <div>${readable_date}</div>
  </div>
  <div>${avgPrice}</div>
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
    const dayOrder = option.closest("[data-day-order]").dataset.dayOrder;
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
