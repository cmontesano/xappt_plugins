import os

import xappt


class ValidateFolderExists(xappt.BaseValidator):
    def validate(self, value: str) -> str:
        value = os.path.abspath(value)
        if not os.path.isdir(value):
            raise xappt.ParameterValidationError(f"Path '{value}' does not exist.")
        return value
