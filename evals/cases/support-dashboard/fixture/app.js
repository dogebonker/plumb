const list = document.querySelector("#tickets");
for (const ticket of window.SEED_TICKETS) {
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
  list.append(item);
}
