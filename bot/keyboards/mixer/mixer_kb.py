from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from Web.CRM.models import Tilers, MincedMeatBatchMix


def mixer_keyboard(mix_id) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(*[InlineKeyboardButton(text="Перемешивание и анализ", callback_data=f"farshov_mix-{mix_id}")])
    keyboard.add(*[InlineKeyboardButton(text="Помощь", callback_data="farshovitel_help")])
    return keyboard


def farshovitel_minced_meat_from_analysis_keyboard(minced_mix_id, is_mko=None) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(row_width=2)

    if is_mko:
        if is_mko in [1, 10]:
            keyboard.add(
                *[InlineKeyboardButton(text="Загрузить в плиточник", callback_data=f"farshunload_mix-{minced_mix_id}")]
            )
        elif is_mko == 2:
            keyboard.add(
                *[
                    InlineKeyboardButton(
                        text="Указать номер паллета", callback_data=f"farshloadshoсk_mix-{minced_mix_id}"
                    )
                ]
            )
    else:
        keyboard.add(
            *[InlineKeyboardButton(text="Загрузить в плиточник", callback_data=f"farshunload_mix-{minced_mix_id}")]
        )

    keyboard.add(*[InlineKeyboardButton(text="Помощь", callback_data="farshovitel_help")])
    return keyboard


def packer_select_tiler_keyboard(mix_id) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(row_width=4)
    line_type = MincedMeatBatchMix.objects.get(pk=mix_id).minced_meat_batch.line_type
    if line_type == 1:
        tillers_for_lines = [i for i in range(1, 8)]
    elif line_type == 2:
        tillers_for_lines = [i for i in range(8, 15)]
    else:
        tillers_for_lines = [i for i in range(1, 15)]
    tillrs_sorted = sorted(
        [i.pk for i in Tilers.objects.filter(status=True).all() if i.status and i.pk in tillers_for_lines]
    )
    keyboard.add(
        *[InlineKeyboardButton(text=f"{i}", callback_data=f"select_tiler-{i}-{mix_id}") for i in tillrs_sorted]
    )
    return keyboard


def packer_for_unload_keyboard(batch_mix) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(*[InlineKeyboardButton(text="Выгрузить из плиточника", callback_data=f"pack_unloaded-{batch_mix}")])
    keyboard.add(*[InlineKeyboardButton(text="Помощь", callback_data="pack_help")])
    return keyboard


def packer_for_unload_shocker_keyboard(batch_mix) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(*[InlineKeyboardButton(text="Выгрузить из шокера", callback_data=f"pack_unloaded_shock-{batch_mix}")])
    keyboard.add(*[InlineKeyboardButton(text="Помощь", callback_data="pack_help")])
    return keyboard


def packer_for_unload_shocker_second_minced_meat_keyboard(batch_mix) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        *[InlineKeyboardButton(text="Выгрузить из шокера", callback_data=f"pack_unloaded_shock_second-{batch_mix}")]
    )
    keyboard.add(*[InlineKeyboardButton(text="Помощь", callback_data="pack_help")])
    return keyboard


def start_storekeeper_and_mark_keyboard(minced_mix_id) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        *[InlineKeyboardButton(text="Начать палетирование и маркировку", callback_data=f"sto_mar-{minced_mix_id}")]
    )
    return keyboard


def start_storekeeper_and_mark_second_meat_keyboard(second_meat_id) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(*[InlineKeyboardButton(text="Начать палетирование и маркировку", callback_data="unload_meat")])
    return keyboard


def start_storekeeper_and_mark_second_meat_keyboard_old(second_meat_id) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        *[
            InlineKeyboardButton(
                text="Начать палетирование и маркировку", callback_data=f"second_meat-{second_meat_id}"
            )
        ]
    )
    return keyboard
