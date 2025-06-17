// const citiesModal = document.getElementsByClassName("cities-modal")[0]
// document.getElementById("departureCity").addEventListener('click', async() => {
//     citiesModal.style.display = "block";
// });
// const checkedCityName = document.getElementById("cityName")
// Array.from(citiesModal.children).forEach(element => {
//     element.onclick = async () => {
//         const cityId = element.dataset.cityId;
//         if (window.location.href.includes("trip-itinerary")) {
//             const sessionId = document.getElementsByClassName("itinerary-left")[0].dataset.sessionId;
//             await fetch('/api/session/update_departure_city', {
//                 method: "POST",
//                 header: {"Content-Type": "application/json"},
//                 body: JSON.stringify({ cityId, sessionId})
//             });
//         }
//         else {
//             checkedCityName.innerText = element.innerText;
//             checkedCityName.dataset.cityId = cityId;
//         }
//     }; 
// });
