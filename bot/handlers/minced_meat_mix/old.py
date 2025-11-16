import logging
import re
from datetime import datetime, timedelta
from decimal import Decimal

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.types import InputFile, Message

from bot.handlers.minced_meat_mix.utils.raw_material import generate_blanks_datatable, generate_blanks_datatable_mko
from bot.keyboards.main_menu import main_menu_keyboard
from bot.keyboards.meat_blank.new_minced_meat_batch_form import (
    set_arrival_date_keyboard,
    set_line_minced_meat_keyboard,
    set_material_type_keyboard,
    set_material_type_keyboard_mko,
    set_meat_blank_keyboard,
    set_nigth_minced_meat_keyboard,
    set_raw_materials_keyboard,
    set_raw_meat_batch_keyboard,
    set_recipe_keyboard,
    set_second_minced_meat_keyboard,
    set_weight_keyboard,
)
from bot.keyboards.meat_blank.new_raw_meat_batch_form import (
    preview_keyboard_meat_batch,
    preview_keyboard_meat_batch_mko,
)
from bot.keyboards.shared import return_keyboard
from bot.loader import dp
from bot.states.new_minced_meat_batch_form import NewMincedMeatBatchForm
from bot.utils.helpers import get_from_dict_list
from bot.utils.text_info import (
    generate_recipe_for_minced_meat_mix,
    generate_recipe_raw_meat_batches_and_meat_blanks_text,
    generate_recipe_second_meat_and_meat_blanks_text,
)
from data.constants import DATE_FORMAT, FLOAT_REGEX
from Web.CRM.dataclasses import RolesModel
from Web.CRM.models import (
    MeatBlank,
    MincedMeatBatch,
    MincedMeatBatchMeatBlank,
    MincedMeatBatchMix,
    MincedMeatBatchRawMeatBatch,
    MincedMeatBatchSecondMeatBlank,
    RawMeatBatch,
    Recipe,
    SecondMincedMeat,
)


@dp.callback_query_handler(Text(startswith="main_menu_new_minced_meat_batch"))
async def new_minced_meat_batch_handler(call: types.CallbackQuery, state: FSMContext):
    meat_blanks = MeatBlank.get_available_chilled()
    meat_batches = RawMeatBatch.get_available_chilled()
    storage_datatable = await generate_blanks_datatable(meat_blanks, meat_batches)

    await call.message.answer_document(
        caption="Выберите сырье для фарша",
        document=InputFile(filename="Заготовки.xlsx", path_or_bytesio=storage_datatable),
        reply_markup=set_material_type_keyboard(),
    )

    await state.update_data(raw_meat_batches=[], meat_blanks=[])
    await NewMincedMeatBatchForm.set_material_type.set()


@dp.callback_query_handler(Text(startswith="new_minced_meat_mko"))
async def new_minced_meat_mko_handler(call: types.CallbackQuery, state: FSMContext):
    meat_blanks_mko = SecondMincedMeat.get_available_second_minced_meat()
    meat_batches = MeatBlank.get_available_chilled_mko()
    await state.update_data(is_mko=1)
    storage_datatable = await generate_blanks_datatable_mko(meat_blanks_mko, meat_batches)
    await call.message.answer_document(
        caption="Выберите сырье для фарша",
        document=InputFile(filename="Заготовки.xlsx", path_or_bytesio=storage_datatable),
        reply_markup=set_material_type_keyboard_mko(),
    )
    await state.update_data(second_minced_meat_blanks=[], meat_blanks=[])
    await NewMincedMeatBatchForm.set_material_type.set()


