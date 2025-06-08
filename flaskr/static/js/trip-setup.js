

// // static/js/trip-setup.js
// import { renderStep1 }   from './render.js';
// import { createSession } from './session-api.js';

// (async function(){
//   const params  = new URLSearchParams(location.search);
//   const routeId = params.get('routeId');
//   if (!routeId) {
//     alert('Не указан маршрут (routeId) в URL');
//     return;
//   }

//   // 1) Загружаем шаблон маршрута
//   const res = await fetch(`/api/plan/${routeId}`);
//   if (!res.ok) {
//     document.getElementById('app').innerHTML =
//       `<div class="error">Не удалось загрузить маршрут: ${res.status}</div>`;
//     return;
//   }
//   const itinerary = await res.json();

//   // 2) Рендерим POI-варианты
//   document.getElementById('tourTitle').textContent = itinerary.title;
//   renderStep1(itinerary);

//   // 3) Дата по умолчанию + включаем кнопку при первом ready
//   const dateInput = document.getElementById('startDate');
//   dateInput.value = new Date().toISOString().slice(0,10);
//   document.getElementById('goToItinerary').disabled = false;

//   // 4) При клике создаём сессию и переходим
//   document.getElementById('goToItinerary').onclick = async () => {
//     const checkIn = dateInput.value;
//     if (!checkIn) {
//       alert('Выберите дату начала поездки');
//       return;
//     }

//     // Собираем выбранные варианты POI
//     const choices = Array.from(
//       document.querySelectorAll('input[name^="day"]:checked')
//     ).map(i => i.value);

//     const payload = {
//       routeId,
//       departure: itinerary.departure,
//       checkIn,
//       checkOut: new Date(Date.parse(checkIn) + itinerary.duration_days*864e5)
//                   .toISOString().slice(0,10),
//       choices
//     };

//     try {
//       const sessionId = await createSession(payload);
//       window.location.href = `trip-itinerary.html?sessionId=${sessionId}`;
//     } catch (e) {
//       alert('Не удалось создать сессию: ' + e.message);
//     }
//   };
// })();


// let selectedTransportThereIndex = 0;
// let selectedTransportBackIndex = 0;
// let selectedMealOptionIndex = {}; // ключ: `${day}_${type}`, значение: индекс
// let selectedLodgingIndex = {};
// const costCard = document.createElement("div");
// costCard.className = "card";
// //let currentStep = 1;

// const step1El = document.getElementById("step1");
// const step2El = document.getElementById("step2");
// function showStep(n) {
//   step1El.style.display = n === 1 ? "" : "none";
//   step2El.style.display = n === 2 ? "" : "none";
// }

// async function loadPlan() {
//   try {
//     const sessionId = new URLSearchParams(window.location.search).get("sessionId");
//     if (!sessionId) {
//       throw new Error("Отсутствует идентификатор сессии (sessionId) в URL");
//     }

//     const res = await fetch(`http://127.0.0.1:3000/api/session/${sessionId}/plan`);
//     if (!res.ok) {
//       throw new Error(`Ошибка сервера: ${res.status}`);
//     }

//     return await res.json();
//   } catch (e) {
//     return { error: e.message };
//   }
// }
// function computeMinCost(itinerary) {
//   const tThere = Math.min(
//     ...itinerary.transport.options.map((o) => o.there.cost_rub),
//   );
//   const tBack = Math.min(
//     ...itinerary.transport.options.map((o) => o.back.cost_rub),
//   );

//   // Самый дешёвый вариант КАЖДОГО дня
//   const daily = itinerary.day_variants.reduce((sum, d) => {
//     const cheapest = Math.min(...d.variants.map((v) => v.est_budget));
//     return sum + cheapest;
//   }, 0);

//   return tThere + tBack + daily; // еду и жильё считаем в est_budget вариантов
// }

// function renderStep1(itinerary) {
//   // 1) Список POI-маршрутов (можно просто title или первые 3 POI)
//   /* --- Замените свою forEach в renderStep1 на этот код --- */
//   const container = document.getElementById("poiList");
//   container.innerHTML = "";

//   /* карточка-заголовок тура */
//   container.insertAdjacentHTML(
//     "beforebegin",
//     `<div class="card"><div class="card-header">${itinerary.title}</div></div>`,
//   );

//   /* карточка «Варианты маршрутов» */
//   container.insertAdjacentHTML(
//     "beforebegin",
//     `<div class="card"><div class="card-header">Варианты маршрутов (POI)</div></div>`,
//   );

