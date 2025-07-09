import { alert } from "./main.js";
import { SERVER_ERROR } from "./constants.js";

const sessionId =
  document.getElementsByClassName("itinerary-left")[0].dataset.sessionId;
const startDateInput = document.getElementById("start-date");

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
  const buttonsShowSimularMPs =
    document.getElementsByClassName("show-simular-spots");

  Array.from(buttonsShowSimularMPs).forEach(btn => {
    btn.addEventListener("click", showSimularMealPlaces);
  });
});
async function showSimularMealPlaces() {
  const mealPlaceId = this.dataset.mealPlaceId;
  const dayOrderMealType = this.dataset.dayOrderMealType;
  const blockSimularMealPlaces = document.getElementById(`simular_spots`);
  blockSimularMealPlaces.classList.remove("hidden");
  const resp = await fetch(`/api/meal_place/${mealPlaceId}/get_simulars`, {
    method: "GET",
    headers: { "Content-type": "application/json" },
  });
  if (resp.status == 200) {
    const data = await resp.json();
    const simular_meal_places_result = JSON.parse(
      data.simular_meal_places_result,
    );
    blockSimularMealPlaces.firstElementChild.innerHTML = `Поесть рядом с ${this.dataset.mealPlaceName}`;

    let food_service_avg_price = "";
    simular_meal_places_result.forEach(spots => {
      for (let index_top in spots.data_json.attribute_groups) {
        for (let index_low in spots.data_json.attribute_groups[index_top]
          .attributes) {
          if (
            spots.data_json.attribute_groups[index_top].attributes[index_low]
              .tag == "food_service_avg_price"
          ) {
            food_service_avg_price =
              spots.data_json.attribute_groups[index_top].attributes[index_low]
                .name;
            break;
          }
        }
      }
      blockSimularMealPlaces.lastElementChild.innerHTML += `
                  <div class="item flex w-full h-30 bg-gray-100 p-3 gap-4 rounded-xl">
                    <div class="flex flex-col gap-3 grow-1">
                        <div class="header">${spots.data_json.name}</div>
                        <div class="text-gray-600 flex flex-col gap-1  text-sm">
                            <div class="attributes flex gap-2">
                                <div class="flex ">
                                    <i class="material-icons-round">star</i>
                                    ${spots.data_json.reviews.general_rating}
                                </div>
                                ${spots.data_json.reviews.general_review_count} отзывов ${food_service_avg_price}
                            </div>
                            <div class="second-line">${spots.data_json.address_name}</div>
                        </div>
                    </div>
                    <img class="w-40 rounded-xl object-cover" src="${spots.data_json.external_content[0]?.main_photo_url}">
                  </div>
            `;
    });
  } else {
    alert(resp.status);
  }
}

function updateBudget() {
  const items = document.querySelectorAll(
    'input[type="radio"][data-cost]:checked',
  );
  let total = 0;
  items.forEach(item => {
    const cost = parseFloat(item.dataset.cost);
    total += isNaN(cost) ? 0 : cost;
  });
  document.getElementById("budgetAmount").textContent = total;
}
