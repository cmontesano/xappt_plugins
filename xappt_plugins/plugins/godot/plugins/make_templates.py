import json
import os
import re
import shutil

from typing import Callable, Generator, Optional, Sequence

import xappt
import xappt_qt

from xappt_plugins.validators import *
from xappt_plugins.utilities import open_file


class ValidateProjectManifest(xappt.BaseValidator):
    def validate(self, value: str) -> str:
        value = os.path.abspath(value)
        if os.path.basename(value).lower() != "project.manifest":
            raise xappt.ParameterValidationError("File must be named 'project.manifest'.")
        return value


NAME_MAPPING = (
    # templates
    ('godot.osx.opt.64', 'godot_osx_release.64'),
    ('godot.osx.opt.debug.64', 'godot_osx_debug.64'),
    ('godot.windows.opt.64.exe', 'windows_64_release.exe'),
    ('godot.windows.opt.debug.64.exe', 'windows_64_debug.exe'),
    ('godot.windows.opt.32.exe', 'windows_32_release.exe'),
    ('godot.windows.opt.debug.32.exe', 'windows_32_debug.exe'),
    ('godot.x11.opt.64', 'linux_x11_64_release'),
    ('godot.x11.opt.debug.64', 'linux_x11_64_debug'),
    # editor
    ('godot.x11.opt.tools.64', 'godot.x11.opt.tools.64'),
    ('godot.windows.opt.tools.64.exe', 'godot.windows.opt.tools.64.exe'),
    ('godot.windows.opt.tools.32.exe', 'godot.windows.opt.tools.32.exe'),
    ('godot.osx.opt.tools.64', 'godot.osx.opt.tools.64'),
)

BUILD_COMMANDS = {
    "windows": [
        {
            "strip_command": {
                "bin": "x86_64-w64-mingw32-strip",
                "regex": r"^.*64\.exe$",
            },
            "command": ("scons", "-j8", "platform=windows", "use_mingw=yes", "tools=no",
                        "target={target}", "bits=64", "use_lto=yes"),
            "targets": ("release", "release_debug"),
            "editor": ("scons", "-j8", "platform=windows", "use_mingw=yes",
                       "target=release_debug", "bits=64", "use_lto=yes"),
        },
        {
            "strip_command": {
                "bin": "i686-w64-mingw32-strip",
                "regex": r"^.*32\.exe$",
            },
            "command": ("scons", "-j8", "platform=windows", "use_mingw=yes", "tools=no",
                        "target={target}", "bits=32", "use_lto=yes"),
            "targets": ("release", "release_debug"),
            "editor": ("scons", "-j8", "platform=windows", "use_mingw=yes",
                       "target=release_debug", "bits=32", "use_lto=yes"),
        },
    ],
    "osx": {
        "strip_command": {
            "bin": '{OSXCROSS_ROOT}/target/bin/x86_64-apple-darwin15-strip',
            "regex": r"^.*\.osx\..*\.64$",
        },
        "targets": ("release", "release_debug"),
        "command": ("scons", "-j8", "platform=osx", "osxcross_sdk=darwin15", "tools=no", "target={target}", "bits=64"),
        "editor": ("scons", "-j8", "platform=osx", "osxcross_sdk=darwin15", "target=release_debug", "bits=64"),
    },
    "linux": {
        "strip_command": {
            "bin": "strip",
            "regex": r"^.*\.x11\..*\.64$",
        },
        "targets": ("release", "release_debug"),
        "command": ("scons", "-j8", "platform=x11", "tools=no", "target={target}", "bits=64"),
        "editor": ("scons", "-j8", "platform=x11", "target=release_debug", "bits=64"),
    },
    "android": {
        "name_match": r"^.*\.(?:apk|zip)$",
        "targets": ("release", "release_debug"),
        "command": ("scons", "-j8", "platform=android", "target={target}", "android_arch={arch}"),
        "architectures": ("armv7", "arm64v8", "x86", "x86_64"),
        "post_target_commands": [
            {
                "command": ("./gradlew", "generateGodotTemplates"),
                "cwd": "{cwd}/platform/android/java",
            }
        ],
    },
}

GODOT_MODULES = {
    "smooth": {
        "repository": "https://github.com/lawnjelly/godot-smooth",
        "src-folder": ".",
        "dst-folder": "smooth",
    },
}


