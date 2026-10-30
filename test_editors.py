"""Editor discovery and launching, without opening any real editor."""

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from branch_store import BranchStore
from editors import detect_editors, open_in_editor
from resource_brancher import DesktopApi


class EditorTests(unittest.TestCase):
    def test_common_install_folder_detection(self):
        with tempfile.TemporaryDirectory() as temporary:
            executable = Path(temporary) / "Programs" / "Microsoft VS Code" / "Code.exe"
            executable.parent.mkdir(parents=True)
            executable.touch()
            with patch("editors.registry_paths", return_value=[]), patch("editors.shutil.which", return_value=None), patch.dict("os.environ", {"LOCALAPPDATA": temporary}, clear=True):
                editors = detect_editors()
            self.assertEqual([editor["id"] for editor in editors], ["vscode"])
            self.assertEqual(editors[0]["executable"], str(executable))

    def test_launch_keeps_folder_as_single_argument(self):
        editor = {"id": "notepad-plus-plus", "executable": r"C:\Editors\notepad++.exe",
                  "arguments": ("-multiInst", "-nosession", "-openFoldersAsWorkspace")}
        folder = Path(r"C:\Resources\Spaces & symbols")
        with patch("editors.detect_editors", return_value=[editor]), patch("editors.subprocess.Popen") as launch:
            open_in_editor(folder, editor["id"])
            launch.assert_called_once_with([editor["executable"], *editor["arguments"], str(folder)], shell=False)
            with self.assertRaises(ValueError):
                open_in_editor(folder, "unknown-editor")
            self.assertEqual(launch.call_count, 1)

    def test_api_only_opens_saved_existing_folders(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "Source"
            source.mkdir()
            source = source.resolve()
            store = BranchStore(Path(temporary) / "settings.json")
            store.select_source(str(source))
            api = DesktopApi(store)
            with patch("resource_brancher.open_in_editor") as launch:
                self.assertTrue(api.request("open_with", str(source), "vscode")["ok"])
                launch.assert_called_once_with(source, "vscode")
                self.assertFalse(api.request("open_with", temporary, "vscode")["ok"])
                self.assertEqual(launch.call_count, 1)


if __name__ == "__main__":
    unittest.main()
