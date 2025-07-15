const transportsItems = document.getElementById("transports_items");

function hideButtonIfNoMoreTranports(containerTransportsGroupsId, btnToHide) {
  const transportGroup = document
    .getElementById(containerTransportsGroupsId)
    .querySelectorAll(".tranport-group");
  const isSingleGroup = transportGroup.length == 1;
  if (isSingleGroup) {
    btnToHide.classList.add("hidden");
  }
}

function showMoreTransports(direction, btnToHide) {
  const blockDirection = document.getElementById(
    `transports-groups-${direction}`,
  );
  for (let children of blockDirection.children) {
    const classList = children.classList;
    if (classList.contains("hidden")) {
      classList.remove("hidden");
      hideButtonIfNoMoreTranports(`transports-groups-${direction}`, btnToHide);
      break;
    }
  }
}

function handleTransportDirectionBlock(direction) {
  const showMoreTransportBtn = document.getElementById(
    `show-more-transports-${direction}`,
  );
  showMoreTransports(`${direction}`, showMoreTransportBtn);
  hideButtonIfNoMoreTranports(
    `transports-groups-${direction}`,
    showMoreTransportBtn,
  );
  showMoreTransportBtn.addEventListener("click", () =>
    showMoreTransports(`${direction}`),
  );
}

export function handleTransports() {
  if (transportsItems) {
    const directions = ["there", "back"];

    for (var direction of directions) {
      const transportThereBlock = transportsItems.querySelector(
        `#transports-groups-${direction}`,
      );
      if (transportThereBlock) {
        handleTransportDirectionBlock(direction);
      }
    }
  }
}
