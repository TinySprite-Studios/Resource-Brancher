let updateBusy = false;
async function updateAction(action = "state") {
  if (!window.pywebview?.api || updateBusy) return;
  updateBusy = true;
  try {
    const state = await window.pywebview.api.update_action(action);
    const busy = ["checking", "downloading", "restarting"].includes(state.status);
    const messages = {idle: `Version ${state.current}`, checking: "Checking for updates…", downloading: "Downloading update…", available: `Version ${state.version} is available`, current: `Version ${state.current} is up to date`, ready: "Update ready. Restart to use it.", restarting: "Restarting…"};
    document.querySelector("#update-status").textContent = state.message || messages[state.status] || "Updates";
    document.querySelector("#update-check").disabled = busy || state.status === "disabled";
    document.querySelector("#update-download").hidden = state.status !== "available";
    document.querySelector("#update-install").hidden = state.status !== "ready";
  } catch (error) {
    document.querySelector("#update-status").textContent = "Could not update. Please check your connection and try again.";
    document.querySelector("#update-check").disabled = false;
  } finally { updateBusy = false; }
}
document.querySelector("#update-check").onclick = () => updateAction("check");
document.querySelector("#update-download").onclick = () => updateAction("download");
document.querySelector("#update-install").onclick = () => updateAction("install");
window.addEventListener("pywebviewready", () => updateAction("check"));
setInterval(() => updateAction(), 1000);
