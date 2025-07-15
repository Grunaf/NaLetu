const budgetBlock = document.getElementById("budget-block");
const budgetAmountBlock = document.getElementById("budget-amount-block");
export const expancesBlock = document.getElementById("expances-block");

const sentinelHideExpanses = document.getElementById(
  "sentinel_for_hide_expanses",
);
const sentinelShowExpanses = document.getElementById(
  "sentinel_for_show_expanses",
);

export function expandeBudgetBlock() {
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
