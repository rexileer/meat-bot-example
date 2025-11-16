import logging
import re
from datetime import datetime, timedelta
from decimal import Decimal

from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.types import Message, InputFile, CallbackQuery

from Web.CRM.dataclasses import RolesModel
from Web.CRM.models import MeatBlank, RawMeatBatch, MeatBlankRawMeatBatch
from data.constants import FLOAT_REGEX, DATE_FORMAT
from bot.handlers.meat_blank.utils.raw_material import generate_storage_datatable
from bot.keyboards.main_menu import main_menu_keyboard
from bot.keyboards.meat_blank.new_minced_meat_batch_form import (
    set_raw_meat_batch_keyboard,
    set_raw_materials_keyboard,
    set_weight_keyboard,
    set_arrival_date_keyboard,
)
from bot.keyboards.meat_blank.new_raw_meat_batch_form import preview_keyboard_meat_blank
from bot.keyboards.shared import return_keyboard
from bot.keyboards.storekeeper.storekeeper_keyboards import start_blank_actual_weight
from bot.loader import dp, bot
from bot.states.new_meat_blank_form import NewMeatBlankForm
from bot.utils.helpers import get_from_dict_list
from bot.utils.text_info import meat_blank_list_for_new, raw_meat_blank_text_final


@dp.callback_query_handler(Text(startswith="new_meat_blank_mko"))
@dp.callback_query_handler(Text(startswith="main_menu_new_meat_blank"))
async def new_meat_blank_handler(call: CallbackQuery, state: FSMContext):
    frozen_raw_meat_batches = MeatBlank.get_available_frozen()
    storage_datatable = await generate_storage_datatable(frozen_raw_meat_batches)

    await call.message.answer_document(
        caption="Выберите сырье для заготовки",
        document=InputFile(filename="Сырье.xlsx", path_or_bytesio=storage_datatable),
        reply_markup=set_raw_materials_keyboard(frozen_raw_meat_batches),
    )
    if "new_meat_blank_mko" in call.data:
        await state.update_data(is_mko=1)
    await state.update_data(raw_meat_batches=[])
    await NewMeatBlankForm.set_raw_materials.set()


@dp.message_handler(state=NewMeatBlankForm.set_raw_materials)
async def set_raw_materials_handler(message: Message, state: FSMContext):
    raw_material: RawMeatBatch = await RawMeatBatch.objects.filter(raw_material__name=message.text).afirst()
    if raw_material:
        await state.update_data(
            current_raw_material_id=raw_material.pk, current_raw_material_name=raw_material.raw_material.name
        )
        logging.info(raw_material)
        raw_meat_batches = await get_available(state, raw_material__name=message.text)
        await message.answer(
            "Выберите партию для заготовки", reply_markup=set_raw_meat_batch_keyboard(raw_meat_batches)
        )
        await NewMeatBlankForm.set_raw_meat_batch.set()
    else:
        frozen_raw_meat_batches = await get_available(state)

        await message.answer(
            "Выбранный вариант не существует. Попробуйте еще раз",
            reply_markup=set_raw_materials_keyboard(frozen_raw_meat_batches),
        )


async def get_available(state: FSMContext, raw_material__name=None):
    state_data = await state.get_data()
    raw_meat_batches = MeatBlank.get_available_frozen(raw_material__name)
    if state_data.get("raw_meat_batches"):
        raw_meat_batches = [
            meat_batch
            for meat_batch in raw_meat_batches
            if not get_from_dict_list(state_data["raw_meat_batches"], "id", meat_batch.pk)
        ]
    return raw_meat_batches


@dp.message_handler(state=NewMeatBlankForm.set_raw_meat_batch)
async def set_raw_meat_batch_handler(message: Message, state: FSMContext):
    raw_meat_batch = await RawMeatBatch.objects.filter(production_id__icontains=message.text).afirst()

    if raw_meat_batch:
        await state.update_data(current_raw_meat_batch_id=raw_meat_batch.pk)

        await message.answer(
            f"""Введите требуемую массу (в кг)\n\n Наличие на складе: {raw_meat_batch.weight} кг""",
            reply_markup=set_weight_keyboard(),
        )
        await NewMeatBlankForm.set_weight.set()
    else:
        raw_meat_batches = await get_available(state)
        await message.answer(
            "Выбранный вариант не существует. Попробуйте еще раз",
            reply_markup=set_raw_meat_batch_keyboard(raw_meat_batches),
        )


