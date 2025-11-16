import uuid
from decimal import Decimal

import pytz


def extract_digits(input_str: str) -> str:
    return "".join([char for char in input_str if char.isdigit()])


def is_valid_uuid(val: str):
    try:
        uuid.UUID(val)
        return True
    except ValueError:
        return False


def get_from_dict_list(list_obj, key, value):
    return next((item for item in list_obj if item.get(key) == value), None)


def beautify_decimal(number: Decimal) -> str:
    return f"{number:.2f}".replace(".", ",")


def convert_to_localtime(utc):
    fmt = "%H:%M %d.%m.%Y"
    localtz = utc.replace(tzinfo=pytz.utc)
    return localtz.strftime(fmt)


def convert_to_localdate(utc):
    fmt = "%d.%m.%Y"
    localtz = utc.replace(tzinfo=pytz.utc)
    return localtz.strftime(fmt)
