const icons = {
  folder:
    '<svg viewBox="0 0 24 24"><path d="M3 7V5a1 1 0 0 1 1-1h5l2 3h9a1 1 0 0 1 1 1v11a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V7Z"/><path d="M3 9h18"/></svg>',
  branch:
    '<svg viewBox="0 0 24 24"><circle cx="6" cy="5" r="2"/><circle cx="18" cy="5" r="2"/><circle cx="6" cy="19" r="2"/><path d="M6 7v10m12-10v3a4 4 0 0 1-4 4h-4a4 4 0 0 0-4 3"/></svg>',
  server:
    '<svg viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="7" rx="1"/><rect x="3" y="14" width="18" height="7" rx="1"/><path d="M6 7.5h.01M6 17.5h.01M15 7.5h3M15 17.5h3"/></svg>',
  refresh:
    '<svg viewBox="0 0 24 24"><path d="M20 7v5h-5M4 17v-5h5M5.2 8a7 7 0 0 1 11.6-3L20 9M4 15l3.2 4A7 7 0 0 0 18.8 16"/></svg>',
};

let applicationState = { profiles: [], destinations: [], history: [] };
let busy = false;
let toastTimeout;

function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function icon(name, className = "") {
  const node = element("span", className);
  node.innerHTML = icons[name];
  return node;
}

function showToast(message) {
  const toast = document.querySelector("#toast");
  toast.textContent = message;
  toast.classList.add("visible");
  clearTimeout(toastTimeout);
  toastTimeout = setTimeout(() => toast.classList.remove("visible"), 4500);
}

async function request(action, value = null, previous = null) {
  if (busy) return;
  busy = true;
  document.querySelector("#create").disabled = true;
  try {
    const result = await window.pywebview.api.request(action, value, previous);
    if (result.state) applicationState = result.state;
    render();
    if (!result.ok) showToast(result.error);
    else if (result.message) showToast(result.message);
    return result.ok;
  } catch (error) {
    showToast("Could not complete that action. Please try again.");
  } finally {
    busy = false;
    document.querySelector("#create").disabled =
      !applicationState.destinations.length;
  }
}

function switchTab(name) {
  document
    .querySelectorAll(".tab")
    .forEach((tab) => tab.classList.toggle("active", tab.dataset.tab === name));
  document
    .querySelectorAll(".page")
    .forEach((page) => page.classList.toggle("active", page.id === name));
}

function render() {
  const state = applicationState;
  document.querySelector("#library-count").textContent = state.profiles.length;
  document.querySelector("#destination-count").textContent =
    state.destinations.length;
  document.querySelector("#history-count").textContent = state.history.length;
  const library = document.querySelector("#sources");
  library.replaceChildren();
  for (const source of state.profiles) {
    const button = element(
      "button",
      `source-entry${source.path === state.source ? " selected" : ""}`,
    );
    button.title = source.path;
    button.append(icon("folder"));
    const description = element("span", "source-entry-text");
    description.append(element("strong", "", source.name));
    button.append(description);
    button.onclick = async () => {
      if (await request("select_source", source.path)) switchTab("workspace");
    };
    library.append(button);
  }
  document.querySelector("#source-name").textContent =
    state.source_name || "Choose a source folder";
  document.querySelector("#source-path").textContent = state.source || "";
  document.querySelector("#source-path").hidden = !state.source;
  document.querySelector("#source-choose").textContent = state.source
    ? "Change source"
    : "Choose folder";
  document.querySelector("#source-path").title = state.source || "";
  document.querySelector("#open-source").disabled = !state.source;
  const destinations = document.querySelector("#destination-cards");
  destinations.replaceChildren();
  for (const destination of state.destinations) {
    const card = element("article", "destination-card");
    const heading = element("div", "destination-heading");
    heading.append(
      icon("server"),
      element("h3", "", destination.name || "Destination"),
      element("span", `badge ${destination.status}`, destination.status),
    );
    card.append(heading, element("p", "path", destination.path));
    if (destination.status === "blocked")
      card.append(element("p", "link-detail", destination.detail));
    const actions = element("div", "card-actions");
    const open = element("button", "folder-button");
    open.append(icon("folder"));
    open.title = "Open folder in File Explorer";
    open.setAttribute("aria-label", "Open folder in File Explorer");
    open.onclick = () => request("open_folder", destination.path);
    const edit = element("button", "", "Edit path");
    edit.title = "Choose a new parent folder";
    edit.onclick = () => request("edit_destination", destination.path);
    const remove = element("button", "remove", "Remove from setup");
    remove.onclick = () => request("remove_destination", destination.path);
    actions.append(open, edit, remove);
    card.append(actions);
    destinations.append(card);
  }
  const add = element("button", "add-card");
  add.append(
    element("span", "plus", "+"),
    element("strong", "", "Add destination"),
  );
  add.disabled = !state.source;
  add.onclick = () => request("choose_destination");
  destinations.append(add);
  const linked = state.destinations.filter(
    (destination) => destination.status === "linked",
  ).length;
  document.querySelector("#setup-summary").textContent = state.destinations
    .length
    ? `${linked} of ${state.destinations.length} destinations linked`
    : "";
  document.querySelector("#create").disabled = !state.destinations.length;
  renderHistory();
}

