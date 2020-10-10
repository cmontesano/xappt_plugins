import os

from typing import Optional

from PIL import Image

import xappt

from xappt_plugins.validators import *

SUPPORTED_EXTENSIONS = {
    ".png": {"mode": "RGBA"},
    ".jpg": {"mode": "RGB"},
    ".jpeg": {"mode": "RGB"},
}


@xappt.register_plugin
class SplitImage(xappt.BaseTool):
    input_image = xappt.ParamString(options={'short_name': "i", "ui": "file-open"},
                                    description="Where is the image that is to be split?",
                                    validators=[ValidateFileExists])
    output_path = xappt.ParamString(options={'short_name': "o", "ui": "folder-select"}, default=os.getcwd(),
                                    description="Where should the tiles be saved?",
                                    validators=[ValidateFolderExists])
    tile_size = xappt.ParamInt(options={'short_name': "t"}, minimum=1,
                               description="How many pixels wide is each tile? All tiles are assumed to be square.")
    replace = xappt.ParamBool(options={'short_name': "r"}, default=False,
                              description="Should we replace existing files?")

    @classmethod
    def name(cls) -> str:
        return "split"

    @classmethod
    def help(cls) -> str:
        return "Split an image into square tiles."

    @classmethod
    def collection(cls) -> str:
        return "Image"

    def execute(self, interface: xappt.BaseInterface, **kwargs) -> int:
        input_path = self.input_image.value
        output_name, output_ext = os.path.splitext(os.path.basename(input_path))
        output_path = os.path.join(self.output_path.value, f'{output_name}.%03d{output_ext}')

        if output_ext.lower() not in SUPPORTED_EXTENSIONS.keys():
            interface.error(f"File extension '{output_ext}' is not supported")
            return 1

        tile_size = self.tile_size.value

        img = Image.open(input_path)
        sw, sh = img.size

        if sw % tile_size != 0 or sh % tile_size != 0:
            interface.error(f"The source image resolution ({sw}x{sh}) must be "
                            f"evenly divisible by the tile size: {tile_size}")
            return 1

        cols = sw // tile_size
        rows = sh // tile_size

        mode = SUPPORTED_EXTENSIONS[output_ext.lower()]['mode']

        total = rows * cols
        interface.progress_start()

        for y in range(rows):
            for x in range(cols):
                tile_index = ((y * cols) + x) + 1
                interface.progress_update(f"Extracting tile {tile_index}", tile_index / total)
                dst = output_path % tile_index
                result = Image.new(mode, (tile_size, tile_size))
                result.paste(img, (-x * tile_size, -y * tile_size))
                result.save(dst)

        interface.progress_end()
        interface.message("Complete")

        return 0
