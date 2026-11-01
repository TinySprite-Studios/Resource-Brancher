"""Build the branded portable Windows application."""
from pathlib import Path
import subprocess
import sys
import os
import re
from PIL import Image

root = Path(__file__).resolve().parent.parent
tag = os.environ.get("RELEASE_TAG", "")
version = tag.removeprefix("v") if tag else (root / "VERSION").read_text().strip()
if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", version):
    raise ValueError("Version must have the form 1.0.1")
assets = root / "build"
assets.mkdir(exist_ok=True)
(assets / "VERSION").write_text(version)
icon = assets / "resource-brancher.ico"
with Image.open(root / "ui/assets/resource-brancher-logo.png") as image:
    image = image.convert("RGBA")
    image.thumbnail((256, 256))
    square = Image.new("RGBA", (256, 256))
    square.alpha_composite(image, ((256-image.width)//2, (256-image.height)//2))
    square.save(icon, sizes=[(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)])
subprocess.run([sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean",
    "--windowed", "--onedir", "--name", "Resource Brancher", "--icon", str(icon),
    "--add-data", "ui;ui", "--add-data", "scripts/apply-update.ps1;.", "--add-data", str(assets / "VERSION")+";.", "--add-data", str(icon)+";.",
    str(root / "resource_brancher.py")], cwd=root, check=True)
import shutil
shutil.make_archive(str(root / "dist" / f"Resource-Brancher-{version}-Windows"),
                    "zip", root / "dist" / "Resource Brancher")

compiler = shutil.which("ISCC.exe") or str(Path(os.environ.get("ProgramFiles(x86)", "C:/Program Files (x86)")) / "Inno Setup 6/ISCC.exe")
if not Path(compiler).is_file():
    raise RuntimeError("Install Inno Setup 6 to build the setup EXE")
subprocess.run([compiler, f"/DAppVersion={version}", str(root / "installer/resource-brancher.iss")], cwd=root, check=True)
