const store = window.TicketStore;
const noStorage = {getItem: () => null, setItem() {}, removeItem() {}};
let storage = noStorage;
try { storage = window.localStorage || noStorage; } catch { /* storage disabled: stay in memory */ }
const repo = store.open(storage, window.SEED_TICKETS);

const search = document.querySelector("#search");
const statusFilter = document.querySelector("#status-filter");
const priorityFilter = document.querySelector("#priority-filter");
const list = document.querySelector("#tickets");
const count = document.querySelector("#result-count");
const emptyState = document.querySelector("#empty-state");

function render() {
  const tickets = repo.list({query: search.value, status: statusFilter.value, priority: priorityFilter.value});
  list.replaceChildren(...tickets.map((ticket) => {
    const item = document.createElement("li");
    const button = document.createElement("button");
    button.type = "button";
    button.className = "ticket";
    for (const text of [`${ticket.id} ${ticket.title}`, ticket.customer, `${ticket.status} · ${ticket.priority}`]) {
      const line = document.createElement("span");
      line.textContent = text;
      button.append(line);
    }
    item.append(button);
    return item;
  }));
  count.textContent = `${tickets.length} ${tickets.length === 1 ? "ticket" : "tickets"}`;
  emptyState.hidden = tickets.length > 0;
  list.hidden = tickets.length === 0;
}

for (const control of [search, statusFilter, priorityFilter]) {
  control.addEventListener("input", render);
  control.addEventListener("change", render);
}
document.querySelector("#reset").addEventListener("click", () => {
  search.value = "";
  statusFilter.value = "";
  priorityFilter.value = "";
  const dialog = document.querySelector("#details");
const detailsStatus = document.querySelector("#details-status");
const detailsPriority = document.querySelector("#details-priority");
let openerId = null;

// Keeps Tab and Shift+Tab inside an open dialog; shared by every dialog.
function trapTab(event) {
  if (event.key !== "Tab") return;
  const controls = [...event.currentTarget.querySelectorAll("select, input, textarea, button")].filter((control) => !control.disabled);
  const first = controls[0];
  const last = controls[controls.length - 1];
  if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
  else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
}

function restoreFocus() {
  const button = [...list.querySelectorAll("button.ticket")].find((candidate) => candidate.textContent.startsWith(`${openerId} `));
  (button || search).focus();
}

function closeDetails() {
  dialog.close();
  restoreFocus();
}

list.addEventListener("click", (event) => {
  const button = event.target.closest("button.ticket");
  if (!button) return;
  const ticket = repo.get(button.textContent.split(" ", 1)[0]);
  if (!ticket) return;
  openerId = ticket.id;
  document.querySelector("#details-title").textContent = ticket.title;
  document.querySelector("#details-customer").textContent = ticket.customer;
  document.querySelector("#details-description").textContent = ticket.description;
  detailsStatus.value = ticket.status;
  detailsPriority.value = ticket.priority;
  dialog.showModal();
});

dialog.addEventListener("keydown", trapTab);
dialog.addEventListener("cancel", (event) => { event.preventDefault(); closeDetails(); });
document.querySelector("#details-cancel").addEventListener("click", closeDetails);
document.querySelector("#details-form").addEventListener("submit", (event) => {
  event.preventDefault();
  repo.update(openerId, {status: detailsStatus.value, priority: detailsPriority.value});
  render();
  closeDetails();
});

render();
});

const dialog = document.querySelector("#details");
const detailsStatus = document.querySelector("#details-status");
const detailsPriority = document.querySelector("#details-priority");
let openerId = null;

// Keeps Tab and Shift+Tab inside an open dialog; shared by every dialog.
function trapTab(event) {
  if (event.key !== "Tab") return;
  const controls = [...event.currentTarget.querySelectorAll("select, input, textarea, button")].filter((control) => !control.disabled);
  const first = controls[0];
  const last = controls[controls.length - 1];
  if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
  else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
}

function restoreFocus() {
  const button = [...list.querySelectorAll("button.ticket")].find((candidate) => candidate.textContent.startsWith(`${openerId} `));
  (button || search).focus();
}

function closeDetails() {
  dialog.close();
  restoreFocus();
}

list.addEventListener("click", (event) => {
  const button = event.target.closest("button.ticket");
  if (!button) return;
  const ticket = repo.get(button.textContent.split(" ", 1)[0]);
  if (!ticket) return;
  openerId = ticket.id;
  document.querySelector("#details-title").textContent = ticket.title;
  document.querySelector("#details-customer").textContent = ticket.customer;
  document.querySelector("#details-description").textContent = ticket.description;
  detailsStatus.value = ticket.status;
  detailsPriority.value = ticket.priority;
  dialog.showModal();
});

dialog.addEventListener("keydown", trapTab);
dialog.addEventListener("cancel", (event) => { event.preventDefault(); closeDetails(); });
document.querySelector("#details-cancel").addEventListener("click", closeDetails);
document.querySelector("#details-form").addEventListener("submit", (event) => {
  event.preventDefault();
  repo.update(openerId, {status: detailsStatus.value, priority: detailsPriority.value});
  render();
  closeDetails();
});

render();