function renderHistory() {
  const container = document.querySelector("#history-list");
  const query = document
    .querySelector("#history-search")
    .value.toLowerCase()
    .trim();
  const history = applicationState.history.filter((entry) =>
    `${entry.source} ${entry.destination}`.toLowerCase().includes(query),
  );
  container.replaceChildren();
  if (!history.length) {
    const empty = element("div", "history-empty");
    empty.append(
      icon("branch"),
      element("h3", "", query ? "No matches" : "No history yet"),
    );
    container.append(empty);
  }
  for (const entry of history) {
    const row = element("article", "history-entry");
    row.append(element("div", "history-marker"));
    const body = element("div", "history-body");
    const heading = element("div", "history-heading");
    const date = new Date(entry.recorded_at);
    const formattedDate = Number.isNaN(date.getTime())
      ? entry.recorded_at
      : date.toLocaleString("en-GB", {
          day: "2-digit",
          month: "short",
          year: "numeric",
          hour: "2-digit",
          minute: "2-digit",
        });
    heading.append(
      element("strong", "", entry.source_name),
      element(
        "span",
        `badge ${entry.link.status}`,
        entry.link.status === "ready" ? "not linked" : entry.link.status,
      ),
      element("time", "", formattedDate),
    );
    heading.querySelector("time").title =
      entry.action === "created"
        ? "Created"
        : "Found; original creation date unknown";
    const paths = element("div", "history-paths");
    paths.append(
      element("span", "", "FROM"),
      element("p", "path", entry.source),
      element("span", "", "TO"),
      element("p", "path", entry.destination),
    );
    const bottom = element("div", "history-bottom");
    const load = element("button", "", "Load setup ↗");
    load.onclick = async () => {
      if (await request("load_history", entry.id)) switchTab("workspace");
    };
    bottom.append(load);
    body.append(heading, paths, bottom);
    row.append(body);
    container.append(row);
  }
}

document.querySelector("#source-icon").append(icon("folder"));
document.querySelector("#open-source").append(icon("folder"));
document.querySelector("#open-source").onclick = () =>
  request("open_folder", applicationState.source);
document.querySelector("#refresh").append(icon("refresh"));
document.querySelector("#refresh").onclick = () => request("state");
document
  .querySelectorAll("[data-action]")
  .forEach((button) => (button.onclick = () => request(button.dataset.action)));
document
  .querySelectorAll("[data-window]")
  .forEach(
    (button) =>
      (button.onclick = () =>
        window.pywebview.api.window_action(button.dataset.window)),
  );
document
  .querySelectorAll("[data-tab]")
  .forEach((button) => (button.onclick = () => switchTab(button.dataset.tab)));
document.querySelector("#history-search").oninput = renderHistory;
document.querySelector("#create").onclick = () => request("create");
window.addEventListener("pywebviewready", () => request("state"));
render();
