"""Saved setups and history, independent of the desktop interface."""

from datetime import datetime
import json
from pathlib import Path

from junctions import create_branch, inspect_destination, source_path


class BranchStore:
    def __init__(self, settings_file):
        self.settings_file = Path(settings_file)
        self.profiles = {}
        self.history = []
        self.current_source = ""
        self.load()
        discovered = False
        for source, destinations in self.profiles.items():
            for destination in destinations:
                if inspect_destination(source, destination).linked:
                    discovered = self.record(source, destination, "found") or discovered
        if discovered:
            self.save()

    @property
    def destinations(self):
        return self.profiles.get(self.current_source, [])

    def load(self):
        try:
            data = json.loads(self.settings_file.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return
        # An unreadable settings file is kept intact rather than silently replaced.
        if not isinstance(data, dict):
            raise ValueError("settings.json must contain an object.")
        profiles = data.get("profiles", {})
        if isinstance(profiles, dict):
            self.profiles = {source: list(dict.fromkeys(destinations)) for source, destinations in profiles.items()
                             if isinstance(source, str) and isinstance(destinations, list)
                             and all(isinstance(destination, str) for destination in destinations)}
        history = data.get("history", [])
        if isinstance(history, list):
            self.history = [entry for entry in history if isinstance(entry, dict)
                            and all(isinstance(entry.get(field), str) for field in ("source", "destination", "recorded_at"))
                            and entry.get("action") in ("created", "found")]
        selected = data.get("last_source", "")
        if isinstance(selected, str) and selected in self.profiles:
            self.current_source = selected

    def save(self):
        temporary = self.settings_file.with_suffix(".tmp")
        temporary.write_text(json.dumps({"last_source": self.current_source, "profiles": self.profiles,
                                         "history": self.history}, indent=2), encoding="utf-8")
        temporary.replace(self.settings_file)

    def select_source(self, source):
        if not isinstance(source, str):
            raise ValueError("Choose a source folder.")
        # Saved sources may temporarily be disconnected; retain their setups.
        if source not in self.profiles:
            source = str(source_path(source))
        self.profiles.setdefault(source, [])
        self.current_source = source
        self.save()

    def remove_source(self, source):
        if source not in self.profiles:
            raise ValueError("That source is not in your saved folders.")
        del self.profiles[source]
        self.history = [entry for entry in self.history if Path(entry["source"]) != Path(source)]
        if self.current_source == source:
            self.current_source = next(iter(self.profiles), "")
        self.save()

    def add_destination(self, destination, previous=None):
        if not self.current_source:
            raise ValueError("Choose a source folder first.")
        if not isinstance(destination, str) or not destination.strip() or not Path(destination).is_absolute():
            raise ValueError("Enter a full destination path including its drive letter.")
        destination = str(Path(destination.strip()))
        if any(Path(existing) == Path(destination) for existing in self.destinations if existing != previous):
            raise ValueError("That destination is already in this setup.")
        if previous is not None:
            self.destinations[self.destinations.index(previous)] = destination
        else:
            self.destinations.append(destination)
        self.save()

    def remove_destination(self, destination):
        self.destinations.remove(destination)
        self.save()

    def record(self, source, destination, action):
        if action == "found" and any(Path(entry["source"]) == Path(source)
                                      and Path(entry["destination"]) == Path(destination) for entry in self.history):
            return False
        self.history.append({"source": source, "destination": destination, "action": action,
                             "recorded_at": datetime.now().astimezone().isoformat(timespec="seconds")})
        return True

    def create_branches(self):
        source_path(self.current_source)
        created = existing = blocked = 0
        for destination in self.destinations:
            try:
                status = create_branch(self.current_source, destination)
                if status.label == "Created":
                    created += 1
                    self.record(self.current_source, destination, "created")
                else:
                    existing += 1
                    self.record(self.current_source, destination, "found")
            except (OSError, ValueError):
                blocked += 1
        self.save()
        return f"{created} created · {existing} already linked · {blocked} blocked"

    def load_history(self, index):
        if index < 0 or index >= len(self.history):
            raise ValueError("That history entry no longer exists.")
        entry = self.history[index]
        self.profiles.setdefault(entry["source"], [])
        self.current_source = entry["source"]
        if not any(Path(destination) == Path(entry["destination"]) for destination in self.destinations):
            self.destinations.append(entry["destination"])
        self.save()

    @staticmethod
    def link_data(source, destination):
        status = inspect_destination(source, destination)
        return {"path": destination, "name": Path(destination).parent.name,
                "status": "linked" if status.linked else "ready" if status.ready else "blocked", "detail": status.label}

    def snapshot(self):
        history = []
        for index, entry in reversed(list(enumerate(self.history))):
            history.append({**entry, "id": index, "source_name": Path(entry["source"]).name,
                            "link": self.link_data(entry["source"], entry["destination"])})
        return {"source": self.current_source, "source_name": Path(self.current_source).name if self.current_source else "",
                "profiles": [{"path": source, "name": Path(source).name, "count": len(destinations)}
                             for source, destinations in self.profiles.items()],
                "destinations": [self.link_data(self.current_source, destination) for destination in self.destinations],
                "history": history}