@dp.message_handler(
    lambda message: re.match(FLOAT_REGEX, message.text) or message.text == "Все", state=NewMeatBlankForm.set_weight
)
async def set_weight_handler(message: Message, state: FSMContext):
    state_data = await state.get_data()
    raw_meat_batch = await RawMeatBatch.objects.filter(pk=state_data["current_raw_meat_batch_id"]).afirst()

    weight_str = message.text
    if message.text == "Все":
        weight = raw_meat_batch.weight
        weight_str = str(raw_meat_batch.weight)
    else:
        weight = Decimal(weight_str)

    if weight <= raw_meat_batch.weight:
        await state.update_data(current_raw_meat_batch_weight=weight_str)

        state_data = await state.get_data()
        raw_meat_batches = state_data["raw_meat_batches"] + [
            {
                "id": state_data["current_raw_meat_batch_id"],
                "weight": state_data["current_raw_meat_batch_weight"],
            }
        ]

        await state.update_data(
            raw_meat_batches=raw_meat_batches,
            current_raw_material_id=None,
            current_raw_material_name=None,
            current_raw_meat_batch_weight=None,
            current_raw_meat_batch_id=None,
        )

        text = f"""Предпросмотр заготовки\n\nИспользуемое сырье:\n{await meat_blank_list_for_new(state)}"""

        await message.answer(text, reply_markup=preview_keyboard_meat_blank())
        await NewMeatBlankForm.preview.set()
    else:
        await message.answer(f"Такой массы нет на складе. Максимальная масса: {int(raw_meat_batch.weight)} кг")


@dp.message_handler(state=NewMeatBlankForm.set_weight)
async def set_weight_decimal_error_handler(message: Message, state: FSMContext):
    await message.answer(text="Масса должна быть числом", reply_markup=return_keyboard())


@dp.message_handler(text="Добавить сырье", state=NewMeatBlankForm.preview)
async def preview_add_raw_material_handler(message: Message, state: FSMContext):
    raw_meat_batches = await get_available(state)
    if not raw_meat_batches:
        return await message.answer("Нет доступного сырья")

    await message.answer("Выберите сырье для заготовки", reply_markup=set_raw_materials_keyboard(raw_meat_batches))
    await NewMeatBlankForm.set_raw_materials.set()


@dp.message_handler(text="Подтвердить", state=NewMeatBlankForm.preview)
async def set_previev_handler(message: Message, state: FSMContext):
    await message.answer(
        "Выберите дату прихода в цех. Можно ввести в формате 21.11.2020", reply_markup=set_arrival_date_keyboard()
    )
    await NewMeatBlankForm.set_arrival_date.set()


@dp.message_handler(state=NewMeatBlankForm.set_arrival_date)
async def set_arrival_date_handler(message: Message, state: FSMContext, roles: RolesModel):
    if message.text == "Сегодня":
        arrival_date = datetime.now()
    elif message.text == "Завтра":
        arrival_date = datetime.now() + timedelta(days=1)
    else:
        try:
            arrival_date = datetime.strptime(message.text, DATE_FORMAT)
        except ValueError:
            return await message.answer("Дата была введена в неверном формате (правильный формат: 21.11.2020)")

    state_data = await state.get_data()

    start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)

    meat_blank_count = MeatBlank.get_count_by_date(start=start, end=end)

    production_id = f"З{arrival_date.strftime('%d%m%Y')}/{meat_blank_count + 3}"

    all_weight = sum([float(data["weight"]) for data in state_data["raw_meat_batches"]])
    meat_blank: MeatBlank = await MeatBlank.objects.acreate(
        production_id=production_id,
        arrival_date=arrival_date,
        type_meat_blank=1 if "is_mko" in state_data else 0,
        protein=state_data["protein"],
        fat=state_data["fat"],
        moisture=state_data["moisture"],
        weight=all_weight,
    )

    for raw_meat_batch_state in state_data["raw_meat_batches"]:
        await MeatBlankRawMeatBatch.objects.acreate(
            meat_blank_id=meat_blank.pk,
            raw_meat_batch_id=raw_meat_batch_state["id"],
            weight=raw_meat_batch_state["weight"],
        )
        raw_meat_batch = await RawMeatBatch.objects.aget(pk=raw_meat_batch_state["id"])
        raw_meat_batch.weight = float(raw_meat_batch.weight) - float(raw_meat_batch_state["weight"])
        await raw_meat_batch.asave()

    raw_materials_info = await raw_meat_blank_text_final(meat_blank.pk)
    text = "\n".join(
        [
            "Заготовка успешно зарегистрирована",
            f"ID заготовки: {production_id}",
            "Используемое сырье:",
            f"{raw_materials_info}",
        ]
    )
    await message.answer(text, reply_markup=main_menu_keyboard(message.from_user.id))
    await state.finish()


async def storkeepe_notify_meat_blank(meat_blank_id, roles: RolesModel):
    meat_blank = MeatBlank.objects.get(pk=meat_blank_id)
    raw_materials_info = await raw_meat_blank_text_final(meat_blank_id)
    text = "\n".join(
        [
            "Была создана новая заготовка",
            f"ID заготовки: {meat_blank.production_id}",
            "Используемое сырье:",
            f"{raw_materials_info}",
        ]
    )
    await bot.send_message(
        chat_id=roles.storekeeper.telegram_id, text=text, reply_markup=start_blank_actual_weight(f"{meat_blank_id}")
    )
