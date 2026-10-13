const storageKey = "support-dashboard:tickets:v1";
function readTickets() {
  const raw = localStorage.getItem(storageKey);
  if (raw === null) return window.SEED_TICKETS.map(ticket => ({...ticket}));
  const stored = JSON.parse(raw);
  if (!Array.isArray(stored) || stored.some(ticket => !ticket || typeof ticket.id !== "string"
    || !["title", "customer", "description"].every(name => typeof ticket[name] === "string" && ticket[name].trim())
    || !["open", "pending", "resolved"].includes(ticket.status) || !["low", "medium", "high"].includes(ticket.priority))
    || new Set(stored.map(ticket => ticket.id)).size !== stored.length) throw new Error("Invalid saved data");
  return stored;
}
let tickets = [];
let loadError = "";
try { tickets = readTickets(); } catch { loadError = "Saved data cannot be read. It has been preserved; restore a valid backup before saving."; }
const search = document.querySelector("#search");
const statusFilter = document.querySelector("#status-filter");
const priorityFilter = document.querySelector("#priority-filter");
const list = document.querySelector("#tickets");
const dialog = document.createElement("dialog");
dialog.setAttribute("aria-labelledby", "dialog-title");
dialog.innerHTML = `<h2 id="dialog-title"></h2><form novalidate>
  <label>Title <input id="ticket-title" name="title" required aria-describedby="title-error"></label><span id="title-error" class="error" role="alert"></span>
  <label>Customer <input id="ticket-customer" name="customer" required aria-describedby="customer-error"></label><span id="customer-error" class="error" role="alert"></span>
  <label>Description <textarea id="ticket-description" name="description" required aria-describedby="description-error"></textarea></label><span id="description-error" class="error" role="alert"></span>
  <label>Status <select name="status" aria-label="Status"><option>open</option><option>pending</option><option>resolved</option></select></label>
  <label>Priority <select name="priority" aria-label="Priority"><option>low</option><option>medium</option><option>high</option></select></label>
  <div class="actions"><button type="submit" id="save"></button><button type="button" id="cancel">Cancel</button></div>
</form>`;
document.body.append(dialog);
const form = dialog.querySelector("form");
const storageError = document.createElement("p");
storageError.setAttribute("role", "alert");
storageError.className = "error";
document.querySelector("main").prepend(storageError);
const saveError = document.createElement("p");
saveError.setAttribute("role", "alert");
saveError.className = "error";
form.prepend(saveError);
storageError.textContent = loadError;
let editing = null;
let opener = null;

function render() {
  const query = search.value.toLowerCase();
  const matching = tickets.filter(ticket => (ticket.title.toLowerCase().includes(query) || ticket.customer.toLowerCase().includes(query))
    && (!statusFilter.value || ticket.status === statusFilter.value)
    && (!priorityFilter.value || ticket.priority === priorityFilter.value));
  list.replaceChildren();
  for (const ticket of matching) {
    const item = document.createElement("li");
    const button = document.createElement("button");
    button.type = "button";
    button.className = "ticket";
    button.dataset.ticket = ticket.id;
    for (const [tag, text] of [["strong", `${ticket.id} ${ticket.title}`], ["span", ticket.customer], ["span", `${ticket.status} · ${ticket.priority}`]]) {
      const line = document.createElement(tag);
      line.textContent = text;
      button.append(line);
    }
    button.addEventListener("click", () => openDialog(ticket, button));
    item.append(button);
    list.append(item);
  }
  document.querySelector("#result-count").textContent = `${matching.length} ${matching.length === 1 ? "ticket" : "tickets"}`;
  document.querySelector("#empty-state").hidden = matching.length !== 0;
}

function openDialog(ticket, button) {
  editing = ticket ? {...ticket} : null;
  saveError.textContent = "";
  opener = button;
  form.reset();
  for (const name of ["title", "customer", "description"]) {
    form.elements[name].value = ticket ? ticket[name] : "";
    form.elements[name].readOnly = !!ticket;
    form.elements[name].removeAttribute("aria-invalid");
    document.querySelector(`#${name}-error`).textContent = "";
  }
  form.elements.status.value = ticket ? ticket.status : "open";
  form.elements.priority.value = ticket ? ticket.priority : "medium";
  document.querySelector("#dialog-title").textContent = ticket ? "Ticket details" : "New ticket";
  document.querySelector("#save").textContent = ticket ? "Save changes" : "Create ticket";
  dialog.showModal();
}

form.addEventListener("submit", event => {
  event.preventDefault();
  const values = {};
  if (!editing) {
    let firstInvalid = null;
    for (const name of ["title", "customer", "description"]) {
      const field = form.elements[name];
      values[name] = field.value.trim();
      field.setAttribute("aria-invalid", String(!values[name]));
      document.querySelector(`#${name}-error`).textContent = values[name] ? "" : `${name[0].toUpperCase() + name.slice(1)} is required.`;
      if (!values[name] && !firstInvalid) firstInvalid = field;
    }
    if (firstInvalid) { firstInvalid.focus(); return; }
  }
  try {
    const next = readTickets();
    if (editing) {
      const current = next.find(ticket => ticket.id === editing.id);
      if (!current) throw new Error("This ticket changed in another tab. Cancel and reopen it before saving.");
      for (const name of ["status", "priority"]) {
        const value = form.elements[name].value;
        if (value === editing[name]) continue;
        if (current[name] !== editing[name] && current[name] !== value) {
          throw new Error("This ticket changed in another tab. Cancel and reopen it before saving.");
        }
        current[name] = value;
      }
    } else {
      const number = Math.max(0, ...next.map(ticket => Number(ticket.id.slice(1)) || 0)) + 1;
      next.push({id: `T${String(number).padStart(3, "0")}`, ...values, status: form.elements.status.value, priority: form.elements.priority.value});
    }
    localStorage.setItem(storageKey, JSON.stringify(next));
    tickets = next;
    storageError.textContent = "";
  } catch (error) {
    saveError.textContent = error.message.includes("another tab") ? error.message
      : "Could not save to storage. Your draft and existing saved data are preserved. Restore storage or valid saved data, then retry.";
    return;
  }
  dialog.close();
  render();
});
document.querySelector("#cancel").addEventListener("click", () => dialog.close());
dialog.addEventListener("close", () => { if (opener && opener.isConnected) opener.focus(); });
dialog.addEventListener("keydown", event => {
  if (event.key !== "Tab") return;
  const controls = [...dialog.querySelectorAll("input, textarea, select, button")];
  const first = controls[0];
  const last = controls[controls.length - 1];
  if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
  else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
});
document.querySelector("#new-ticket").addEventListener("click", event => openDialog(null, event.currentTarget));
for (const control of [search, statusFilter, priorityFilter]) control.addEventListener("input", render);
document.querySelector("#reset").addEventListener("click", () => { search.value = ""; statusFilter.value = ""; priorityFilter.value = ""; render(); });
render();
