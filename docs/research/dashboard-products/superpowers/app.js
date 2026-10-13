const STORAGE_KEY = "support-tickets.v1";
const STATUSES = ["open", "pending", "resolved"];
const PRIORITIES = ["low", "medium", "high"];

function copySeeds() {
  return window.SEED_TICKETS.map(ticket => ({...ticket}));
}

function isTicket(value) {
  return Boolean(value) && typeof value === "object" &&
    ["id", "title", "customer", "description"].every(key => typeof value[key] === "string") &&
    STATUSES.includes(value.status) && PRIORITIES.includes(value.priority);
}

function loadTickets() {
  try {
    const parsed = JSON.parse(localStorage.getItem(STORAGE_KEY));
    if (Array.isArray(parsed) && parsed.every(isTicket)) return parsed;
  } catch (error) { /* missing, corrupt or unavailable storage: use the seeds */ }
  return copySeeds();
}

const state = {tickets: loadTickets(), filters: {query: "", status: "", priority: ""}};

function saveTickets() {
  try { localStorage.setItem(STORAGE_KEY, JSON.stringify(state.tickets)); } catch (error) { /* storage full or blocked */ }
}

// Plain substring search (never a RegExp) over title and customer only; the description and ID are not searched.
function matches(ticket, filters) {
  const query = filters.query.trim().toLowerCase();
  if (query && ![ticket.title, ticket.customer].some(text => text.toLowerCase().includes(query))) return false;
  if (filters.status && ticket.status !== filters.status) return false;
  if (filters.priority && ticket.priority !== filters.priority) return false;
  return true;
}

const list = document.querySelector("#tickets");
const countEl = document.querySelector("#result-count");
const emptyEl = document.querySelector("#empty-state");

function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function badge(kind, value) {
  return element("span", `badge ${kind} ${kind}-${value}`, value);
}

function renderItem(ticket) {
  const item = element("li", "ticket-row");
  const button = element("button", "ticket");
  button.type = "button";
  button.dataset.id = ticket.id;
  button.append(element("span", "ticket-id", ticket.id), " ", element("span", "ticket-title", ticket.title), element("span", "ticket-customer", ticket.customer));
  item.append(button, badge("status", ticket.status), badge("priority", ticket.priority));
  return item;
}

function render() {
  const visible = state.tickets.filter(ticket => matches(ticket, state.filters));
  list.replaceChildren(...visible.map(renderItem));
  countEl.textContent = `${visible.length} ${visible.length === 1 ? "ticket" : "tickets"}`;
  emptyEl.hidden = visible.length > 0;
}

const searchEl = document.querySelector("#search");
const statusEl = document.querySelector("#status-filter");
const priorityEl = document.querySelector("#priority-filter");

function readFilters() {
  state.filters.query = searchEl.value;
  state.filters.status = statusEl.value;
  state.filters.priority = priorityEl.value;
  render();
}

searchEl.addEventListener("input", readFilters);
statusEl.addEventListener("change", readFilters);
priorityEl.addEventListener("change", readFilters);
function resetFilters() {
  searchEl.value = "";
  statusEl.value = "";
  priorityEl.value = "";
  readFilters();
}
document.querySelector("#reset").addEventListener("click", resetFilters);

// ---- Generic modal helpers (also used by the New ticket dialog) ----
const returnTargets = new WeakMap();
const FOCUSABLE = "a[href], button, input, select, textarea, [tabindex]";

function focusableIn(dialog) {
  return [...dialog.querySelectorAll(FOCUSABLE)].filter(node =>
    !node.disabled && node.tabIndex >= 0 && !node.hidden && !node.closest("[hidden]") && node.getClientRects().length > 0);
}

function trapTab(event) {
  if (event.key !== "Tab") return;
  const dialog = event.currentTarget;
  const items = focusableIn(dialog);
  if (!items.length) { event.preventDefault(); return; }
  const first = items[0];
  const last = items[items.length - 1];
  const active = document.activeElement;
  if (event.shiftKey && (active === first || !dialog.contains(active) || active === dialog)) {
    event.preventDefault();
    last.focus();
  } else if (!event.shiftKey && (active === last || !dialog.contains(active) || active === dialog)) {
    event.preventDefault();
    first.focus();
  }
}

function setReturnFocus(dialog, target) {
  returnTargets.set(dialog, target);
}

// Escape fires the native cancel event: dismiss through closeDialog so nothing is saved and focus returns.
function onCancel(event) {
  event.preventDefault();
  closeDialog(event.currentTarget);
}

function openDialog(dialog, opener) {
  if (dialog.dataset.modalReady !== "true") {
    dialog.addEventListener("keydown", trapTab);
    dialog.addEventListener("cancel", onCancel);
    dialog.dataset.modalReady = "true";
  }
  returnTargets.set(dialog, opener || document.activeElement);
  if (!dialog.open) dialog.showModal();
}

function closeDialog(dialog) {
  if (dialog.open) dialog.close();
  const target = returnTargets.get(dialog);
  if (target && target.isConnected) target.focus();
}

// ---- Ticket details dialog ----
const detailsDialog = document.querySelector("#details-dialog");
const detailsStatus = document.querySelector("#details-status");
const detailsPriority = document.querySelector("#details-priority");
let detailsTicketId = null;

