import os

import xappt


class ValidateFileExists(xappt.BaseValidator):
    def validate(self, value: str) -> str:
        value = os.path.abspath(value)
        if not os.path.isfile(value):
            raise xappt.ParameterValidationError(f"File '{value}' does not exist.")
        return value
