import dataclasses
import datetime
import typing
from dataclasses import dataclass


class CustomDateTime(datetime.datetime):
    @staticmethod
    def to_parse(date_string, date_format="%d.%m.%Y") -> typing.Optional["CustomDateTime"]:
        if not date_string:
            return None

        date = CustomDateTime.fromisoformat(date_string[:-6])

        return date

    @staticmethod
    def to_format(date_string, date_format="%d.%m.%Y") -> str:
        date = CustomDateTime.to_parse(date_string)

        if date is None:
            return ""

        return date.strftime(date_format)


@dataclass
class RolesModel:
    raw_material_reciver: int
    defrost_manager: int
    Farshesostovitel: int
    Farshesostovitel_line_2: int
    press_operator_line_1: int
    press_operator_line_2: int
    labaratory: int
    packer: int
    technologist: int
    rastarshchik: int
    rastarshchik_line_2: int
    rastarshchik_meat_blanks: int
    storekeeper: int
    storekeeper_shocker: int
    mko_manager_line_2: int


def from_dict(data_class_type, data):
    if dataclasses.is_dataclass(data_class_type):
        field_types = {f.name: f.type for f in dataclasses.fields(data_class_type)}
        return data_class_type(**{f: from_dict(field_types[f], data.get(f, None)) for f in field_types})
    elif isinstance(data_class_type, type) and issubclass(data_class_type, CustomDateTime):
        if isinstance(data, dict):
            return None
        else:
            return data_class_type.fromisoformat(data)
    else:
        return data
