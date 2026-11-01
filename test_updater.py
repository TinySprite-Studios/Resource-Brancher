import hashlib
import tempfile
import unittest
import sys
from unittest.mock import patch
from updater import Updater
from pathlib import Path
from updater import select_release, verify_download, BASE

class UpdateTests(unittest.TestCase):
    def release(self, tag="v1.0.1"):
        name=f"Resource-Brancher-Setup-{tag[1:]}.exe"
        return {"tag_name":tag,"assets":[{"name":name,"browser_download_url":BASE+tag+"/"+name,"digest":"sha256:"+"a"*64}]}
    def test_versions(self):
        self.assertIsNone(select_release(self.release(), "1.0.1"))
        self.assertIsNone(select_release(self.release(), "2.0.0"))
        self.assertEqual(select_release(self.release("v1.0.10"), "1.0.9")["version"], "1.0.10")
    def test_prerelease(self):
        data=self.release(); data["prerelease"]=True
        self.assertIsNone(select_release(data,"1.0.0"))
    def test_untrusted_download(self):
        data=self.release(); data["assets"][0]["browser_download_url"]="https://example.com/app.zip"
        with self.assertRaises(ValueError):select_release(data,"1.0.0")
    def test_missing_checksum(self):
        data=self.release(); data["assets"][0].pop("digest")
        with self.assertRaises(ValueError):select_release(data,"1.0.0")
    def test_download_checksum(self):
        with tempfile.TemporaryDirectory() as folder:
            file=Path(folder)/"setup.exe"; file.write_bytes(b"installer")
            verify_download(file,hashlib.sha256(file.read_bytes()).hexdigest())
            with self.assertRaises(ValueError):verify_download(file,"0"*64)

    def test_installer_launch_targets_existing_install(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder); (root/"VERSION").write_text("1.0.0")
            (root/"apply-update.ps1").write_text("# helper")
            (root/"installed.marker").write_text("installed")
            (root/"download").mkdir()
            setup=root/"download/setup.exe"; setup.write_bytes(b"installer")
            updater=Updater(root,root)
            updater.stage=setup
            updater.release={"digest":hashlib.sha256(setup.read_bytes()).hexdigest()}
            updater.state["status"]="ready"
            with patch.object(sys,"executable",str(root/"Resource Brancher.exe")), patch("updater.subprocess.Popen") as launch, patch("updater.subprocess.CREATE_NO_WINDOW",0):
                updater.install()
                args=launch.call_args.args[0]
                self.assertEqual(args[args.index("-InstallDirectory")+1], str(root.resolve()))
                self.assertEqual(args[args.index("-Installer")+1], str(setup))
    def test_install_requires_download(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder); (root/"VERSION").write_text("1.0.0")
            with self.assertRaises(ValueError):Updater(root,root).install()
