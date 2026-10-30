"""Find installed folder editors without scanning drives or using a shell."""

import os
from pathlib import Path
import shutil
import subprocess
import winreg


EDITOR_DEFINITIONS = (
    ("vscode", "Visual Studio Code", "Code.exe", "Microsoft VS Code", ()),
    ("vscode-insiders", "VS Code Insiders", "Code - Insiders.exe", "Microsoft VS Code Insiders", ()),
    ("notepad-plus-plus", "Notepad++", "notepad++.exe", "Notepad++", ("-multiInst", "-nosession", "-openFoldersAsWorkspace")),
    ("cursor", "Cursor", "Cursor.exe", "cursor", ()),
    ("windsurf", "Windsurf", "Windsurf.exe", "Windsurf", ()),
    ("sublime", "Sublime Text", "sublime_text.exe", "Sublime Text", ()),
)


def registry_paths(executable_name):
    registry_key = rf"Software\Microsoft\Windows\CurrentVersion\App Paths\{executable_name}"
    for hive in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
        for view in (winreg.KEY_WOW64_64KEY, winreg.KEY_WOW64_32KEY):
            try:
                with winreg.OpenKey(hive, registry_key, 0, winreg.KEY_READ | view) as key:
                    value, _value_type = winreg.QueryValueEx(key, None)
                    if isinstance(value, str):
                        yield Path(os.path.expandvars(value.strip('"')))
            except OSError:
                continue


def detect_editors():
    detected = []
    for editor_id, label, executable_name, installation_folder, arguments in EDITOR_DEFINITIONS:
        candidates = list(registry_paths(executable_name))
        path_match = shutil.which(executable_name)
        if path_match:
            candidates.append(Path(path_match))
        for variable in ("LOCALAPPDATA", "ProgramFiles", "ProgramFiles(x86)"):
            location = os.environ.get(variable)
            if location:
                base = Path(location)
                candidates.extend((base / installation_folder / executable_name,
                                   base / "Programs" / installation_folder / executable_name))
        executable = next((candidate for candidate in candidates if candidate.suffix.lower() == ".exe" and candidate.is_file()), None)
        if executable:
            detected.append({"id": editor_id, "name": label, "executable": str(executable), "arguments": arguments})
    return detected


def open_in_editor(folder, editor_id):
    editor = next((editor for editor in detect_editors() if editor["id"] == editor_id), None)
    if not editor:
        raise ValueError("That editor is no longer available. Refresh the editor list.")
    subprocess.Popen([editor["executable"], *editor["arguments"], str(folder)], shell=False)