//   itinerary.day_variants.forEach((day) => {
//     container.insertAdjacentHTML(
//       "beforeend",
//       `<div class="section-title">День ${day.day}</div>`,
//     );

//     day.variants.forEach((v, idx) => {
//       const pois = v.segments
//         .filter((s) => s.poi)
//         .slice(0, 3)
//         .map((s) => s.poi.name)
//         .join(" → ");

//       const card = `
//         <div class="route-card">
//           <div class="marker">${day.day}.${idx + 1}</div>
//           <div style="flex:1">
//             <label class="route-radio">
//               <input type="radio" name="day${day.day}" value="${v.variant_id}" ${idx === 0 ? "checked" : ""}>
//               <span class="route-title">${v.name}</span>
//             </label>
//             <div class="route-pois">${pois}${v.segments.length > 3 ? " …" : ""}</div>
//           </div>
//           <span class="cost-pill">от ${v.est_budget} ₽</span>
//         </div>`;
//       container.insertAdjacentHTML("beforeend", card);
//     });
//   });

//   /* активируем голос-кнопку, когда выбран хотя бы один вариант в каждом дне */
//   function checkReady() {
//     const ready = itinerary.day_variants.every((d) =>
//       document.querySelector(`input[name="day${d.day}"]:checked`),
//     );
//     document.getElementById("castVotePOI").disabled = !ready;
//   }
//   container.addEventListener("change", checkReady);

//   // 2) Минимальная стоимость
//   const mc = computeMinCost(itinerary);
//   document.getElementById("minCost").textContent =
//     `Минимальная стоимость: от ${mc} ₽`;

//   // 3) Панель голосования (за POI-маршрут)
//   const voteSec = document.getElementById("voteSection");
//   voteSec.innerHTML = `
//     <button id="castVotePOI" style="margin:12px;">Голосовать за POI-маршрут</button>
//     <div id="voteMsgPOI" class="small"></div>`;
//   checkReady();
//   document.getElementById("castVotePOI").onclick = async () => {
//     const choice = itinerary.day_variants.map(
//       (d) => document.querySelector(`input[name="day${d.day}"]:checked`).value,
//     );

//     const msg = document.getElementById("voteMsgPOI");
//     try {
//       await fetch(`/api/session/${itinerary.session_id}/vote`, {
//         method: "POST",
//         headers: { "Content-Type": "application/json" },
//         body: JSON.stringify({ choice }), // <-- [{day1Var},{day2Var}…]
//       });
//       msg.style.color = "green";
//       msg.textContent = "Спасибо, ваш выбор учтён!";
//     } catch (e) {
//       msg.style.color = "red";
//       msg.textContent = "Ошибка: " + e.message;
//     }
//   };
// }

// function attachExtraButtonHandlers() {
//   const btnExport = document.getElementById("btnExport");
//   const btnInvite = document.getElementById("btnInvite");
//   if (!btnExport || !btnInvite) return;

//   /* ---------- Экспорт ---------- */
//   btnExport.onclick = () => {
//     showModal(
//       `
//       <h3>Экспорт маршрута</h3>
//       <label>Формат:</label>
//       <select id="expFmt">
//         <option value="pdf">PDF</option>
//         <option value="ics">iCalendar (ICS)</option>
//       </select>
//       <footer>
//         <button id="expOk">Скачать</button>
//         <button id="expCancel">Отмена</button>
//       </footer>`,
//       (m) => {
//         m.querySelector("#expCancel").onclick = () => m.parentElement.remove();
//         m.querySelector("#expOk").onclick = () => {
//           const fmt = m.querySelector("#expFmt").value;
//           window.open(
//             `/api/session/${window.itinerary.session_id}/export?format=${fmt}`,
//             "_blank",
//           );
//           m.parentElement.remove();
//         };
//       },
//     );
//   };

