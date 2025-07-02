export function alert(message, color) {
  const alertPlaceholder = document.getElementById("alert-placeholder");
  const wrapper = document.createElement("div");
  wrapper.innerHTML = [
    `<div class="bg-${color}-200  flex items-start justify-between gap-4 text-${color}-900 px-4 py-3 rounded-lg shadow-xl w-full max-w-xl">`,
    `   <div class="leading-snug">${message}</div>`,
    `   <div type="button" class="text-${color}-800 hover:text-${color}-600 transition-colors rounded focus:outline-none cursor-pointer" onclick="this.parentElement.remove()" aria-label="Close"><i class="material-icons-round">close</i></div>`,
    "</div>",
  ].join("");

  alertPlaceholder.append(wrapper);
}
