import json
import logging
import os
import pathlib
import shutil

# noinspection PyPackageRequirements
from Crypto.Cipher import AES
# noinspection PyPackageRequirements
from Crypto.Random import get_random_bytes

import xappt

from xappt_plugins.plugins.godot import templates
from xappt_plugins.validators import *
from xappt_plugins.utilities import open_file

logger = logging.getLogger("xappt")


@xappt.register_plugin
class NewProject(xappt.BaseTool):
    project_name = xappt.ParamString(required=True, default="my_project",
                                     description="What should the new project be called?")
    project_path = xappt.ParamString(options={'short_name': "p", "ui": "folder-select"},
                                     default=os.getcwd(),
                                     description="Where should the project be created?",
                                     validators=[ValidateFolderExists])
    git = xappt.ParamBool(options={'short_name': "g"},
                          description="Initialize a git repository in the project folder?")
    encryption = xappt.ParamBool(options={'short_name': "e"},
                                 description="Enable encryption for the project?")
    godot_version = xappt.ParamString(options={'short_name': "v"}, default="3.2.3-stable",
                                      choices=templates.get_templates("godot"),
                                      description="Which version of Godot do you want to target?")
    gdnative = xappt.ParamBool(options={'short_name': "n"},
                               description="Include GDNative C++ support?")
    class_name = xappt.ParamString(options={'short_name': "c"}, default="GDExample",
                                   description="What should the GDNative class be called?")

    def __init__(self, interface: xappt.BaseInterface, **kwargs):
        super().__init__(interface=interface, **kwargs)
        self.template_vars = {
            "TEMPLATE_NAME": "",
            "PROJECT_NAME": "",
            "EXPORT_PATH_REL": "",
            "ENCRYPTION_KEY": "",
            "GDNATIVE": "",
        }

    @classmethod
    def name(cls) -> str:
        return "new-project"

    @classmethod
    def help(cls) -> str:
        return "Create a new Godot project from a template with optional encryption and GDNative starter files."

    @classmethod
    def collection(cls) -> str:
        return "Godot"

    @staticmethod
    def _initialize_git_repository(output_path):
        cmd = xappt.CommandRunner()
        cmd.run(("git", "init"), cwd=output_path)
        with open(os.path.join(output_path, ".gitignore"), "w", newline="\n") as fp:
            fp.write(".idea/\n")
            fp.write("venv*/\n")
            fp.write("export/\n")

    def _initialize_gdnative(self, output_path: str):
        self._unpack_template("gdnative", "scons", output_path)

        def dst_name_callback(name: str) -> str:
            file_path, file_name = os.path.split(name)
            file_name = file_name.replace("gdexample", self.template_vars['CLASS_NAME'].lower())
            return os.path.join(file_path, file_name)

        source_path = os.path.join(output_path, "src")
        os.makedirs(source_path, exist_ok=True)
        self._unpack_template("gdnative", "cpp", source_path, dst_callback=dst_name_callback)

        godot_gdnative_path = os.path.join(output_path, "project", "bin")
        os.makedirs(godot_gdnative_path, exist_ok=True)
        self._unpack_template("gdnative", "gdns", godot_gdnative_path, dst_callback=dst_name_callback)

        scripts_path = os.path.join(output_path, "scripts")
        os.makedirs(scripts_path, exist_ok=True)
        self._unpack_template("gdnative", "scripts", scripts_path, dst_callback=dst_name_callback)

        cmd = xappt.CommandRunner(cwd=output_path)

        if self.git.value:
            cmd.run(("git", "submodule", "add", "https://github.com/GodotNativeTools/godot-cpp"))
        else:
            cmd.run(("git", "clone", "--recursive", "https://github.com/GodotNativeTools/godot-cpp", "godot-cpp"))

        cmd.run(("git", "submodule", "update", "--init", "--recursive"))

    @staticmethod
    def _generate_aes_256_cbc_key():
        key = get_random_bytes(32)
        aes_256_cbc = AES.new(key, AES.MODE_CBC)
        return aes_256_cbc.encrypt(key).hex().upper()

    def _unpack_template(self, category: str, key: str, target_path: str, **kwargs):
        alt = kwargs.get("alternative")
        dst_name_cb = kwargs.get("dst_callback", lambda x: x)
        for t in templates.get_template_files(category, key, alternative=alt):
            src = t.source
            dst = dst_name_cb(os.path.normpath(os.path.join(target_path, t.target)))
            if t.text_mode:
                with open(src, "r") as fp_in:
                    with open(dst, "w") as fp_out:
                        contents = fp_in.read()
                        for key, value in self.template_vars.items():
                            contents = contents.replace(f"{{{key.upper()}}}", value)
                            contents = contents.replace(f"{{{key.upper()}!u}}", value.upper())
                            contents = contents.replace(f"{{{key.upper()}!l}}", value.lower())
                        fp_out.write(contents)
            else:
                shutil.copy2(src, dst)
            os.chmod(dst, t.permissions)

    def _generate_godot_project(self, godot_version, project_path):
        if len(self.template_vars['ENCRYPTION_KEY']):
            alt = "encryption"
        else:
            alt = None
        self._unpack_template("godot", godot_version, project_path, alternative=alt)

    def _generate_manifest(self, output_path):
        with open(os.path.join(output_path, "project.manifest"), "w", newline="\n") as fp:
            json.dump(self.template_vars, fp, indent=2)

    def execute(self, **kwargs) -> int:
        source_path = self.project_path.value
        project_name = self.project_name.value
        project_path = os.path.join(source_path, project_name)
        if os.path.exists(project_path):
            self.interface.message(f"Error: path '{project_path}' exists")
            return 1

        template_name = self.godot_version.value

        self.template_vars['TEMPLATE_NAME'] = template_name
        self.template_vars['PROJECT_NAME'] = project_name
        self.template_vars['EXPORT_PATH_REL'] = "../export"

        self.interface.progress_start()

        self.interface.progress_update(f"Creating {project_path}", 0.0)

        godot_project_path = os.path.join(project_path, "project")
        os.makedirs(godot_project_path, exist_ok=True)
        os.makedirs(os.path.join(project_path, "export"), exist_ok=True)
        os.makedirs(os.path.join(project_path, "resources"), exist_ok=True)

        pathlib.Path(os.path.join(project_path, "export", ".gitkeep")).touch()
        pathlib.Path(os.path.join(project_path, "resources", ".gitkeep")).touch()

        if self.encryption.value:
            self.interface.progress_update("Generating encryption key", 0.1)
            enc_key = self._generate_aes_256_cbc_key()
            self.template_vars['ENCRYPTION_KEY'] = enc_key

        self.interface.progress_update(f"Generating project", 0.2)
        self._generate_godot_project(template_name, godot_project_path)

        if self.git.value:
            self.interface.progress_update("Initializing git", 0.3)
            self._initialize_git_repository(project_path)

        if self.gdnative.value:
            self.interface.progress_update("Generating GDNative", 0.4)
            self.template_vars['GDNATIVE'] = "true"
            self.template_vars['CLASS_NAME'] = self.class_name.value
            self._initialize_gdnative(project_path)

        self.interface.progress_update("Generating manifest", 0.5)
        self._generate_manifest(project_path)

        self.interface.progress_end()

        if self.interface.ask("Process complete.\n\nOpen project folder?"):
            open_file(project_path)

        return 0
