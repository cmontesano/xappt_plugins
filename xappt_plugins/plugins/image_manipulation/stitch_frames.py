import logging
import math
import os

from typing import Generator, Optional

import pyseq
from boltons.iterutils import chunked_iter, pairwise_iter
from PIL import Image

import xappt

from xappt_plugins.validators import ValidateFolderExists

logger = logging.getLogger("xappt")
logger.setLevel(logging.DEBUG)

SUPPORTED_EXTENSIONS = {
    ".png": {"mode": "RGBA"},
    ".jpg": {"mode": "RGB"},
    ".jpeg": {"mode": "RGB"},
}

PO2 = [2 ** (x + 1) for x in range(16)]


def coroutine(func):
    def start(*args, **kwargs):
        cr = func(*args, **kwargs)
        next(cr)
        return cr
    return start


def get_matching_po2(n: int) -> int:
    for lower, upper in pairwise_iter(PO2):
        if n == lower:
            return n
        if n == upper:
            return n
        if lower < n < upper:
            return upper
    raise ValueError(f"Could not find power of 2 for '{n}'")


@coroutine
def join_slices(output: str, **kwargs) -> Generator[None, str, None]:
    image_mode = kwargs['image_mode']
    columns = kwargs['columns']
    force_po2 = kwargs.get('force_po2', True)
    tile_w = 0
    tile_h = 0
    slices = []
    try:
        while True:
            image_slice = yield
            img = Image.open(image_slice)
            slices.append(img)
            # make sure all tiles are the same size
            sw, sh = img.size
            if tile_w == 0:
                tile_w = sw
            else:
                assert sw == tile_w
            if tile_h == 0:
                tile_h = sh
            else:
                assert sh == tile_h
    except GeneratorExit:
        rows = int(math.ceil(len(slices) / float(columns)))
        if force_po2:
            img_size = (get_matching_po2(tile_w * columns), get_matching_po2(tile_w * rows))
        else:
            img_size = (tile_w * columns, tile_w * rows)
        result = Image.new(image_mode, img_size)
        for row, images in enumerate(chunked_iter(slices, columns)):
            x = 0
            for img in images:
                sw, sh = img.size
                result.paste(img, (x, row * sh))
                x += sw
        result.save(output)


def stitch_sequence(interface: xappt.BaseInterface, sequence: pyseq.Sequence, **kwargs):
    input_path = kwargs['input_path']
    output_path = kwargs['output_path']
    columns = kwargs['columns']
    force_po2 = kwargs['force_po2']

    if len(sequence) == 1:
        logger.warning(f"Skipping '{sequence[0]}'. Not a sequence.")
        return

    extension = os.path.splitext(sequence.format("%h%p%t"))[-1].lower()
    if extension not in SUPPORTED_EXTENSIONS.keys():
        logger.warning(f"'{extension}' not supported")
        return

    image_mode = SUPPORTED_EXTENSIONS[extension]['mode']

    output_file = os.path.join(output_path, f"{sequence.head()}[stitched]{sequence.tail()}")
    if os.path.isfile(output_file) and not kwargs['replace']:
        raise OSError(f"File exists: '{output_file}'")

    progress_max = len(sequence)

    interface.progress_start()

    joiner = join_slices(output_file, columns=columns, force_po2=force_po2, image_mode=image_mode)
    for i, frame in enumerate(sequence, start=1):
        progress = i / progress_max
        source = os.path.join(input_path, frame)
        joiner.send(source)
        interface.progress_update(f"processed {frame}", progress)
    joiner.close()

    interface.progress_end()


@xappt.register_plugin
class StitchImages(xappt.BaseTool):
    input_path = xappt.ParamString(options={'short_name': "i", "ui": "folder-select"},
                                   description="Where are the images that are to be stitched?",
                                   validators=[ValidateFolderExists])
    output_path = xappt.ParamString(options={'short_name': "o", "ui": "folder-select"},
                                    description="Where should the stitched image be saved?",
                                    validators=[ValidateFolderExists])
    columns = xappt.ParamInt(options={'short_name': "c"}, default=8,
                             description="How many images per row?")
    replace = xappt.ParamBool(options={'short_name': "r"}, default=False,
                              description="Should we replace existing files?")
    force_po2 = xappt.ParamBool(options={'short_name': "p", "caption": "Force res²"}, default=False,
                                description="Should the output image dimensions be a power of 2?")

    @classmethod
    def name(cls) -> str:
        return "stitch"

    @classmethod
    def help(cls) -> str:
        return "Stitch a directory of images together. The images must all share the same prefix."

    @classmethod
    def collection(cls) -> str:
        return "Image"

    def execute(self, interface: xappt.BaseInterface, **kwargs) -> int:
        sequences = pyseq.get_sequences(os.listdir(self.input_path.value))
        for sequence in sequences:
            stitch_sequence(interface, sequence, **self.param_dict())
        interface.message("Complete")
        return 0
