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

  const REQUIRED = {title: "Title is required", customer: "Customer is required", description: "Description is required"};

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
        create(input) {
          if (!STATUSES.includes(input.status)) throw new RangeError(`Unknown status: ${input.status}`);
          if (!PRIORITIES.includes(input.priority)) throw new RangeError(`Unknown priority: ${input.priority}`);
          const text = {};
          const errors = {};
          for (const field of Object.keys(REQUIRED)) {
            text[field] = String(input[field] ?? "").trim();
            if (!text[field]) errors[field] = REQUIRED[field];
          }
          if (Object.keys(errors).length > 0) return {errors};
          const current = read(storage) || tickets;
          const next = Math.max(0, ...current.map((ticket) => Number(ticket.id.slice(1)) || 0)) + 1;
          const ticket = {id: `T${String(next).padStart(3, "0")}`, ...text, status: input.status, priority: input.priority};
          tickets = [...current, ticket];
          try { storage.setItem(KEY, JSON.stringify(tickets)); } catch { /* keep working in memory */ }
          return {ticket: {...ticket}};
        },
      };
    },
  };
})();

globalThis.TicketStore = TicketStore;
if (typeof module !== "undefined") module.exports = TicketStore;
