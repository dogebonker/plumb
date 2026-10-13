const TicketStore = (() => {
  const KEY = "support-tickets.v1";
  const STATUSES = ["open", "pending", "resolved"];
  const PRIORITIES = ["low", "medium", "high"];
  const TEXT_FIELDS = ["id", "title", "customer", "description"];

  const isTicket = (record) =>
    record !== null && typeof record === "object" &&
    TEXT_FIELDS.every((field) => typeof record[field] === "string") &&
    STATUSES.includes(record.status) && PRIORITIES.includes(record.priority);

  const copyAll = (tickets) => tickets.map((ticket) => ({...ticket}));

  // Stored tickets, or null when storage is missing, unreadable or invalid.
  function read(storage) {
    try {
      const parsed = JSON.parse(storage.getItem(KEY));
      return Array.isArray(parsed) && parsed.every(isTicket) ? parsed : null;
    } catch {
      return null;
    }
  }

  return {
    STATUSES,
    PRIORITIES,

    /** @param {Storage} storage @param {Ticket[]} seed @returns {TicketRepo} */
    open(storage, seed) {
      let tickets = read(storage) || copyAll(seed);
      return {
        list(filter = {}) {
          const {query = "", status = "", priority = ""} = filter;
          const needle = query.toLowerCase();
          return copyAll(tickets.filter((ticket) =>
            (!needle || ticket.title.toLowerCase().includes(needle) || ticket.customer.toLowerCase().includes(needle)) &&
            (!status || ticket.status === status) &&
            (!priority || ticket.priority === priority)));
        },
        get(id) {
          const ticket = tickets.find((candidate) => candidate.id === id);
          return ticket && {...ticket};
        },
        update(id, changes) {
          const {status, priority} = changes;
          if (status !== undefined && !STATUSES.includes(status)) throw new RangeError(`Unknown status: ${status}`);
          if (priority !== undefined && !PRIORITIES.includes(priority)) throw new RangeError(`Unknown priority: ${priority}`);
          const current = read(storage) || tickets;
          const ticket = current.find((candidate) => candidate.id === id);
          if (!ticket) return undefined;
          if (status !== undefined) ticket.status = status;
          if (priority !== undefined) ticket.priority = priority;
          tickets = current;
          try { storage.setItem(KEY, JSON.stringify(tickets)); } catch { /* keep working in memory */ }
          return {...ticket};
        },
        create(input) { throw new Error("stub"); },
      };
    },
  };
})();

globalThis.TicketStore = TicketStore;
if (typeof module !== "undefined") module.exports = TicketStore;
