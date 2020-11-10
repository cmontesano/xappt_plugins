import os

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
    columns = xappt.ParamInt(options={'short_name': "x"}, minimum=1,
                             description="How many columns of tiles are there?", default=8)
    rows = xappt.ParamInt(options={'short_name': "y"}, minimum=1,
                          description="How many rows of tiles are there?", default=8)
    replace = xappt.ParamBool(options={'short_name': "r"}, default=False,
                              description="Should we replace existing files?")

    @classmethod
    def name(cls) -> str:
        return "split"

    @classmethod
    def help(cls) -> str:
        return "Split an image into tiles."

    @classmethod
    def collection(cls) -> str:
        return "Image"

    def execute(self, **kwargs) -> int:
        input_path = self.input_image.value
        output_name, output_ext = os.path.splitext(os.path.basename(input_path))
        output_path = os.path.join(self.output_path.value, f'{output_name}.%03d{output_ext}')

        if output_ext.lower() not in SUPPORTED_EXTENSIONS.keys():
            self.interface.error(f"File extension '{output_ext}' is not supported")
            return 1

        cols = self.columns.value
        rows = self.rows.value

        img = Image.open(input_path)
        sw, sh = img.size

        tile_size = (sw // cols, sh // rows)

        mode = SUPPORTED_EXTENSIONS[output_ext.lower()]['mode']

        total = rows * cols
        self.interface.progress_start()

        for y in range(rows):
            for x in range(cols):
                tile_index = ((y * cols) + x) + 1
                self.interface.progress_update(f"Extracting tile {tile_index}", tile_index / total)
                dst = output_path % tile_index
                result = Image.new(mode, tile_size)
                result.paste(img, (-x * tile_size[0], -y * tile_size[1]))
                result.save(dst)

        self.interface.progress_end()
        self.interface.message("Complete")

        return 0
