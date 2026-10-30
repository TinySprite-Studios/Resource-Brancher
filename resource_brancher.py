"""Resource Brancher's desktop shell and folder-picker API."""

import logging
import os
from pathlib import Path
import threading

from branch_store import BranchStore
from editors import detect_editors, open_in_editor


APP_DIRECTORY = Path(__file__).resolve().parent
DEFAULT_SOURCE_DIRECTORY = Path.home()


class DesktopApi:
    def __init__(self, store):
        self._store = store
        self._window = None
        self._lock = threading.RLock()
        self._maximized = False

    def request(self, action, value=None, previous=None):
        """Expose only the operations needed by the local interface."""
        with self._lock:
            try:
                message = ""
                if action == "choose_source":
                    import webview
                    current = Path(self._store.current_source) if self._store.current_source else DEFAULT_SOURCE_DIRECTORY
                    selected = self._window.create_file_dialog(webview.FileDialog.FOLDER,
                                                              directory=str(current) if current.is_dir() else "")
                    if selected:
                        self._store.select_source(selected[0])
                elif action == "select_source":
                    self._store.select_source(value)
                elif action == "remove_source":
                    self._store.remove_source(value)
                elif action == "toggle_favourite":
                    options = self._store.source_options.get(value, {})
                    self._store.update_source_option(value, "favourite", not options.get("favourite", False))
                elif action == "set_group":
                    self._store.update_source_option(value, "group", previous)
                elif action == "choose_destination":
                    import webview
                    if not self._store.current_source:
                        raise ValueError("Choose a source folder first.")
                    selected = self._window.create_file_dialog(webview.FileDialog.FOLDER)
                    if selected:
                        self._store.add_destination(str(Path(selected[0]) / Path(self._store.current_source).name))
                elif action == "edit_destination":
                    import webview
                    if value not in self._store.destinations:
                        raise ValueError("That destination is not in this setup.")
                    destination = Path(value)
                    selected = self._window.create_file_dialog(
                        webview.FileDialog.FOLDER,
                        directory=str(destination.parent) if destination.parent.is_dir() else "",
                    )
                    if selected:
                        self._store.add_destination(str(Path(selected[0]) / destination.name), value)
                elif action == "editors":
                    return {"ok": True, "editors": [{"id": editor["id"], "name": editor["name"]} for editor in detect_editors()]}
                elif action in ("open_folder", "open_with"):
                    known_paths = set(self._store.profiles)
                    for destinations in self._store.profiles.values():
                        known_paths.update(destinations)
                    if value not in known_paths or not Path(value).is_dir():
                        raise ValueError("This folder is no longer available.")
                    if action == "open_with":
                        open_in_editor(Path(value), previous)
                    else:
                        os.startfile(str(Path(value)))
                elif action == "save_destination":
                    self._store.add_destination(value, previous)
                elif action == "remove_destination":
                    self._store.remove_destination(value)
                elif action == "create":
                    message = self._store.create_branches()
                elif action == "load_history":
                    self._store.load_history(int(value))
                elif action != "state":
                    raise ValueError("That action is not available.")
                return {"ok": True, "state": self._store.snapshot(), "message": message}
            except (OSError, ValueError) as error:
                return {"ok": False, "error": str(error), "state": self._store.snapshot()}

    def window_action(self, action):
        if action == "close":
            self._window.destroy()
        elif action == "minimize":
            self._window.minimize()
        elif action == "maximize":
            if self._maximized:
                self._window.restore()
            else:
                self._window.maximize()
            self._maximized = not self._maximized


def main():
    import webview

    store = BranchStore(APP_DIRECTORY / "settings.json")
    api = DesktopApi(store)
    api._window = webview.create_window(
        "Resource Brancher", (APP_DIRECTORY / "ui" / "index.html").as_uri(),
        js_api=api, width=1250, height=820, min_size=(980, 680),
        frameless=True, easy_drag=False, shadow=True, background_color="#0f1113",
    )
    webview.start(gui="edgechromium", private_mode=True)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        logging.basicConfig(filename=APP_DIRECTORY / "brancher-error.log", encoding="utf-8", level=logging.ERROR)
        logging.exception("Resource Brancher could not start")
        import ctypes
        ctypes.windll.user32.MessageBoxW(None, "Could not open Resource Brancher. See brancher-error.log in the program folder.",
                                        "Resource Brancher", 0x10)