function openDetails(ticket, opener) {
  detailsTicketId = ticket.id;
  document.querySelector("#details-title").textContent = ticket.title;
  document.querySelector("#details-customer").textContent = ticket.customer;
  document.querySelector("#details-description").textContent = ticket.description;
  detailsStatus.value = ticket.status;
  detailsPriority.value = ticket.priority;
  openDialog(detailsDialog, opener);
}

list.addEventListener("click", event => {
  if (event.detail > 1) return; // a double-click (e.g. the tail of a double-click on Create ticket) never opens details
  const button = event.target.closest("button.ticket");
  const ticket = button && state.tickets.find(item => item.id === button.dataset.id);
  if (ticket) openDetails(ticket, button);
});

document.querySelector("#details-form").addEventListener("submit", event => {
  event.preventDefault();
  const ticket = state.tickets.find(item => item.id === detailsTicketId);
  if (ticket) {
    ticket.status = detailsStatus.value;
    ticket.priority = detailsPriority.value;
    saveTickets();
    render();
    // render() replaced the rows: return focus to the new row, or to the search box if the filters hid it.
    const rows = [...list.querySelectorAll("button.ticket")];
    setReturnFocus(detailsDialog, rows.find(button => button.dataset.id === ticket.id) || searchEl);
  }
  closeDialog(detailsDialog);
});

document.querySelector("#details-cancel").addEventListener("click", () => closeDialog(detailsDialog));

// ---- New ticket dialog ----
const newDialog = document.querySelector("#new-ticket-dialog");
const newForm = document.querySelector("#new-form");
const newButton = document.querySelector("#new-ticket");
const NEW_TEXT_FIELDS = [["title", "Title"], ["customer", "Customer"], ["description", "Description"]];

// "T" + zero-padded (highest numeric ID suffix + 1); never derived from the array length.
function nextId(tickets) {
  const max = tickets.reduce((highest, ticket) => {
    const match = /^T(\d+)$/.exec(ticket.id);
    return match ? Math.max(highest, Number(match[1])) : highest;
  }, 0);
  return "T" + String(max + 1).padStart(3, "0");
}

// Trims the text fields; whitespace-only counts as empty. Returns {errors: {field: message}, clean: values}.
function validateNew(values) {
  const clean = {
    title: String(values.title ?? "").trim(),
    customer: String(values.customer ?? "").trim(),
    description: String(values.description ?? "").trim(),
    status: STATUSES.includes(values.status) ? values.status : "open",
    priority: PRIORITIES.includes(values.priority) ? values.priority : "medium",
  };
  const errors = {};
  for (const [key, label] of NEW_TEXT_FIELDS) {
    if (!clean[key]) errors[key] = `${label} is required.`;
  }
  return {errors, clean};
}

function clearNewErrors() {
  for (const [key] of NEW_TEXT_FIELDS) {
    const field = document.querySelector(`#new-${key}`);
    const message = document.querySelector(`#new-${key}-error`);
    field.removeAttribute("aria-invalid");
    field.removeAttribute("aria-describedby");
    message.textContent = "";
    message.hidden = true;
  }
}

function showNewErrors(errors) {
  clearNewErrors();
  let firstInvalid = null;
  for (const [key] of NEW_TEXT_FIELDS) {
    if (!errors[key]) continue;
    const field = document.querySelector(`#new-${key}`);
    const message = document.querySelector(`#new-${key}-error`);
    message.textContent = errors[key];
    message.hidden = false;
    field.setAttribute("aria-invalid", "true");
    field.setAttribute("aria-describedby", message.id);
    firstInvalid = firstInvalid || field;
  }
  if (firstInvalid) firstInvalid.focus();
}

newButton.addEventListener("click", () => {
  newForm.reset();
  clearNewErrors();
  openDialog(newDialog, newButton);
  document.querySelector("#new-title").focus();
});

newForm.addEventListener("submit", event => {
  event.preventDefault();
  if (!newDialog.open) return; // re-entrancy guard: a submit after the dialog closed must not create anything
  const {errors, clean} = validateNew({
    title: document.querySelector("#new-title").value,
    customer: document.querySelector("#new-customer").value,
    description: document.querySelector("#new-description").value,
    status: document.querySelector("#new-status").value,
    priority: document.querySelector("#new-priority").value,
  });
  if (Object.keys(errors).length) { showNewErrors(errors); return; }
  const ticket = {id: nextId(state.tickets), ...clean};
  state.tickets.push(ticket);
  saveTickets();
  if (matches(ticket, state.filters)) {
    render();
  } else {
    // The active filters would hide the new ticket: clear them (stored tickets untouched) and focus its row.
    resetFilters();
    setReturnFocus(newDialog, [...list.querySelectorAll("button.ticket")].find(button => button.dataset.id === ticket.id));
  }
  newForm.reset();
  clearNewErrors();
  closeDialog(newDialog); // closing immediately also stops a second click from creating a duplicate
});

document.querySelector("#new-cancel").addEventListener("click", () => closeDialog(newDialog));

// Browsers may restore control values on reload; keep state in sync with the controls.
readFilters();