# вторфашр
@dp.message_handler(text="Добавить вторфарш", state=NewMincedMeatBatchForm.preview)
@dp.message_handler(text="Вторфарш", state=NewMincedMeatBatchForm.set_material_type)
async def set_material_second_minced_meat(message: Message, state: FSMContext):
    state_data = await state.get_data()
    used_second_minced_meat = state_data.get("second_minced_meat_weight", 0)
    available_weight = SecondMincedMeat.get_available_weight_second_minced_meat()
    if (available_weight - used_second_minced_meat) > 0:
        await message.answer(
            f"Доступно {available_weight - used_second_minced_meat} кг вторфарша. Введите требуемую массу (в кг)",
            reply_markup=set_second_minced_meat_keyboard(),
        )
        await NewMincedMeatBatchForm.set_weight_release_minced_meat.set()
    else:
        await message.answer("Нет доступного вторфарша")


@dp.message_handler(
    lambda message: re.match(FLOAT_REGEX, message.text) or message.text == "Использовать все",
    state=NewMincedMeatBatchForm.set_weight_release_minced_meat,
)
async def set_weight_release_second_minced_meat_handler(message: Message, state: FSMContext):
    state_data = await state.get_data()
    used_second_minced_meat = state_data.get("second_minced_meat_weight", 0)
    available_weight = SecondMincedMeat.get_available_weight_second_minced_meat()
    if message.text == "Использовать все":
        final_weight = SecondMincedMeat.get_available_weight_second_minced_meat()
    else:
        final_weight = used_second_minced_meat + float(message.text)

    if (available_weight - final_weight) < 0:
        await message.answer(
            "Вторфарша отрицателен! Не забудьте добавить вторфарш для компенсации отрицательного значения!"
        )

    await state.update_data(second_minced_meat_weight=final_weight)

    text = "\n".join(
        [
            "Предпросмотр фарша",
            "Используемое сырье и заготовки:",
            f"\n{await generate_recipe_second_meat_and_meat_blanks_text(state)}",
        ]
    )

    await message.answer(text, reply_markup=preview_keyboard_meat_batch_mko())
    await NewMincedMeatBatchForm.preview.set()


# Заготовки


@dp.message_handler(
    lambda message: re.match(FLOAT_REGEX, message.text) or message.text == "Все",
    state=NewMincedMeatBatchForm.set_weight_meat_blank,
)
async def set_weight_meat_blank_handler(message: Message, state: FSMContext):
    state_data = await state.get_data()
    meat_blank: MeatBlank = await MeatBlank.objects.aget(pk=state_data["current_meat_blank_id"])
    weight_str = message.text
    if message.text == "Все":
        weight = meat_blank.weight
        weight_str = str(weight)
    else:
        weight = Decimal(weight_str)

    if weight <= meat_blank.weight:
        await state.update_data(current_meat_blank_weight=weight_str)

        state_data = await state.get_data()
        meat_blanks = state_data["meat_blanks"] + [
            {
                "id": state_data["current_meat_blank_id"],
                "weight": state_data["current_meat_blank_weight"],
            }
        ]

        await state.update_data(meat_blanks=meat_blanks, current_meat_blank_weight=None, current_meat_blank_id=None)
        if "is_mko" in state_data:
            recipe = await generate_recipe_second_meat_and_meat_blanks_text(state)
        else:
            recipe = await generate_recipe_raw_meat_batches_and_meat_blanks_text(state)
        text = "\n".join(
            [
                "Предпросмотр фарша",
                "Используемое сырье и заготовки:",
                f"\n{recipe}",
            ]
        )

        await message.answer(
            text,
            reply_markup=(
                preview_keyboard_meat_batch() if "is_mko" not in state_data else preview_keyboard_meat_batch_mko()
            ),
        )
        await NewMincedMeatBatchForm.preview.set()
    else:
        await message.answer(f"Такой массы нет на складе. Максимальная масса: {meat_blank.weight} кг")


@dp.message_handler(text="Заготовка", state=NewMincedMeatBatchForm.set_material_type)
async def set_material_type_meat_blank_handler(message: Message, state: FSMContext):
    state_data = await state.get_data()
    meat_blanks = (
        MeatBlank.get_available_chilled() if not state_data.get("is_mko") else MeatBlank.get_available_chilled_mko()
    )
    if not meat_blanks:
        await message.answer(text="Доступные заготовки отсутствуют")
        return
    await message.answer(text="Выберите заготовку", reply_markup=set_meat_blank_keyboard(meat_blanks))
    await NewMincedMeatBatchForm.set_meat_blanks.set()


