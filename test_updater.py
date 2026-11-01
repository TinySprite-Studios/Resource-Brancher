import hashlib
import tempfile
import unittest
import zipfile
from pathlib import Path
from updater import select_release, extract_verified, BASE

class UpdateTests(unittest.TestCase):
    def release(self, tag="v1.0.1"):
        name=f"Resource-Brancher-{tag[1:]}-Windows.zip"
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
    def test_archive(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder); archive=root/"update.zip"
            with zipfile.ZipFile(archive,"w") as z:z.writestr("Resource Brancher.exe",b"example")
            digest=hashlib.sha256(archive.read_bytes()).hexdigest()
            extract_verified(archive,root/"valid",digest)
            self.assertTrue((root/"valid/Resource Brancher.exe").exists())
            with self.assertRaises(ValueError):extract_verified(archive,root/"bad","0"*64)
            with zipfile.ZipFile(archive,"w") as z:
                z.writestr("Resource Brancher.exe",b"example")
                z.writestr("../escape",b"bad")
            with self.assertRaises(ValueError):extract_verified(archive,root/"unsafe",hashlib.sha256(archive.read_bytes()).hexdigest())
