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
let applicationReady = false;
let loadingTimeout;
let readinessTimer;
let refreshPending = false;
let refreshTimer;

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
    if (typeof window.pywebview?.api?.request !== "function")
      throw new Error("Desktop connection unavailable");
    const operation = window.pywebview.api.request(action, value, previous);
    const result =
      !applicationReady && action === "state"
        ? await startupRequest(operation)
        : await operation;
    if (result.state) applicationState = result.state;
    render();
    if (!result.ok) showToast(result.error);
    else if (result.message) showToast(result.message);
    if (!applicationReady) {
      if (result.ok) {
        applicationReady = true;
        clearTimeout(loadingTimeout);
        document.querySelector("#loading-screen").hidden = true;
      } else {
        showLoadingError();
      }
    }
    return result.ok;
  } catch (error) {
    showToast("Could not complete that action. Please try again.");
    if (!applicationReady) showLoadingError();
  } finally {
    busy = false;
    document.querySelector("#create").disabled =
      !applicationState.destinations.length;
    if (refreshPending && applicationReady) {
      refreshPending = false;
      scheduleStatusRefresh();
    }
  }
}

function showLoadingError() {
  document.querySelector("#loading-message").textContent =
    "Could not load your folders.";
  document.querySelector(".loading-spinner").hidden = true;
  document.querySelector("#retry-loading").hidden = false;
}

function startupRequest(operation) {
  let timeout;
  const deadline = new Promise((resolve, reject) => {
    timeout = setTimeout(() => reject(new Error("Loading timed out")), 15000);
  });
  return Promise.race([operation, deadline]).finally(() =>
    clearTimeout(timeout),
  );
}

