
const btnVoteAndToIniterary = document.getElementById('vote-and-to-itinerary');
const sessionId = btnVoteAndToIniterary.dataset.sessionId;
const participantNameModal = document.getElementById("enter-name-modal");
if(participantNameModal) {
    btnVoteAndToIniterary.setAttribute("disabled", true);
    const participantNameInput = document.querySelector("input[id='participant-name']");
    const errorMsg = document.getElementById("error-msg-name-modal")
    const btnSaveParticipantName = document.getElementById('btn-save-participant-name');
    btnSaveParticipantName.onclick = async () => {
      if (!participantNameInput.value) {
        errorMsg.textContent = "Поле обязательно для заполнения"
        errorMsg.classList.remove("hidden");
        return;
      }
      participantNameModal.style["display"] = "none";
      const resp = await fetch(`/api/session/add_user_name`, {
        method:"POST",
        headers:{"Content-Type": "application/json"},
        body: JSON.stringify({"user_name": participantNameInput.value, "session_id": sessionId})
      })
      btnVoteAndToIniterary.removeAttribute("disabled");
    }
}

const btnCreateInvite = document.getElementById("create-invite");
const blockInviteLink = document.getElementById("block-invite-link");
const inviteLinkText = document.getElementById("invite-link-text");
btnCreateInvite.addEventListener("click", async() => {
  const sessionUuid = btnCreateInvite.dataset.sessionUuid;
  const resp = await fetch(`/api/session/${sessionUuid}/create_invite`, {
    method: "POST",
    headers: {"Content-Type": "application/json"}
  })
  if (resp.status != 200) {    
      alert("Ошибка на сервере, попробуйте позже.", "red");
      return;
  }
  const data = await resp.json()
  blockInviteLink.classList.remove("hidden")
  inviteLinkText.innerHTML = data.link
});
if (document.getElementById("is-completed-vote")) {
  btnVoteAndToIniterary.textContent = "Перейти к маршруту"
  btnVoteAndToIniterary.onclick = async() => {
    window.location = `/trip-itinerary?sessionId=${sessionId}`;
  }
}
else {
  btnVoteAndToIniterary.addEventListener('click', async () => {
    const startDateInput = document.getElementById('start-date');
    inputs_with_variants = document.querySelectorAll("input[name^='day']:checked")
    const choices = [];
    for (let d = 0; d < inputs_with_variants.length; d++) {
      variant_id = inputs_with_variants[d].value;
      dayNumber = inputs_with_variants[d].dataset.dayNumber;

      choices.push({[variant_id]: dayNumber});
    }
    const checkIn = new Date(startDateInput.value);
    const checkOut = new Date(checkIn.getDate()+'{{ plan.day_variants|length }}');

    const resp = await fetch(`/api/session/vote`, {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({"choices":choices, "session_id": sessionId})
    });
    if (resp.status == 200) {
      location.reload();
    }
    else {
        alert(SERVER_ERROR.message, SERVER_ERROR.color);
    }
  });
}