@xappt.register_plugin
class MakeTemplates(xappt.BaseTool):
    manifest_path = xappt.ParamString(options={"ui": "file-open"},
                                      default=os.path.join(os.getcwd(), "project.manifest"),
                                      description="Where is the target project.manifest?",
                                      validators=[ValidateFileExists, ValidateProjectManifest])
    platform = xappt.ParamList(options={'short_name': "p"},
                               choices=("windows", "android", "linux", "osx"),
                               description="For which platforms should templates be built?")
    strip = xappt.ParamBool(options={'short_name': "s"},
                            description="Should symbols be stripped from binaries?")
    tools = xappt.ParamBool(options={'short_name': "t"},
                            description="Should the editor tools also be built?")
    modules = xappt.ParamList(options={'short_name': "m"}, choices=list(GODOT_MODULES.keys()),
                              description="Which third party modules should be included?")

    def __init__(self):
        super().__init__()
        self.cmd = xappt.CommandRunner()
        self.stdout_fn: Optional[Callable] = None
        self.stderr_fn: Optional[Callable] = None

    @classmethod
    def name(cls) -> str:
        return "make-templates"

    @classmethod
    def help(cls) -> str:
        return "Build Godot binaries and export templates for a project created with the `new-project` plugin."

    @classmethod
    def collection(cls) -> str:
        return "Godot"

    def _build_platform_template(self, **kwargs):
        cwd = kwargs['cwd']
        bin_path = os.path.join(cwd, "bin")
        output_path = kwargs['output_path']
        targets = kwargs['targets']
        architectures = kwargs.get('architectures', [])
        post_target_commands = kwargs.get('post_target_commands', [])
        command = kwargs['command']
        build_editor = self.tools.value

        os.makedirs(output_path, exist_ok=True)

        if len(architectures) == 0:
            architectures = [None]

        variables = kwargs.copy()
        variables['bin_path'] = bin_path
        variables.update(os.environ)

        for target in targets:
            variables['target'] = target
            for arch in architectures:
                variables['arch'] = arch
                build_cmd = [c.format_map(variables) for c in command]
                self._run_command(build_cmd, cwd=cwd)
                self._collect_files(bin_path, output_path, **variables)
            for post_target in post_target_commands:
                post_cmd = [c.format_map(variables) for c in post_target['command']]
                post_cmd_cwd = post_target.get('cwd', cwd).format_map(variables)
                self._run_command(post_cmd, cwd=post_cmd_cwd)
                self._collect_files(bin_path, output_path, **variables)
        if build_editor and "editor" in kwargs:
            editor_command = kwargs['editor']
            self._run_command(editor_command, cwd=cwd)
            self._collect_files(bin_path, output_path, **variables)

    def _run_command(self, command: Sequence, *, cwd: Optional[str] = None):
        silent = self.stdout_fn is not None or self.stderr_fn is not None
        result = self.cmd.run(command, cwd=cwd, silent=silent,
                              stdout_fn=self.stdout_fn, stderr_fn=self.stderr_fn).result
        assert result == 0, f"Command failed with code {result}: '{' '.join(command)}'"

    def _collect_files(self, source: str, destination: str, **kwargs):
        strip = self.strip.value
        for binary in self._collect_binaries(source, destination):
            file_name = os.path.basename(binary)
            for source_name, target_name in NAME_MAPPING:
                if file_name == source_name:
                    new_binary = os.path.join(destination, target_name)
                    shutil.move(binary, new_binary)
                    binary = new_binary
            if strip and "strip_command" in kwargs:
                strip_bin = kwargs["strip_command"]["bin"].format_map(kwargs)
                name_match_regex = re.compile(kwargs["strip_command"]['regex'], re.I)
                backup_path = os.path.join(destination, "backup")
                os.makedirs(backup_path, exist_ok=True)
                if name_match_regex.match(file_name) is not None:
                    unstripped_file_name = os.path.join(backup_path, file_name)
                    shutil.move(binary, unstripped_file_name)
                    # self.cmd.run((strip_bin, unstripped_file_name, "-o", binary), silent=False)
                    self._run_command((strip_bin, unstripped_file_name, "-o", binary))

    @staticmethod
    def _collect_binaries(src_path: str, dst_path: str) -> Generator[str, None, None]:
        collected_files = []
        for item in os.scandir(src_path):  # type: os.DirEntry
            if not item.is_file():
                continue
            dst = xappt.get_unique_name(os.path.join(dst_path, item.name), mode=xappt.UniqueMode.INTEGER)
            shutil.move(item.path, dst)
            collected_files.append(dst)
        for f in collected_files:
            yield f

    def run_build(self, interface: xappt.BaseInterface) -> int:
        manifest_path = self.manifest_path.value
        project_root = os.path.dirname(manifest_path)
        template_path = os.path.join(project_root, "templates")

        interface.progress_start()

        interface.progress_update("Loading manifest...", 0.0)

        with open(manifest_path, "r") as fp:
            manifest = json.load(fp)

        branch = manifest['TEMPLATE_NAME']
        if len(manifest['ENCRYPTION_KEY']):
            self.cmd.env_var_add("SCRIPT_AES256_ENCRYPTION_KEY", manifest['ENCRYPTION_KEY'])

        with xappt.temp_path() as tmp:
            interface.progress_update("Cloning Godot Engine repository...", 0.0)
            # assert self.cmd.run(("git", "clone", "https://github.com/godotengine/godot.git", "godot-build"),
            #                     cwd=tmp, silent=False).result == 0
            self._run_command(("git", "clone", "https://github.com/godotengine/godot.git", "godot-build"), cwd=tmp)

            godot_path = os.path.join(tmp, "godot-build")
            interface.progress_update(f"Fetching...", 0.33)
            # assert self.cmd.run(("git", "fetch", "--all", "--tags"), cwd=godot_path, silent=False).result == 0
            self._run_command(("git", "fetch", "--all", "--tags"), cwd=godot_path)

            interface.progress_update(f"Checking out branch '{branch}'...", 0.66)
            # assert self.cmd.run(("git", "checkout", f"tags/{branch}", "-b", branch),
            #                     cwd=godot_path, silent=False).result == 0
            self._run_command(("git", "checkout", f"tags/{branch}", "-b", branch), cwd=godot_path)

            selected_modules = self.modules.value
            for i, module in enumerate(selected_modules):
                progress = (i / len(selected_modules))
                interface.progress_update(f"Cloning module '{module}'...", progress)
                module_dict = GODOT_MODULES[module]
                # assert self.cmd.run(("git", "clone", module_dict['repository'], module),
                #                     cwd=tmp, silent=False).result == 0
                self._run_command(("git", "clone", module_dict['repository'], module), cwd=tmp)
                module_src_path = os.path.abspath(os.path.join(tmp, module, module_dict['src-folder']))
                module_dst_path = os.path.abspath(os.path.join(godot_path, "modules", module_dict['dst-folder']))
                shutil.copytree(module_src_path, module_dst_path)

            selected_platforms = self.platform.value
            for i, platform in enumerate(selected_platforms):
                progress = (i / len(selected_platforms))
                interface.progress_update(f"Building for platform '{platform}'...", progress)
                build_vars = BUILD_COMMANDS[platform]
                if isinstance(build_vars, dict):
                    build_vars = [build_vars]
                for var_set in build_vars:
                    argument_dict = var_set.copy()
                    argument_dict.update({
                        'cwd': godot_path,
                        'output_path': template_path,
                    })
                    self._build_platform_template(**argument_dict)

        interface.progress_end()

        if interface.ask("Build complete.\n\nOpen build folder?"):
            open_file(template_path)

        return 0

    def check_prerequisites(self):
        if os.name != "posix":
            raise RuntimeError("This plugins is currently only supported on posix systems.")
        if shutil.which("git") is None:
            raise RuntimeError("'git' binary not found.")
        if shutil.which("scons") is None:
            raise RuntimeError("'scons' binary not found.")
        if "osx" in self.platform.value:
            osxcross = os.environ.get("OSXCROSS_ROOT")
            if osxcross is None:
                raise RuntimeError("OSXCROSS_ROOT environment variable is not set.")
            else:
                if not os.path.isdir(osxcross):
                    raise RuntimeError(f"OSXCROSS_ROOT folder ({osxcross}) does not exist.")
        if "windows" in self.platform.value:
            if shutil.which("x86_64-w64-mingw32-strip") is None:
                raise RuntimeError("'mingw32' binaries not found.")
            if shutil.which("i686-w64-mingw32-strip") is None:
                raise RuntimeError("'mingw32' binaries not found.")

    def execute(self, interface: xappt.BaseInterface, **kwargs) -> int:
        if isinstance(interface, xappt_qt.QtInterface):
            interface.runner.show_console()
            self.stdout_fn = interface.runner.add_output_line
            self.stderr_fn = interface.runner.add_error_line

        try:
            self.check_prerequisites()
        except RuntimeError as e:
            interface.error(str(e))
            interface.progress_end()
            return 1

        try:
            return self.run_build(interface)
        except AssertionError as e:
            interface.error(str(e))
            interface.progress_end()
            return 1
