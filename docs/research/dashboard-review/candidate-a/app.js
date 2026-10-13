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
const columns = document.querySelector("#columns");

function cell(className, text) {
  const element = document.createElement("span");
  element.className = className;
  element.textContent = text;
  return element;
}

function render() {
  const tickets = repo.list({query: search.value, status: statusFilter.value, priority: priorityFilter.value});
  list.replaceChildren(...tickets.map((ticket) => {
    const item = document.createElement("li");
    const button = document.createElement("button");
    button.type = "button";
    button.className = "ticket";
    button.dataset.id = ticket.id;
    button.append(
      cell("t-id", ticket.id),
      cell("t-title", ticket.title),
      cell("t-customer", ticket.customer),
      cell("badge t-status", ticket.status),
      cell("badge t-priority", ticket.priority),
    );
    item.append(button);
    return item;
  }));
  count.textContent = `${tickets.length} ${tickets.length === 1 ? "ticket" : "tickets"}`;
  emptyState.hidden = tickets.length > 0;
  list.hidden = columns.hidden = tickets.length === 0;
}

// Search renders on "input" only: a "change" on blur would replace the rows between a click's press and release.
search.addEventListener("input", render);
for (const select of [statusFilter, priorityFilter]) select.addEventListener("change", render);
document.querySelector("#reset").addEventListener("click", () => {
  search.value = "";
  statusFilter.value = "";
  priorityFilter.value = "";
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
  const button = [...list.querySelectorAll("button.ticket")].find((candidate) => candidate.dataset.id === openerId);
  (button || search).focus();
}

function closeDetails() {
  dialog.close();
  restoreFocus();
}

list.addEventListener("click", (event) => {
  const button = event.target.closest("button.ticket");
  if (!button) return;
  const ticket = repo.get(button.dataset.id);
  if (!ticket) return;
  openerId = ticket.id;
  document.querySelector("#details-id").textContent = ticket.id;
  document.querySelector("#details-status-badge").textContent = ticket.status;
  document.querySelector("#details-priority-badge").textContent = ticket.priority;
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

const newButton = document.querySelector("#new-ticket");
const creator = document.querySelector("#create");
const createForm = document.querySelector("#create-form");
const createFields = ["title", "customer", "description"].map((name) => ({
  name,
  input: document.querySelector(`#create-${name}`),
  error: document.querySelector(`#create-${name}-error`),
}));

function closeCreator() {
  creator.close();
  newButton.focus();
}

function showErrors(errors) {
  for (const {name, input, error} of createFields) {
    error.textContent = errors[name] || "";
    error.hidden = !errors[name];
    if (errors[name]) input.setAttribute("aria-invalid", "true");
    else input.removeAttribute("aria-invalid");
  }
  createFields.find(({name}) => errors[name])?.input.focus();
}

newButton.addEventListener("click", () => {
  createForm.reset();
  showErrors({});
  creator.showModal();
});
creator.addEventListener("keydown", trapTab);
creator.addEventListener("cancel", (event) => { event.preventDefault(); closeCreator(); });
document.querySelector("#create-cancel").addEventListener("click", closeCreator);
createForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const result = repo.create(Object.fromEntries(new FormData(createForm)));
  if (result.errors) { showErrors(result.errors); return; }
  render();
  closeCreator();
});

render();