function loadApplication() {
  if (applicationReady || busy) return;
  clearTimeout(loadingTimeout);
  clearTimeout(readinessTimer);
  document.querySelector("#loading-message").textContent = "Loading…";
  document.querySelector(".loading-spinner").hidden = false;
  document.querySelector("#retry-loading").hidden = true;
  loadingTimeout = setTimeout(() => {
    clearTimeout(readinessTimer);
    if (!applicationReady && !busy) showLoadingError();
  }, 15000);
  function connectWhenReady() {
    if (typeof window.pywebview?.api?.request === "function") {
      clearTimeout(loadingTimeout);
      request("state");
    } else {
      readinessTimer = setTimeout(connectWhenReady, 250);
    }
  }
  connectWhenReady();
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
  renderSources();
  const selectedSource = state.profiles.find(
    (source) => source.path === state.source,
  );
  const groupPicker = document.querySelector("#source-group");
  groupPicker.replaceChildren();
  for (const group of state.groups || ["Scripts", "Maps", "Props", "Other"]) {
    groupPicker.append(element("option", "", group));
  }
  groupPicker.value = selectedSource?.group || "Other";
  groupPicker.disabled = !selectedSource;
  document.querySelector("#source-name").textContent =
    state.source_name || "Choose a source folder";
  document.querySelector("#source-path").textContent = state.source || "";
  document.querySelector("#source-path").hidden = !state.source;
  document.querySelector("#source-choose").textContent = state.source
    ? "Change source"
    : "Choose folder";
  document.querySelector("#source-path").title = state.source || "";
  document.querySelector("#open-source").disabled = !state.source;
  document.querySelector("#source-open-with").disabled = !state.source;
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
    const openWith = element("button", "", "Open with");
    openWith.onclick = (event) =>
      showEditorMenu(event.currentTarget, destination.path);
    actions.append(open, openWith, edit, remove);
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

function renderSources() {
  const library = document.querySelector("#sources");
  const scrollPosition = library.scrollTop;
  const query = document
    .querySelector("#source-search")
    .value.trim()
    .toLowerCase();
  const sources = applicationState.profiles.filter((source) =>
    `${source.name} ${source.path}`.toLowerCase().includes(query),
  );
  library.replaceChildren();
  const groups = [
    "Favourites",
    ...(applicationState.groups || ["Scripts", "Maps", "Props", "Other"]),
  ];
  for (const group of groups) {
    const members = sources.filter((source) =>
      group === "Favourites"
        ? source.favourite
        : !source.favourite && (source.group || "Other") === group,
    );
    if (!members.length) continue;
    library.append(element("h3", "source-section-title", group));
    for (const source of members) {
      const row = element(
        "div",
        `source-entry${source.path === applicationState.source ? " selected" : ""}`,
      );
      const select = element("button", "source-select");
      select.title = source.path;
      select.append(icon("folder"));
      const description = element("span", "source-entry-text");
      description.append(element("strong", "", source.name));
      select.append(description);
      select.onclick = async () => {
        if (await request("select_source", source.path)) switchTab("workspace");
      };
      const favourite = element(
        "button",
        `favourite-source${source.favourite ? " pinned" : ""}`,
        source.favourite ? "★" : "☆",
      );
      favourite.title = source.favourite ? "Unpin favourite" : "Pin favourite";
      favourite.setAttribute(
        "aria-label",
        `${favourite.title}: ${source.name}`,
      );
      favourite.setAttribute("aria-pressed", String(Boolean(source.favourite)));
      favourite.onclick = () => request("toggle_favourite", source.path);
      const remove = element("button", "remove-source", "×");
      remove.title = "Remove from app";
      remove.setAttribute("aria-label", `Remove ${source.name} from app`);
      remove.onclick = () => request("remove_source", source.path);
      row.append(select, favourite, remove);
      library.append(row);
    }
  }
  if (query && !sources.length)
    library.append(element("p", "source-search-empty", "No matches"));
  library.scrollTop = scrollPosition;
}

function scheduleStatusRefresh() {
  if (!applicationReady || document.hidden) return;
  clearTimeout(refreshTimer);
  refreshTimer = setTimeout(() => {
    if (busy) {
      refreshPending = true;
      return;
    }
    request("state");
  }, 250);
}

window.addEventListener("focus", scheduleStatusRefresh);
document.addEventListener("visibilitychange", () => {
  if (!document.hidden) scheduleStatusRefresh();
});
document.querySelector("#source-group").onchange = (event) =>
  request("set_group", applicationState.source, event.target.value);

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

async function showEditorMenu(anchor, folder) {
  const menu = document.querySelector("#editor-menu");
  menu.hidden = true;
  menu.replaceChildren();
  try {
    const result = await window.pywebview.api.request("editors");
    if (!result.ok) {
      showToast(result.error);
      return;
    }
    for (const editor of result.editors) {
      const button = element("button", "", editor.name);
      button.setAttribute("role", "menuitem");
      button.onclick = () => {
        menu.hidden = true;
        request("open_with", folder, editor.id);
      };
      menu.append(button);
    }
    if (!result.editors.length)
      menu.append(element("p", "", "No supported editors found"));
    menu.hidden = false;
    const bounds = anchor.getBoundingClientRect();
    menu.style.left = `${Math.max(8, Math.min(bounds.left, window.innerWidth - menu.offsetWidth - 8))}px`;
    menu.style.top = `${bounds.bottom + menu.offsetHeight + 8 > window.innerHeight ? Math.max(8, bounds.top - menu.offsetHeight - 6) : bounds.bottom + 6}px`;
    menu.querySelector("button")?.focus();
  } catch (error) {
    showToast("Could not detect installed editors.");
  }
}

document.addEventListener("pointerdown", (event) => {
  if (!event.target.closest("#editor-menu"))
    document.querySelector("#editor-menu").hidden = true;
});
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape")
    document.querySelector("#editor-menu").hidden = true;
});
document.querySelector(".canvas-scroll").addEventListener("scroll", () => {
  document.querySelector("#editor-menu").hidden = true;
});
document.querySelector("#source-open-with").onclick = (event) =>
  showEditorMenu(event.currentTarget, applicationState.source);

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
document.querySelector("#source-search").oninput = renderSources;
document.querySelector("#create").onclick = () => request("create");
document.querySelector("#retry-loading").onclick = loadApplication;
window.addEventListener("pywebviewready", loadApplication);
loadApplication();
render();
