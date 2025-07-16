const departureCity = document.getElementById("departureCity");
const promptChooseCity = document.getElementById("prompt-choose-city");
const btnChooseCity = document.getElementById("choose-city");
const btnPromptHide = document.getElementById("prompt-hide");
const citiesModal = document.getElementsByClassName("cities-modal")[0];

function showCitiesChoose() {
  citiesModal.classList.remove("hidden");
}

function showPromptChooseCity() {
  promptChooseCity.classList.remove("hidden");
}

function hidePromptChooseCity() {
  promptChooseCity.classList.add("hidden");
}

function setChooseCityFuncForChooseItems() {
  Array.from(citiesModal.children).forEach(element => {
    element.onclick = async () => {
      const citySlug = element.dataset.citySlug;
      window.location.assign(`/city/${citySlug}/routes`);
    };
  });
}
export function handleDepartureCity() {
  btnPromptHide.addEventListener("click", hidePromptChooseCity);
  btnChooseCity.addEventListener("click", () => {
    hidePromptChooseCity();
    showCitiesChoose();
  });

  departureCity.addEventListener("click", showCitiesChoose);

  if (!localStorage.getItem("visited")) {
    showPromptChooseCity();
    localStorage.setItem("visited", 1);
  }
  setChooseCityFuncForChooseItems();
}
