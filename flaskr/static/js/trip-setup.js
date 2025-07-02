import { alert } from "./main.js";
import {
  SERVER_ERROR,
  VOTING_FINISHED,
  TRIP_SESSION_IS_FULLED,
  API_URI_ADD_NAME,
} from "./constants.js";

const main = document.getElementById("main");
const sessionUuid = main.dataset.sessionUuid;

const btnVoteAndToIniterary = document.getElementById("vote-and-to-itinerary");
const participantNameModal = document.getElementById("enter-name-modal");

const btnCreateInvite = document.getElementById("create-invite");
const blockInviteLink = document.getElementById("block-invite-link");
const inviteLinkText = document.getElementById("invite-link-text");
const errorMsg = document.getElementById("error-msg-name-modal");
const isVotingCompleted = main.dataset.isVotingCompleted == "True";

const btnSaveParticipantName = document.getElementById(
  "btn-save-participant-name",
);
const participantNameInput = document.getElementById("participant-name");

function changeBtnToGoItinerary() {
  btnVoteAndToIniterary.textContent = "Перейти к маршруту";
  btnVoteAndToIniterary.addEventListener("click", goToItinerary);
}
function goToItinerary() {
  window.location.assign(`/trip-itinerary?session_uuid=${sessionUuid}`);
}

async function fetchAddUserName(name) {
  return await fetch(API_URI_ADD_NAME, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_name: name }),
  });
}

async function addUserName() {
  if (!participantNameInput.value) {
    errorMsg.textContent = "Поле обязательно для заполнения";
    errorMsg.classList.remove("hidden");
    return;
  }
  participantNameModal.style["display"] = "none";
  btnVoteAndToIniterary.removeAttribute("disabled");
  return await fetchAddUserName(participantNameInput.value);
}

async function showEnterNameModalIfNotExist() {
  btnVoteAndToIniterary.setAttribute("disabled", true);
  btnSaveParticipantName.addEventListener("click", addUserName);
}
async function createInvite() {
  fetch(`/api/session/${sessionUuid}/create_invite`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  }).then(async resp => {
    if (resp.status == 422) {
      alert(TRIP_SESSION_IS_FULLED.message, TRIP_SESSION_IS_FULLED.color);
    } else if (resp.status != 200) {
      alert(SERVER_ERROR.message, SERVER_ERROR.color);
      return;
    }
    const data = await resp.json();
    const cliping = await navigator.clipboard.writeText(data.link);
    blockInviteLink.classList.remove("hidden");
    inviteLinkText.innerHTML = data.link;
    alert("Ссылка скопирована", "neutral");
  });
}
function assembleChoices() {
  const inputs_with_variants = document.querySelectorAll(
    "input[name^='day']:checked",
  );
  const choices = [];
  for (let d = 0; d < inputs_with_variants.length; d++) {
    let variant_id = inputs_with_variants[d].value;
    let dayNumber = inputs_with_variants[d].dataset.dayNumber;

    choices.push({ [variant_id]: dayNumber });
  }
  return choices;
}
async function fetchVote(choices) {
  return await fetch(`/api/session/vote`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ choices: choices, session_uuid: sessionUuid }),
  });
}

async function sendVote() {
  const choices = assembleChoices();
  const resp = await fetchVote(choices);
  switch (resp.status) {
    case 200:
      location.reload();
      break;

    case 422:
      alert(VOTING_FINISHED.message, VOTING_FINISHED.color);
      break;

    default:
      alert(SERVER_ERROR.message, SERVER_ERROR.color);
      break;
  }
}

if (participantNameModal) {
  showEnterNameModalIfNotExist();
}

btnCreateInvite.addEventListener("click", createInvite);
const isSingleTraveler = main.dataset.countOtherParticipants == 0;
const voteHandler = async () => {
  if (isSingleTraveler || !isVotingCompleted) {
    await sendVote();
  }
  if (isSingleTraveler) {
    goToItinerary();
  }
};
btnVoteAndToIniterary.addEventListener("click", voteHandler);

if (!isSingleTraveler && isVotingCompleted) {
  btnVoteAndToIniterary.removeEventListener("click", voteHandler);
  changeBtnToGoItinerary();
}