@dp.message_handler(state=NewMincedMeatBatchForm.set_meat_blanks)
async def set_meat_blanks_handler(message: Message, state: FSMContext):
    meat_blank = await MeatBlank.objects.filter(production_id=message.text).afirst()
    if meat_blank:
        weight = meat_blank.weight
        await state.update_data(current_meat_blank_id=meat_blank.id)
        logging.info(weight)
        text = f"""
Введите требуемую массу (в кг)

Наличие на складе: {weight} кг"""
        await message.answer(text, reply_markup=set_weight_keyboard())
        await NewMincedMeatBatchForm.set_weight_meat_blank.set()
    else:
        meat_blanks = await MeatBlank.objects.filter(type_meat_blank=0, weight__gt=0)
        await message.answer(
            "Выбранный вариант не существует. Попробуйте еще раз", reply_markup=set_meat_blank_keyboard(meat_blanks)
        )


@dp.message_handler(text="Добавить заготовку", state=NewMincedMeatBatchForm.preview)
async def preview_add_meat_blank_handler(message: Message, state: FSMContext):
    state_data = await state.get_data()
    meat_blanks = (
        MeatBlank.get_available_chilled() if "is_mko" not in state_data else MeatBlank.get_available_chilled_mko()
    )

    meat_blanks = [
        meat_blank
        for meat_blank in meat_blanks
        if not get_from_dict_list(state_data["meat_blanks"], "id", meat_blank.pk)
    ]

    if not meat_blanks:
        await message.answer(text="Доступные заготовки отсутствуют")
        return

    await message.answer(text="Выберите заготовку", reply_markup=set_meat_blank_keyboard(meat_blanks))
    await NewMincedMeatBatchForm.set_meat_blanks.set()


@dp.message_handler(text="Сырье", state=NewMincedMeatBatchForm.set_material_type)
async def set_material_type_meat_blank_handler_2(message: Message, state: FSMContext):
    state_data = await state.get_data()

    meat_batches = RawMeatBatch.get_available_chilled()

    meat_batches = [
        meat_batch
        for meat_batch in meat_batches
        if not get_from_dict_list(state_data["raw_meat_batches"], "id", meat_batch.pk)
    ]

    if not meat_batches:
        await message.answer(text="Доступное сырье отсутствует")
        return

    await message.answer("Выберите сырье для фарша", reply_markup=set_raw_materials_keyboard(meat_batches))
    await NewMincedMeatBatchForm.set_raw_materials.set()


@dp.message_handler(state=NewMincedMeatBatchForm.set_raw_materials)
async def set_raw_materials_handler(message: Message, state: FSMContext):
    raw_material = RawMeatBatch.objects.filter(raw_material__name__icontains=message.text).first()
    state_data = await state.get_data()
    if raw_material:
        await state.update_data(
            current_raw_material_id=raw_material.raw_material.pk,
            current_raw_material_name=raw_material.raw_material.name,
        )
        await message.answer("Введите требуемую массу (в кг)", reply_markup=set_weight_keyboard())
        await NewMincedMeatBatchForm.set_weight.set()
    else:

        raw_meat_batches = list(
            set(
                RawMeatBatch.objects.filter(
                    weight__gt=0, raw_material_id=raw_material.pk, condition="chilled", is_future_batch=False
                ).all()
            )
        )

        raw_meat_batches = [
            meat_batch
            for meat_batch in raw_meat_batches
            if not get_from_dict_list(state_data["raw_meat_batches"], "id", meat_batch.pk)
        ]

        await message.answer(
            "Выбранный вариант не существует. Попробуйте еще раз",
            reply_markup=set_raw_materials_keyboard(raw_meat_batches),
        )