//   /* ---------- Пригласить друзей ---------- */
//   btnInvite.onclick = () => {
//     // 1) Создаём токен приглашения
//     const token = Math.random().toString(36).slice(2);
//     // 2) Сохраняем в LocalStorage маппинг token→session_id
//     const invites = JSON.parse(localStorage.getItem("invites") || "{}");
//     invites[token] = window.itinerary.session_id;
//     localStorage.setItem("invites", JSON.stringify(invites));
//     // 3) Делаем ссылку
//     const link = `${location.origin}/web/join.html?token=${token}`;
//     // 4) Показываем модалку
//     showModal(
//       `
//       <h3>Пригласить друзей</h3>
//       <p>Поделитесь этой ссылкой, чтобы участники могли выбрать свой вариант и задать никнейм:</p>
//       <input id="inviteLink" readonly value="${link}" style="width:100%;margin-bottom:12px;">
//       <footer>
//         <button id="copyLink">Копировать</button>
//         <button id="closeInvite">Закрыть</button>
//       </footer>`,
//       (m) => {
//         m.querySelector("#copyLink").onclick = () => {
//           const input = m.querySelector("#inviteLink");
//           input.select();
//           input.setSelectionRange(0, 99999);
//           document.execCommand("copy");
//         };
//         m.querySelector("#closeInvite").onclick = () =>
//           m.parentElement.remove();
//       },
//     );
//   };
// }

// function renderItinerary(itinerary) {
//   // 1. Собираем выбранные variant_id
//   const chosenIds = itinerary.day_variants.map(
//     (d) => document.querySelector(`input[name="day${d.day}"]:checked`).value,
//   );
//   const extraButtons = document.getElementById("extraButtons"); // сохраняем кнопку

//   const app = document.getElementById("step2");
//   app.innerHTML = ""; // очищаем всё внутри step2
//   app.appendChild(extraButtons); // сразу вернуть кнопки на место
//   const header = document.createElement("div");
//   header.className = "card";
//   header.innerHTML = `<div class="card-header">${itinerary.title}</div>`;
//   app.appendChild(header);

//   const routeFlat = itinerary.day_variants.map((d) => {
//     const v = d.variants.find((v) => v.variant_id === chosenIds[d.day - 1]);
//     return { ...v, day: d.day }; // ←  теперь внутри есть поле day
//   });

//   const transportCard = document.createElement("div");
//   transportCard.className = "card";
//   renderTransportOptions(itinerary, transportCard);
//   app.appendChild(transportCard);

//   const weatherCard = document.createElement("div");
//   weatherCard.className = "card";
//   weatherCard.innerHTML = `
//     <div class="card-header">Погодные условия</div>
//     <div class="list-item">
//       <label>
//         <input type="radio" name="weather" value="good" checked> С прогулками (хорошая погода)
//       </label><br>
//       <label>
//         <input type="radio" name="weather" value="bad"> Без прогулок (плохая погода)
//       </label>
//     </div>
//   `;

//   weatherCard.querySelectorAll('input[name="weather"]').forEach((input) => {
//     input.addEventListener("change", (e) => {
//       goodWeather = e.target.value === "good";
//       renderRoute(itinerary, routeContainer);
//     });
//   });

//   app.appendChild(weatherCard);

//   const routeContainer = document.createElement("div");
//   app.appendChild(routeContainer);
//   let goodWeather = true;

//   function renderRoute() {
//     routeContainer.innerHTML = "";
//     const selectedTransportThere =
//       itinerary.transport.options[selectedTransportThereIndex];
//     const baseArrivalHour =
//       9 + Math.floor(selectedTransportThere.there.time_min / 60);
//     let currentHour = baseArrivalHour;

//     routeFlat.forEach((day) => {
//       const dayCard = document.createElement("div");
//       dayCard.className = "card";
//       dayCard.innerHTML = `<div class="card-header">День ${day.day}</div>`;

//       if (Array.isArray(day.segments)) {
//         day.segments.forEach((seg) => {
//           // Пропускаем уличные сегменты при плохой погоде
//           if (!goodWeather && seg.poi?.weather_constraints) return;

