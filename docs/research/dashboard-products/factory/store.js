(() => {
  const STORAGE_KEY = "support-tickets.v1";
  const STATUSES = ["open", "pending", "resolved"];
  const PRIORITIES = ["low", "medium", "high"];
  const TEXT_FIELDS = ["id", "title", "customer", "status", "priority", "description"];

  const isValidTicket = item =>
    item !== null && typeof item === "object" &&
    TEXT_FIELDS.every(field => typeof item[field] === "string") &&
    STATUSES.includes(item.status) && PRIORITIES.includes(item.priority);

  // Stored tickets, or null when storage is missing, unreadable or malformed.
  function readStored(storage) {
    try {
      const parsed = JSON.parse(storage.getItem(STORAGE_KEY));
      return Array.isArray(parsed) && parsed.every(isValidTicket) ? parsed : null;
    } catch {
      return null;
    }
  }

  const copyTicket = ticket => Object.fromEntries(TEXT_FIELDS.map(field => [field, ticket[field]]));

  globalThis.TicketStore = {
    STATUSES,
    PRIORITIES,
    open(storage = globalThis.localStorage, seeds = globalThis.SEED_TICKETS) {
      let tickets = readStored(storage) ?? seeds;
      return {
        all: () => tickets.map(copyTicket),
        update(id, {status, priority}) {
          if (!STATUSES.includes(status)) throw new RangeError(`Unknown status: ${status}`);
          if (!PRIORITIES.includes(priority)) throw new RangeError(`Unknown priority: ${priority}`);
          const current = readStored(storage) ?? tickets;
          const target = current.find(ticket => ticket.id === id);
          if (!target) return null;
          const updated = {...copyTicket(target), status, priority};
          tickets = current.map(ticket => ticket === target ? updated : copyTicket(ticket));
          try {
            storage.setItem(STORAGE_KEY, JSON.stringify(tickets));
          } catch {
            // The change stays in memory.
          }
          return copyTicket(updated);
        },
      };
    },
    filter(tickets, {query = "", status = "", priority = ""} = {}) {
      const needle = query.trim().toLowerCase();
      return tickets.filter(ticket =>
        (ticket.title.toLowerCase().includes(needle) || ticket.customer.toLowerCase().includes(needle)) &&
        (status === "" || ticket.status === status) &&
        (priority === "" || ticket.priority === priority));
    },
  };
})();