@dp.message_handler(state=NewMincedMeatBatchForm.set_raw_meat_batch)
async def set_raw_meat_batch_handler(message: Message, state: FSMContext):
    state_data = await state.get_data()
    raw_meat_batch = RawMeatBatch.objects.filter(production_id=message.text).first()
    if raw_meat_batch:
        await state.update_data(current_raw_meat_batch_id=raw_meat_batch.pk)
        text = f"""Введите требуемую массу (в кг)\n\nНаличие на складе: {raw_meat_batch.weight} кг"""
        await message.answer(text, reply_markup=set_weight_keyboard())
        await NewMincedMeatBatchForm.set_weight.set()
    else:
        raw_meat_batches = list(
            set(
                RawMeatBatch.objects.filter(
                    weight__gt=0,
                    raw_material_id=state_data["current_raw_material_id"],
                    condition="chilled",
                    is_future_batch=False,
                ).all()
            )
        )
        await message.answer(
            "Выбранный вариант не существует. Попробуйте еще раз",
            reply_markup=set_raw_meat_batch_keyboard(raw_meat_batches),
        )


@dp.message_handler(
    lambda message: re.match(FLOAT_REGEX, message.text) or message.text == "Все",
    state=NewMincedMeatBatchForm.set_weight,
)
async def set_weight_handler(message: Message, state: FSMContext):
    state_data = await state.get_data()
    current_weight_str = None
    if message.text.isnumeric():
        current_weight = Decimal(message.text)
        current_weight_str = message.text
    else:
        if message.text == "Все":
            current_weight = None
        else:
            return message.answer("Введите число или нажмите 'Все'")
    raw_meat_batches = []
    max_weight = 0
    for raw_meat_batch in RawMeatBatch.objects.filter(
        raw_material__name__icontains=state_data["current_raw_material_name"]
    ).order_by("created_at"):
        if not raw_meat_batch.weight:
            continue
        max_weight += raw_meat_batch.weight
        if current_weight is not None and current_weight <= 0:
            break
        if current_weight is None:
            raw_meat_batches.append(
                {
                    "id": raw_meat_batch.id,
                    "weight": raw_meat_batch.weight,
                }
            )
        else:
            raw_meat_batches.append(
                {
                    "id": raw_meat_batch.id,
                    "weight": raw_meat_batch.weight if raw_meat_batch.weight < current_weight else current_weight,
                }
            )
            current_weight -= Decimal(raw_meat_batch.weight)
    if current_weight is not None and current_weight > 0:
        return await message.answer(f"Такой массы нет на складе. Максимальная масса: {max_weight} кг")
    if not current_weight_str:
        current_weight_str = str(max_weight)
    await state.update_data(current_raw_meat_batch_weight=current_weight_str)
    raw_meat_batches = state_data["raw_meat_batches"] + raw_meat_batches
    await state.update_data(
        raw_meat_batches=raw_meat_batches,
        current_raw_material_id=None,
        current_raw_material_name=None,
        current_raw_meat_batch_weight=None,
        current_raw_meat_batch_id=None,
    )
    text = (
        "Предпросмотр заготовки\n\nИспользуемое сырье:\n"
        f"{await generate_recipe_raw_meat_batches_and_meat_blanks_text(state)}"
    )

    await message.answer(text, reply_markup=preview_keyboard_meat_batch())
    await NewMincedMeatBatchForm.preview.set()


@dp.message_handler(state=NewMincedMeatBatchForm.set_weight)
async def set_weight_decimal_error_handler(message: Message, state: FSMContext):
    await message.answer(text="Масса должна быть числом", reply_markup=return_keyboard())


@dp.message_handler(text="Добавить сырье", state=NewMincedMeatBatchForm.preview)
async def preview_add_raw_material_handler(message: Message, state: FSMContext):
    state_data = await state.get_data()

    meat_batches = RawMeatBatch.get_available_chilled()
    meat_batches = [
        meat_batch
        for meat_batch in meat_batches
        if not get_from_dict_list(state_data["raw_meat_batches"], "id", meat_batch.pk)
    ]

    if not meat_batches:
        await message.answer(text="Доступное сырье отсутствует")
        return

    await message.answer("Выберите сырье для фарша", reply_markup=set_raw_materials_keyboard(meat_batches))
    await NewMincedMeatBatchForm.set_raw_materials.set()


