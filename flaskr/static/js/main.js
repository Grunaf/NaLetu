export function alert (message, color) {
    const alertPlaceholder = document.getElementById('alert-placeholder')
    const wrapper = document.createElement('div')
    wrapper.innerHTML = [
        `<div class="bg-${color}-200  flex items-start justify-between gap-4 text-${color}-900 px-4 py-2 rounded-lg shadow-xl w-full max-w-xl">`,
        `   <div>${message}</div>`,
        '   <div type="button" class="text-red-500 hover:text-red-700 transition-colors rounded focus:outline-none cursor-pointer" onclick="this.parentElement.remove()" aria-label="Close"><i class="material-icons-round">close</i></div>',
        '</div>'
    ].join('')

    alertPlaceholder.append(wrapper)
}