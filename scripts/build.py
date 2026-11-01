"""Build the branded portable Windows application."""
from pathlib import Path
import subprocess
import sys
from PIL import Image

root = Path(__file__).resolve().parent.parent
version = (root / "VERSION").read_text().strip()
assets = root / "build"
assets.mkdir(exist_ok=True)
icon = assets / "resource-brancher.ico"
with Image.open(root / "ui/assets/resource-brancher-logo.png") as image:
    image = image.convert("RGBA")
    image.thumbnail((256, 256))
    square = Image.new("RGBA", (256, 256))
    square.alpha_composite(image, ((256-image.width)//2, (256-image.height)//2))
    square.save(icon, sizes=[(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)])
subprocess.run([sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean",
    "--windowed", "--onedir", "--name", "Resource Brancher", "--icon", str(icon),
    "--add-data", "ui;ui", "--add-data", str(icon)+";.",
    str(root / "resource_brancher.py")], cwd=root, check=True)
import shutil
shutil.make_archive(str(root / "dist" / f"Resource-Brancher-{version}-Windows"),
                    "zip", root / "dist" / "Resource Brancher")