@dp.message_handler(text="Подтвердить", state=NewMincedMeatBatchForm.preview)
async def set_previev_handler(message: Message, state: FSMContext):
    await message.answer("Укажите количество замесов", reply_markup=return_keyboard())
    await NewMincedMeatBatchForm.set_number_mix.set()


@dp.message_handler(lambda message: message.text.isdigit(), state=NewMincedMeatBatchForm.set_number_mix)
async def set_number_mix_handler(message: Message, state: FSMContext):
    number_mix = int(message.text)
    await state.update_data(number_mix=number_mix)
    await message.answer("Введите название рецепта или выберите ниже", reply_markup=set_recipe_keyboard())
    await NewMincedMeatBatchForm.set_recipe.set()


@dp.message_handler(state=NewMincedMeatBatchForm.set_number_mix)
async def set_number_mix_digit_error_handler(message: Message, state: FSMContext):
    await message.answer("Количество замесов должно быть числом", reply_markup=return_keyboard())


@dp.message_handler(state=NewMincedMeatBatchForm.set_recipe)
async def set_recipe_handler(message: Message, state: FSMContext):
    recipe = Recipe.objects.filter(name__icontains=message.text).first()

    if not recipe:
        recipe = Recipe
    await state.update_data(recipe_id=recipe.pk)
    state_data = await state.get_data()
    await message.answer("Выберите производственную линию", reply_markup=set_line_minced_meat_keyboard(state_data))
    await NewMincedMeatBatchForm.set_line_type.set()


@dp.callback_query_handler(Text(startswith="minced_meat_batch_line"), state=NewMincedMeatBatchForm.set_line_type)
async def minced_meat_batch_line(call: types.CallbackQuery, state: FSMContext):
    await call.message.delete()
    await state.update_data(work_line=int(call.data.split("-")[1]))
    await call.message.answer("В какое время будет доставлен фарш", reply_markup=set_nigth_minced_meat_keyboard())
    await NewMincedMeatBatchForm.set_night.set()


@dp.callback_query_handler(Text(startswith="minced_meat_batch_night"), state=NewMincedMeatBatchForm.set_night)
async def minced_meat_batch_night(call: types.CallbackQuery, state: FSMContext):
    await call.message.delete()
    await state.update_data(is_night=bool(call.data.split("-")[1]))
    await call.message.answer(
        "Выберите дату прихода в цех. Можно ввести в формате 21.11.2020", reply_markup=set_arrival_date_keyboard()
    )
    await NewMincedMeatBatchForm.set_arrival_date.set()


