"""Check the real desktop connection, retry and close using a temporary settings copy.

Run: python check_desktop.py --settings settings.json
"""

import argparse
import json
from pathlib import Path
import tempfile
import time

import webview

from branch_store import BranchStore
from resource_brancher import APP_DIRECTORY, DesktopApi


class RetryCheckApi(DesktopApi):
    def __init__(self, store):
        super().__init__(store)
        self._fail_once = True

    def request(self, action, value=None, previous=None):
        if action == "state" and self._fail_once:
            self._fail_once = False
            return {"ok": False, "error": "Simulated startup failure", "state": self._store.snapshot()}
        return super().request(action, value, previous)


def wait_until(window, expression):
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        try:
            if window.evaluate_js(expression):
                return
        except webview.errors.JavascriptException:
            pass
        time.sleep(0.1)
    raise AssertionError(f"Desktop check timed out: {expression}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--settings", type=Path)
    arguments = parser.parse_args()
    failures = []
    with tempfile.TemporaryDirectory(prefix="brancher-desktop-check-") as temporary:
        settings = Path(temporary) / "settings.json"
        if arguments.settings:
            settings.write_bytes(arguments.settings.read_bytes())
        api = RetryCheckApi(BranchStore(settings))
        api._window = webview.create_window("Resource Brancher desktop check", (APP_DIRECTORY / "ui" / "index.html").as_uri(),
                                            js_api=api, hidden=True, background_color="#0f1113")

        def check():
            try:
                wait_until(api._window, 'typeof window.pywebview?.api?.window_action === "function"')
                wait_until(api._window, '!document.querySelector("#retry-loading").hidden')
                api._window.evaluate_js('document.querySelector("#retry-loading").click()')
                wait_until(api._window, 'document.querySelector("#loading-screen").hidden')
                count = api._window.evaluate_js('Number(document.querySelector("#library-count").textContent)')
                assert count == len(api._store.profiles), "Saved source count differs"
                print(json.dumps({"saved_sources": count, "real_connection": "passed", "retry": "passed", "close": "requested"}), flush=True)
                api._window.evaluate_js('setTimeout(() => document.querySelector("[data-window=close]").click(), 50); true')
            except Exception as error:
                failures.append(error)
                api._window.destroy()

        webview.start(check, gui="edgechromium", private_mode=True)
        if failures:
            raise failures[0]
        print("Native desktop closed successfully.")


if __name__ == "__main__":
    main()
