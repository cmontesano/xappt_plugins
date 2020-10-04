import datetime
import logging
import os
import time

from typing import Optional

import pyscreenshot

import xappt
import xappt_qt

from xappt_plugins.validators import *

logger = logging.getLogger("xappt")
logger.setLevel(logging.DEBUG)


@xappt.register_plugin
class TimeLapse(xappt.BaseTool):
    output_path = xappt.ParamString(options={'short_name': "o", "ui": "folder-select"}, default=os.getcwd(),
                                    description="Where should the stitched image be saved?",
                                    validators=[ValidateFolderExists])
    output_name = xappt.ParamString(options={'short_name': "n"}, default="screenshot-",
                                    description="What file name should be given to each image?")
    time_format = xappt.ParamString(options={'short_name': "t"}, default="%Y%m%d_%H%M%S",
                                    description="What date format should be used in the file names?")
    output_format = xappt.ParamString(options={'short_name': "f"}, default=".jpg", choices=('.jpg', '.png'),
                                      description="What file format should be used?")
    interval = xappt.ParamFloat(options={'short_name': "i"}, minimum=2.0, default=5.0,
                                description="How much time between each screenshot?")
    bounds = xappt.ParamString(options={'short_name': "b"}, required=False, default="",
                               description="Specify optional recording coordinates: x1,y1,x2,y2",
                               validators=[ValidateRectString])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._closed = False

    @classmethod
    def help(cls) -> str:
        return "Take a screenshot at fixed intervals."

    def on_close(self):
        self._closed = True

    def execute(self, interface: Optional[xappt.BaseInterface], **kwargs) -> int:
        interval = max(2.0, self.interval.value)
        bounds = self.bounds.value
        if len(bounds):
            assert bounds.count(",") == 3
            bounds = tuple([int(x) for x in bounds.split(",")])
            assert len(bounds) == 4
        output_path = self.output_path.value
        output_filename = f"{self.output_name.value}{self.time_format.value}{self.output_format.value}"
        if interface is None:
            interface = xappt.get_interface()
        if isinstance(interface, xappt_qt.interface.QtInterface):
            update_fn = interface.instance.app.processEvents
            interface.runner.rejected.connect(self.on_close)
        else:
            def update_fn():
                pass
        interface.progress_start()
        try:
            while not self._closed:
                start = time.perf_counter()
                timestamp = datetime.datetime.now()
                out_file = os.path.join(output_path, timestamp.strftime(output_filename))
                im = pyscreenshot.grab(bbox=bounds)
                im.save(out_file)
                message = f"saved {os.path.basename(out_file)}"
                while True:
                    if self._closed:
                        break
                    elapsed = time.perf_counter() - start
                    if elapsed > interval:
                        interface.progress_update("", 0.0)
                        break
                    interface.progress_update(message, elapsed/interval)
                    update_fn()
                    time.sleep(0.1)
        except KeyboardInterrupt:
            pass
        interface.progress_end()
        return 0