@dp.message_handler(state=NewMincedMeatBatchForm.set_arrival_date)
async def set_arrival_date_handler(message: Message, state: FSMContext, roles: RolesModel):
    if message.text == "Сегодня":
        arrival_date = datetime.now()
    elif message.text == "Завтра":
        arrival_date = datetime.now() + timedelta(days=1)
    else:
        try:
            arrival_date = datetime.strptime(message.text, DATE_FORMAT)
        except ValueError:
            return await message.answer("Дата была введена в невером формате (правильный формат: 21.11.2020)")

    state_data = await state.get_data()

    start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)

    minced_meat_batch_count = MincedMeatBatch.get_by_date_range(start=start, end=end)

    production_id = (
        f"Ф{arrival_date.strftime('%d%m%Y')}{state_data['recipe_id']}/{minced_meat_batch_count.count() + 3}"
    )
    recipe = Recipe.objects.filter(pk=state_data["recipe_id"]).first()

    minced_meat_batch = await MincedMeatBatch.objects.acreate(
        production_id=production_id,
        line_type=state_data["work_line"],
        is_night=state_data["is_night"],
        number_mix=state_data["number_mix"],
        protein=state_data["protein"],
        fat=state_data["fat"],
        type="МКО" if "is_mko" in state_data else "ММО",
        moisture=state_data["moisture"],
        arrival_date=arrival_date,
        recipe_id=state_data["recipe_id"],
    )
    # print(json.dumps(state_data))

    for meat_blank_state in state_data["meat_blanks"]:
        await MincedMeatBatchMeatBlank.objects.acreate(
            minced_meat_batch_id=minced_meat_batch.pk,
            meat_blank_id=meat_blank_state["id"],
            weight=meat_blank_state["weight"],
        )

        meat_blank = MeatBlank.objects.filter(pk=meat_blank_state["id"]).first()
        meat_blank.weight -= float(meat_blank_state["weight"])
        await meat_blank.asave()

    if "is_mko" not in state_data:
        for raw_meat_batch_state in state_data["raw_meat_batches"]:
            await MincedMeatBatchRawMeatBatch.objects.acreate(
                minced_meat_batch_id=minced_meat_batch.pk,
                raw_meat_batch_id=raw_meat_batch_state["id"],
                weight=raw_meat_batch_state["weight"],
            )

            raw_meat_batches = RawMeatBatch.objects.filter(pk=raw_meat_batch_state["id"]).first()
            raw_meat_batches.weight -= float(raw_meat_batch_state["weight"])
            await raw_meat_batches.asave()

    else:
        used_second_minced_meat_weight = state_data.get("second_minced_meat_weight", 0)
        while used_second_minced_meat_weight > 0:
            available_second_minced_meat = SecondMincedMeat.get_available_second_minced_meat().order_by("created_at")
            second_minced_meat = available_second_minced_meat.first()
            logging.info(available_second_minced_meat)
            logging.info(second_minced_meat)
            if second_minced_meat:
                available_weight = second_minced_meat.get_available_weight()
                if used_second_minced_meat_weight > available_weight:
                    await MincedMeatBatchSecondMeatBlank.objects.acreate(
                        minced_meat_batch_id=minced_meat_batch.pk,
                        second_minced_meat_id=second_minced_meat.pk,
                        weight=available_weight,
                    )
                    used_second_minced_meat_weight -= available_weight
                elif used_second_minced_meat_weight <= available_weight:
                    await MincedMeatBatchSecondMeatBlank.objects.acreate(
                        minced_meat_batch_id=minced_meat_batch.pk,
                        second_minced_meat_id=second_minced_meat.pk,
                        weight=used_second_minced_meat_weight,
                    )
                    used_second_minced_meat_weight = 0
            if not second_minced_meat and used_second_minced_meat_weight > 0:
                last_created_minced_meat_batch_second_meat = (
                    MincedMeatBatchSecondMeatBlank.objects.filter(minced_meat_batch_id=minced_meat_batch.pk)
                    .order_by("-created_at")
                    .first()
                )
                last_created_minced_meat_batch_second_meat.weight += used_second_minced_meat_weight
                await last_created_minced_meat_batch_second_meat.asave()
                used_second_minced_meat_weight = 0

    mixes = list()
    mixes_ids = list()
    for i in range(state_data["number_mix"]):
        mix_production_id = production_id + f"/{i + 1}"

        mix_id = await MincedMeatBatchMix.objects.acreate(
            minced_meat_batch_id=minced_meat_batch.pk,
            production_id=mix_production_id,
        )
        mixes_ids.append((mix_id.id, mix_id.minced_meat_batch_id))
        mixes.append(mix_production_id)
    raw_materials_preview = await generate_recipe_for_minced_meat_mix(minced_meat_batch.pk)
    mixes_text = "\n".join(mixes)
    text = f"""    фарш успешно зарегистрирован

ID фарша: {production_id}
Рецепт: {recipe.name}

Используемое сырье и заготовки:
{raw_materials_preview}

Созданные замесы:
{mixes_text}

"""

    await message.answer(text, reply_markup=main_menu_keyboard(message.from_user.id))
    await state.finish()
