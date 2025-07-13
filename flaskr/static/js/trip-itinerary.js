import { alert } from "./main.js";
import { SERVER_ERROR } from "./constants.js";

const body = document.getElementById("body");
const sessionId = body.dataset.sessionId;
const startDateInput = document.getElementById("start-date");

const startDateSession = startDateInput
  ? new Date(startDateInput.value)
  : new Date(body.dataset.startDate);

const sentinelHideExpanses = document.getElementById(
  "sentinel_for_hide_expanses",
);
const sentinelShowExpanses = document.getElementById(
  "sentinel_for_show_expanses",
);
const itineraryLeft = document.getElementById("scroll-block-itinerary");

const budgetBlock = document.getElementById("budget-block");
const budgetAmountBlock = document.getElementById("budget-amount-block");
const budgetAmount = document.getElementById("budgetAmount");
const expancesBlock = document.getElementById("expances-block");
const simularSpots = document.getElementById("similar-spots-block");
const isTransports = document.getElementById("transports_items") != null;

if (isTransports) {
  const showMoreTransportThereBtn = document.getElementById(
    "show-more-transports-there",
  );
  const showMoreTransportBackBtn = document.getElementById(
    "show-more-transports-back",
  );
  function hideButtonIfNoMoreTranports() {
    if (
      document.getElementById("transports-groups-there").children.length == 2
    ) {
      showMoreTransportThereBtn.classList.add("hidden");
    }
    if (
      document.getElementById("transports-groups-back").children.length == 2
    ) {
      showMoreTransportBackBtn.classList.add("hidden");
    }
  }
  hideButtonIfNoMoreTranports();
  showMoreTransportThereBtn.addEventListener("click", () =>
    showMoreTransports("there"),
  );
  showMoreTransportBackBtn.addEventListener("click", () =>
    showMoreTransports("back"),
  );
}
function showMoreTransports(direction) {
  const blockDirection = document.getElementById(
    `transports-groups-${direction}`,
  );
  for (let children of blockDirection.children) {
    const classList = children.classList;
    if (classList.contains("hidden")) {
      classList.remove("hidden");
      break;
      hideButtonIfNoMoreTranports();
    }
  }
}
showMoreTransports("there");
showMoreTransports("back");

function expandeBudgetBlock() {
  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.target === sentinelHideExpanses) {
        if (!entry.isIntersecting) {
          console.log("Hide");
          budgetBlock.classList.add("sticky");
          budgetAmountBlock.classList.remove("mb-3", "mt-2");
          budgetAmountBlock.classList.add("border-t", "mt-6", "shadow");
          expancesBlock.classList.add("hidden");
        }
      }
      if (entry.target === sentinelShowExpanses) {
        if (entry.isIntersecting) {
          console.log("Show");
          budgetBlock.classList.remove("sticky");
          budgetAmountBlock.classList.add("mb-3", "mt-2");
          budgetAmountBlock.classList.remove("border-t", "mt-6", "shadow");
          expancesBlock.classList.remove("hidden");
        }
      }
    });
  });

  observer.observe(sentinelHideExpanses);
  observer.observe(sentinelShowExpanses);
}

expandeBudgetBlock();

function diffInDays(date) {
  const MS_PER_DAY = 1000 * 60 * 60 * 24;
  const utc_start_session_date = Date.UTC(
    startDateSession.getFullYear(),
    startDateSession.getMonth(),
    startDateSession.getDate(),
  );
  const utc_count_date = Date.UTC(
    date.getFullYear(),
    date.getMonth(),
    date.getDate(),
  );
  return Math.floor((utc_count_date - utc_start_session_date) / MS_PER_DAY);
}
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

      updateBudgetBlock(target, dayOrder);
    }
  });
});
document.addEventListener("htmx:afterSwap", () => {
  if (simularSpots.innerHTML.trim()) {
    simularSpots.classList.remove("hidden");
  } else {
    simularSpots.classList.remove("hidden");
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
