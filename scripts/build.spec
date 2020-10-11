# -*- mode: python -*-
import glob
import os
import platform
import sys

# noinspection PyPackageRequirements
from PyInstaller.building.build_main import Analysis, BUNDLE
# noinspection PyPackageRequirements
from PyInstaller.building.api import EXE, PYZ, COLLECT

ROOT_PATH = os.getcwd()
assert os.path.basename(ROOT_PATH) == "xappt_plugins"

sys.path.append(ROOT_PATH)

try:
    import xappt_plugins
    from xappt_plugins.__version__ import __version__ as xp_version
except ImportError:
    raise SystemExit("xappt_plugins not found. Be sure that you are running PyInstaller from the root directory")


APP_NAME = "xappt-plugins"
SYSTEM = platform.system()

BLOCK_CIPHER = None


def collect_packages(root_path):
    namespace = os.path.basename(root_path)
    modules = set()
    for root, dirs, files in os.walk(root_path):
        for f in files:
            if f.endswith(".pyc"):
                continue
            if f.startswith("__init__"):
                rel_path = os.path.relpath(root, root_path)
            else:
                file_name = os.path.splitext(f)[0]
                rel_path = os.path.relpath(os.path.join(root, file_name), root_path)
            mod_path = rel_path.replace(os.sep, ".")
            modules.add(f"{namespace}.{mod_path}")
    for module in modules:
        yield module


def load_path(path, dst_root):
    for root, dirs, files in os.walk(path):
        relpath = os.path.relpath(root, path)
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext in (".pyc", ):
                continue
            yield os.path.join(root, f), os.path.join(dst_root, relpath, f)


excluded_packages = []
required_files = list(load_path(
    os.path.abspath("../xappt_plugins/xappt_plugins/plugins/godot/templates"), "xappt_plugins"))
for req in required_files:
    print(req)
required_binaries = []
hidden_imports = []

if SYSTEM == "Windows":
    exe_path = os.path.dirname(sys.executable)
    for item in glob.glob(os.path.join(exe_path, "python*.dll")):
        required_binaries.append((item, "."))
    icon_path = os.path.abspath(r"resources\icons\appicon.ico")
elif SYSTEM == "Linux":
    icon_path = "../resources/icons/appicon.png"
elif SYSTEM == "Darwin":
    icon_path = "../resources/icons/appicon.icns"
else:
    raise NotImplementedError

a = Analysis(
    ['../xappt_plugins/main.py'],
    pathex=[],
    binaries=required_binaries,
    datas=required_files,
    hiddenimports=hidden_imports,
    hookspath=[],
    runtime_hooks=[],
    excludes=excluded_packages,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=BLOCK_CIPHER,
    noarchive=False)

pyz = PYZ(a.pure, cipher=BLOCK_CIPHER)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    exclude_binaries=False,
    name=APP_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=True,
    console=True,
    icon=icon_path)

# coll = COLLECT(
#     exe,
#     a.binaries,
#     a.zipfiles,
#     a.datas,
#     strip=False,
#     upx=True,
#     name='main')


if platform.system() == "Darwin":
    app = BUNDLE(
        exe,
        appname=APP_NAME,
        version=xp_version,
        name="{0}.app".format(APP_NAME),
        icon=icon_path
    )
