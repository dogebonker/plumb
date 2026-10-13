const list = document.querySelector("#tickets");
const search = document.querySelector("#search");
const statusFilter = document.querySelector("#status-filter");
const priorityFilter = document.querySelector("#priority-filter");
const store = TicketStore.open();

function render() {
  const matches = TicketStore.filter(store.all(), {query: search.value, status: statusFilter.value, priority: priorityFilter.value});
  document.querySelector("#result-count").textContent = matches.length === 1 ? "1 ticket" : `${matches.length} tickets`;
  document.querySelector("#empty-state").hidden = matches.length > 0;
  list.replaceChildren(...matches.map(ticket => {
    const item = document.createElement("li");
    const button = document.createElement("button");
    button.type = "button";
    button.className = "ticket";
    button.dataset.id = ticket.id;
    for (const text of [`${ticket.id} ${ticket.title}`, ticket.customer, `${ticket.status} · ${ticket.priority}`]) {
      const line = document.createElement("span");
      line.textContent = text;
      button.append(line);
    }
    item.append(button);
    return item;
  }));
}

// Binds the generic dialog behaviour: returns open(findFocusTarget), which shows the dialog modally.
// When the dialog closes (Save, Cancel or Escape) focus goes to findFocusTarget() at that moment.
function bindDialog(dialog) {
  let findFocusTarget = () => null;
  dialog.addEventListener("close", () => findFocusTarget()?.focus());
  dialog.addEventListener("keydown", event => {
    if (event.key !== "Tab") return;
    const controls = [...dialog.querySelectorAll("button, input, select, textarea, [href]")].filter(control => !control.disabled);
    const edge = event.shiftKey ? controls[0] : controls.at(-1);
    if (document.activeElement === edge) {
      event.preventDefault();
      (event.shiftKey ? controls.at(-1) : controls[0]).focus();
    }
  });
  return finder => {
    findFocusTarget = finder;
    dialog.showModal();
  };
}

const detailsDialog = document.querySelector("#details-dialog");
const detailsStatus = document.querySelector("#details-status");
const detailsPriority = document.querySelector("#details-priority");
const openDetails = bindDialog(detailsDialog);
let detailsId = "";

list.addEventListener("click", event => {
  const row = event.target.closest("button.ticket");
  const ticket = row && store.all().find(item => item.id === row.dataset.id);
  if (!ticket) return;
  detailsId = ticket.id;
  document.querySelector("#details-heading").textContent = `${ticket.id} ${ticket.title}`;
  document.querySelector("#details-customer").textContent = ticket.customer;
  document.querySelector("#details-description").textContent = ticket.description;
  detailsStatus.value = ticket.status;
  detailsPriority.value = ticket.priority;
  openDetails(() => list.querySelector(`[data-id="${detailsId}"]`) ?? search);
});
document.querySelector("#details-form").addEventListener("submit", event => {
  event.preventDefault();
  store.update(detailsId, {status: detailsStatus.value, priority: detailsPriority.value});
  render();
  detailsDialog.close();
});
document.querySelector("#details-cancel").addEventListener("click", () => detailsDialog.close());

search.addEventListener("input", render);
statusFilter.addEventListener("change", render);
priorityFilter.addEventListener("change", render);
document.querySelector("#reset").addEventListener("click", () => {
  search.value = statusFilter.value = priorityFilter.value = "";
  render();
});
render();
