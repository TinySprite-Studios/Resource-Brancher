"""Run with: python -m unittest -v test_brancher"""

import os
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from junctions import BranchError, create_branch, inspect_destination, is_junction
from branch_store import BranchStore
from resource_brancher import DesktopApi


class BrancherTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="resource-brancher-test-")
        self.workspace = Path(self.temporary.name).resolve()
        self.source = self.workspace / "Source & 100% original"
        self.source.mkdir()
        self.junctions = []

    def tearDown(self):
        # Unlink only the junctions this test created, before cleaning its temp folder.
        for destination in reversed(self.junctions):
            if is_junction(destination):
                os.rmdir(destination)
        self.temporary.cleanup()

    def make_branch(self, destination, source=None):
        self.junctions.append(destination)
        return create_branch(source or self.source, destination)

    def test_multiple_locations_share_edits_and_deletes(self):
        first = self.workspace / "Server one"
        second = self.workspace / "Server two"
        self.assertEqual(self.make_branch(first).label, "Created")
        self.make_branch(second)
        (first / "example.txt").write_text("shared", encoding="utf-8")
        self.assertEqual((second / "example.txt").read_text(encoding="utf-8"), "shared")
        (second / "example.txt").unlink()
        self.assertFalse((self.source / "example.txt").exists())
        self.assertEqual(create_branch(self.source, first).label, "Already linked")

    def test_existing_folder_and_file_are_preserved(self):
        existing = self.workspace / "Existing"
        existing.mkdir()
        sentinel = existing / "keep.txt"
        sentinel.write_text("keep", encoding="utf-8")
        for destination in (existing, sentinel):
            with self.assertRaises(BranchError):
                create_branch(self.source, destination)
        self.assertEqual(sentinel.read_text(encoding="utf-8"), "keep")

    def test_wrong_and_broken_links_are_preserved(self):
        other = self.workspace / "Other source"
        other.mkdir()
        destination = self.workspace / "Other branch"
        self.make_branch(destination, other)
        with self.assertRaises(BranchError):
            create_branch(self.source, destination)
        other.rmdir()
        self.assertTrue(os.path.lexists(destination))
        with self.assertRaises(BranchError):
            create_branch(self.source, destination)
        self.assertTrue(is_junction(destination))

    def test_cycles_and_missing_parents_are_blocked(self):
        for destination in (self.source, self.source / "Nested", self.workspace,
                            self.workspace / "Missing" / "Branch"):
            self.assertFalse(inspect_destination(self.source, destination).ready)
        indirect = self.workspace / "Indirect"
        self.make_branch(indirect)
        self.assertFalse(inspect_destination(self.source, indirect / "Nested").ready)

    def test_failed_creation_rolls_back_only_empty_destination(self):
        destination = self.workspace / "Failed"
        with patch("junctions._set_junction", side_effect=OSError("Test failure")):
            with self.assertRaises(OSError):
                create_branch(self.source, destination)
        self.assertFalse(destination.exists())
        self.assertTrue(self.source.is_dir())

    def test_setups_history_and_restore(self):
        settings = self.workspace / "settings.json"
        destination = self.workspace / "UI branch"
        self.junctions.append(destination)
        store = BranchStore(settings)
        store.select_source(str(self.source))
        store.add_destination(str(destination))
        self.assertIn("1 created", store.create_branches())
        self.assertTrue(is_junction(destination))
        self.assertEqual(len(store.history), 1)
        store.create_branches()
        self.assertEqual(len(store.history), 1)
        other = self.workspace / "Second source"
        other.mkdir()
        store.select_source(str(other))
        self.assertEqual(store.destinations, [])
        store.select_source(str(self.source))
        restored = BranchStore(settings)
        self.assertEqual(restored.destinations, [str(destination)])
        self.assertEqual(restored.history[0]["action"], "created")
        restored.remove_destination(str(destination))
        self.assertEqual(len(restored.history), 1)
        self.assertTrue(is_junction(destination))
        os.rmdir(destination)
        self.assertEqual(restored.snapshot()["history"][0]["link"]["status"], "ready")
        restored.load_history(0)
        self.assertEqual(restored.destinations, [str(destination)])
        self.assertFalse(destination.exists())

    def test_previous_saved_links_are_discovered_once(self):
        destination = self.workspace / "Earlier branch"
        self.make_branch(destination)
        settings = self.workspace / "old-settings.json"
        settings.write_text(json.dumps({"last_source": str(self.source),
                                        "profiles": {str(self.source): [str(destination)]}}), encoding="utf-8")
        store = BranchStore(settings)
        self.assertEqual(len(store.history), 1)
        self.assertEqual(store.history[0]["action"], "found")
        restored = BranchStore(settings)
        self.assertEqual(len(restored.history), 1)
        self.assertEqual(restored.destinations, [str(destination)])

    def test_desktop_api_and_editing_destinations(self):
        store = BranchStore(self.workspace / "settings.json")
        api = DesktopApi(store)
        self.assertFalse(api.request("save_destination", "relative") ["ok"])
        self.assertTrue(api.request("select_source", str(self.source))["ok"])
        first = str(self.workspace / "First branch")
        second = str(self.workspace / "Second branch")
        self.assertTrue(api.request("save_destination", first)["ok"])
        self.assertTrue(api.request("save_destination", second, first)["ok"])
        self.assertEqual(store.destinations, [second])
        self.assertFalse(api.request("save_destination", second)["ok"])
        self.assertFalse(api.request("unknown")["ok"])
        self.assertFalse((self.workspace / "Second branch").exists())

    def test_folder_picker_edits_setup_without_moving_existing_link(self):
        store = BranchStore(self.workspace / "settings.json")
        store.select_source(str(self.source))
        destination = self.workspace / "Original branch"
        self.make_branch(destination)
        store.add_destination(str(destination))
        new_parent = self.workspace / "New location"
        new_parent.mkdir()
        api = DesktopApi(store)
        api.window = Mock()
        api.window.create_file_dialog.return_value = (str(new_parent),)
        result = api.request("edit_destination", str(destination))
        self.assertTrue(result["ok"])
        self.assertEqual(store.destinations, [str(new_parent / destination.name)])
        self.assertTrue(is_junction(destination))
        self.assertFalse((new_parent / destination.name).exists())
        api.window.create_file_dialog.return_value = None
        self.assertTrue(api.request("edit_destination", store.destinations[0])["ok"])
        self.assertEqual(store.destinations, [str(new_parent / destination.name)])

    def test_open_folder_and_missing_destination_status(self):
        store = BranchStore(self.workspace / "settings.json")
        store.select_source(str(self.source))
        destination = self.workspace / "Explorer branch"
        self.make_branch(destination)
        store.add_destination(str(destination))
        api = DesktopApi(store)
        with patch("resource_brancher.os.startfile") as open_folder:
            self.assertTrue(api.request("open_folder", str(self.source))["ok"])
            self.assertTrue(api.request("open_folder", str(destination))["ok"])
            self.assertEqual(open_folder.call_count, 2)
            os.rmdir(destination)
            self.assertFalse(api.request("open_folder", str(destination))["ok"])
            self.assertEqual(open_folder.call_count, 2)
            self.assertEqual(api.request("state")["state"]["destinations"][0]["status"], "ready")


if __name__ == "__main__":
    unittest.main()
