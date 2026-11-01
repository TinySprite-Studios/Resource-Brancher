"""GitHub release checks and verified, staged Windows updates."""
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import urllib.request
import os
from pathlib import Path

REPOSITORY = "TinySprite-Studios/Resource-Brancher"
BASE = f"https://github.com/{REPOSITORY}/releases/download/"

def version_tuple(value):
    if not re.fullmatch(r"v?[0-9]+\.[0-9]+\.[0-9]+", value):
        raise ValueError("Unsupported release version")
    return tuple(map(int, value.removeprefix("v").split(".")))

def select_release(data, current):
    tag = data.get("tag_name", "")
    version_tuple(tag)
    tag = "v" + tag.removeprefix("v")
    if data.get("draft") or data.get("prerelease") or version_tuple(tag) <= version_tuple(current):
        return None
    name = f"Resource-Brancher-Setup-{tag[1:]}.exe"
    asset = next((a for a in data.get("assets", []) if a.get("name") == name), None)
    if not asset or asset.get("browser_download_url") != BASE + tag + "/" + name:
        raise ValueError("The release has no compatible Windows download yet")
    digest = asset.get("digest", "")
    if not re.fullmatch(r"sha256:[a-fA-F0-9]{64}", digest):
        raise ValueError("The release is missing its download checksum")
    return {"version": tag[1:], "url": asset["browser_download_url"], "digest": digest[7:]}

def verify_download(path, digest):
    checksum = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            checksum.update(chunk)
    if checksum.hexdigest().lower() != digest.lower():
        raise ValueError("Download checksum did not match. Please try again")

class Updater:
    def __init__(self, root, data):
        self.root, self.data = Path(root), Path(data)
        self.current = (self.root / "VERSION").read_text().strip()
        self.state = {"status": "idle", "current": self.current}
        self.release = None
        self.stage = None
        self.lock = threading.Lock()

    def action(self, action):
        if action == "state":
            return dict(self.state)
        if not getattr(sys, "frozen", False):
            return {**self.state, "status": "disabled", "message": "Updates are available in the built EXE. Source copies are updated through Git."}
        if action not in ("check", "download"):
            raise ValueError("Unknown update action")
        if not self.lock.acquire(False):
            return dict(self.state)
        if action == "download" and (not self.release or self.state["status"] != "available"):
            self.lock.release()
            return dict(self.state)
        self.state.update(status="checking" if action == "check" else "downloading", message="")
        threading.Thread(target=self._work, args=(action,), daemon=True).start()
        return dict(self.state)

    def _work(self, action):
        try:
            if action == "check":
                req = urllib.request.Request(f"https://api.github.com/repos/{REPOSITORY}/releases/latest", headers={"User-Agent": "Resource-Brancher", "Accept": "application/vnd.github+json"})
                with urllib.request.urlopen(req, timeout=20) as response:
                    self.release = select_release(json.load(response), self.current)
                self.state.update(status="available" if self.release else "current", version=self.release["version"] if self.release else self.current)
            else:
                self.data.mkdir(parents=True, exist_ok=True)
                folder = Path(tempfile.mkdtemp(prefix="update-", dir=self.data))
                archive = folder / "setup.exe"
                req = urllib.request.Request(self.release["url"], headers={"User-Agent": "Resource-Brancher"})
                with urllib.request.urlopen(req, timeout=60) as response, archive.open("wb") as output:
                    shutil.copyfileobj(response, output)
                verify_download(archive, self.release["digest"])
                self.stage = archive
                self.state.update(status="ready")
        except Exception as error:
            self.state.update(status="error", message=str(error))
        finally:
            self.lock.release()

    def install(self):
        if self.state["status"] != "ready" or not self.stage:
            raise ValueError("Download an update first")
        verify_download(self.stage, self.release["digest"])
        executable_directory = Path(sys.executable).resolve().parent
        installed = (executable_directory / "installed.marker").is_file()
        helper = self.stage.parent / "apply-update.ps1"
        shutil.copy2(self.root / "apply-update.ps1", helper)
        command = ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
                          "-File", str(helper), "-AppProcessId", str(os.getpid()),
                          "-Installer", str(self.stage),
                          "-LogFile", str(self.stage.parent / "install.log")]
        if installed:
            command.extend(["-InstallDirectory", str(executable_directory)])
        subprocess.Popen(command, creationflags=subprocess.CREATE_NO_WINDOW)
        return True
