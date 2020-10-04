import xappt


class ValidateRectString(xappt.BaseValidator):
    def validate(self, value: str) -> str:
        if not len(value):
            return value
        coordinates = value.split(",")
        if len(coordinates) != 4:
            raise xappt.ParameterValidationError(f"Rect '{value}' must contain four comma separated numbers.")
        ints = []
        for item in coordinates:
            try:
                ints.append(int(item.strip()))
            except (ValueError, TypeError):
                raise xappt.ParameterValidationError(f"Item '{value}' is not a valid integer.")
        value = ",".join(map(str, ints))
        return value
