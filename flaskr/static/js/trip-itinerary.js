const sessionId = document.getElementsByClassName("itinerary-left")[0].dataset.sessionId
const startDateInput = document.getElementById("start-date")
const startDateValue = startDateInput.value

startDateInput.addEventListener('change', async () => {
const resp = await fetch('/api/session/update_transports', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({startDateValue, sessionId})
});
console.log(resp.body);
});


function updateBudget() {
const items = document.querySelectorAll('input[type="radio"][data-cost]:checked')
let total = 0;
items.forEach(item => {
    const cost = parseFloat(item.dataset.cost)
    total += isNaN(cost) ? 0 : cost;
})
document.getElementById('budgetAmount').textContent = total;
}