//           const segmentBlock = document.createElement("div");
//           segmentBlock.className = "list-item";
//           if (seg.poi) {
//             segmentBlock.innerHTML = `<strong>${seg.poi.name}</strong>
//               ${seg.poi.must_see ? '<span class="badge">Must-see</span>' : ""}
//               <div class="small">Время: ${day.day === 1 ? `${currentHour}:00–${currentHour + 2}:00` : seg.arrival_window || "–"}</div>
//               ${seg.rating ? `<div class='small'>Рейтинг: ${seg.rating} ⭐</div>` : ""}
//               ${
//                 seg.opening_hours
//                   ? `<div class='small'>Часы работы: ${Object.entries(
//                       seg.opening_hours,
//                     )
//                       .map(([k, v]) => k + ": " + v)
//                       .join("; ")}</div>`
//                   : ""
//               }
//               ${seg.tickets ? `<div class='small'>Билеты: ${seg.tickets.map((t) => t.type + ": " + t.price_rub + "₽").join(", ")}</div>` : ""}
//               ${seg.poi.weather_constraints ? `<div class='small'>Ограничения по погоде: осадки до ${seg.poi.weather_constraints.max_precip_mm} мм, ветер до ${seg.poi.weather_constraints.max_wind_m_s} м/с</div>` : ""}
//               ${seg.reviews ? `<div class='small'>Отзывы: ${seg.reviews.map((r) => `${r.author}: “${r.text}”`).join("; ")}</div>` : ""}`;
//             if (day.day === 1) currentHour += 2;
//           }

//           if (seg.meal) {
//             const key = `${day.day}_${seg.meal.type}`;
//             const selected = selectedMealOptionIndex[key];
//             const mealHTML = seg.meal.options
//               .map(
//                 (opt, idx) => `
//               <label>
//                 <input type="radio" name="meal_${key}" value="${idx}" ${selected === idx ? "checked" : ""}>
//                 <span>${opt.name} — ${opt.avg_check_rub}₽</span>
//               </label>
//             `,
//               )
//               .join("<br>");

//             segmentBlock.innerHTML = `<strong>${seg.meal.type === "lunch" ? "Обед" : "Ужин"}</strong><br>
//               <div class='small'>Время: ${day.day === 1 ? `${currentHour}:00–${currentHour + 1}:00` : seg.time_window || "–"}</div>
//               ${mealHTML}`;

//             segmentBlock
//               .querySelectorAll(`input[name="meal_${key}"]`)
//               .forEach((input) => {
//                 input.addEventListener("change", () => {
//                   selectedMealOptionIndex[key] = Number(input.value);
//                   renderSummaryBlock();
//                 });
//               });

//             if (day.day === 1) currentHour += 1;
//           }

//           if (seg.transport_segment) {
//             segmentBlock.innerHTML += `<strong>Транспорт: ${seg.transport_segment.from} → ${seg.transport_segment.to}</strong><br>
//               ${seg.transport_segment.options.map((opt) => `${opt.mode}: ${opt.time_min} мин, ${opt.cost_rub}₽`).join("<br>")}`;
//           }

//           if (seg.transport_back) {
//             segmentBlock.innerHTML += `<strong>Возвращение:</strong> ${seg.transport_back}`;
//           }

//           dayCard.appendChild(segmentBlock);
//         });
//       }

//       if (day.lodging_options) {
//         const lodgeTitle = document.createElement("div");
//         lodgeTitle.className = "section-title";
//         lodgeTitle.textContent = "Варианты ночёвки";
//         dayCard.appendChild(lodgeTitle);

//         const lodgeList = document.createElement("ul");
//         lodgeList.className = "list";
//         day.lodging_options.forEach((opt, idx) => {
//           const li = document.createElement("li");
//           li.className = "list-item";
//           const isSelected = selectedLodgingIndex[day.day] === idx;
//           li.innerHTML = `<label>
//             <input type="radio" name="lodging_day_${day.day}" value="${idx}" ${isSelected ? "checked" : ""}>
//             <span>${opt.name} (${opt.type}) — ${opt.avg_price_rub_per_night}₽</span
//           </label>`;
//           li.querySelector("input").addEventListener("change", () => {
//             selectedLodgingIndex[day.day] = idx;
//             renderSummaryBlock();
//           });
//           lodgeList.appendChild(li);
//         });
//         dayCard.appendChild(lodgeList);
//       }

//       routeContainer.appendChild(dayCard);
//     });
//   }

//   function renderTransportOptions(itinerary, container) {
//     container.innerHTML = `<div class="card-header">Выбор транспорта</div>`;

//     ["there", "back"].forEach((dir) => {
//       const title = document.createElement("div");
//       title.className = "section-title";
//       title.textContent = dir === "there" ? "Туда:" : "Обратно:";
//       container.appendChild(title);

//       itinerary.transport.options.forEach((opt, idx) => {
//         const div = document.createElement("div");
//         div.className = "list-item transport-option";
// //        const option = dir === "there" ? opt.there : opt.back;
//         div.innerHTML = `<label>
//           <input type="radio" name="transport_${dir}" value="${idx}" ${idx === (dir === "there" ? selectedTransportThereIndex : selectedTransportBackIndex) ? "checked" : ""}>
//           <span>${opt.mode}: ${opt.there.from} → ${opt.there.to} (~${opt.there.time_min} мин, ${opt.there.cost_rub}₽)</span>
//         </label>`;
//         div.querySelector("input").addEventListener("change", () => {
//           if (dir === "there") selectedTransportThereIndex = idx;
//           else selectedTransportBackIndex = idx;
//           renderRoute();
//           renderSummaryBlock();
//         });
//         container.appendChild(div);
//       });
//     });
//   }

//   function renderSummaryBlock() {
//     const t1 = itinerary.transport.options[selectedTransportThereIndex].there;
//     const t2 = itinerary.transport.options[selectedTransportBackIndex].back;
//     let total = t1.cost_rub + t2.cost_rub;

//     routeFlat.forEach((day) => {
//       const idx = selectedLodgingIndex[day.day];
//       if (day.lodging_options?.[idx])
//         total += day.lodging_options[idx].avg_price_rub_per_night;
//     });

//     // добавляем стоимость выбранных блюд
//     routeFlat.forEach((day) => {
//       if (!Array.isArray(day.segments)) return;
//       day.segments.forEach((seg) => {
//         if (seg.meal) {
//           const key = `${day.day}_${seg.meal.type}`;
//           const idx = selectedMealOptionIndex[key];
//           if (typeof idx === "number") {
//             total += seg.meal.options[idx].avg_check_rub;
//           }
//         }
//       });
//     });

//     const selectedTransportThere =
//       itinerary.transport.options[selectedTransportThereIndex];
//     const selectedTransportBack =
//       itinerary.transport.options[selectedTransportBackIndex];

//     const lodgingSummaries = Object.entries(selectedLodgingIndex)
//       .map(([day, idx]) => {
//         const dayObj = routeFlat.find((v) => v.day == day);
//         const opt = dayObj?.lodging_options?.[idx];
//         return opt ? `День ${day}: ${opt.name}` : null;
//       })
//       .filter(Boolean)
//       .join("<br>");

//     costCard.innerHTML = `
//       <div class="card-header">Вы выбрали</div>
//       <div class="list-item">
//         Транспорт туда: ${selectedTransportThere.mode}<br>
//         Транспорт обратно: ${selectedTransportBack.mode}<br>
//         ${lodgingSummaries ? `Ночёвки:<br>${lodgingSummaries}<br>` : ""}
//       </div>
//       <div class="card-header">Бюджет поездки</div>
//       <div class="list-item">
//         Ориентировочная стоимость: <strong>${total}₽</strong>
//       </div>`;
//   }

//   renderRoute();
//   renderSummaryBlock();
//   app.appendChild(costCard);
//   document.getElementById("extraButtons").innerHTML = `
//     <button id="btnExport">Экспорт маршрута</button>
//     <button id="btnInvite" class="btn btn-new">Пригласить друзей</button>`;
//   attachExtraButtonHandlers();
// }
// addEventListener("DOMContentLoaded", async () => {
//   // 1. Получаем routeId из URL
//   const params    = new URLSearchParams(window.location.search);
//   const sessionId = params.get("sessionId");
//   if (!sessionId) {
//     document.getElementById("app").innerHTML =
//       '<div class="error">Не указан sessionId в URL</div>';
//     return;
//   }
//   // 2. Загружаем все маршруты
//   const itinerary = await loadPlan();
//   if (itinerary.error) {
//     document.getElementById("app").innerHTML =
//       `<div class="error">${itinerary.error}</div>`;
//     return;
//   }

//   window.itinerary = itinerary;
//   renderStep1(itinerary);
//   const btnNext = document.getElementById("toDetailsBtn");
//   // 4) Навесить клик → показываем step2 и рисуем детали
//   btnNext.addEventListener("click", () => {
//     showStep(2);
//     renderItinerary(itinerary);
//   });
// });


// function showModal(html, onMount) {
//   const wrap = document.createElement("div");
//   wrap.className = "modal-backdrop";
//   wrap.innerHTML = `<div class="modal">${html}</div>`;
//   document.body.appendChild(wrap);
//   onMount?.(wrap.querySelector(".modal"));
//   wrap.addEventListener("click", (e) => {
//     if (e.target === wrap) wrap.remove(); // клик вне модалки — закрыть
//   });
// }
