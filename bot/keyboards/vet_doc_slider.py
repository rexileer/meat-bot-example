from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery

from Web.CRM.constans.positions import position_dict
from Web.CRM.models import RawMaterial, Users
from bot.handlers.technologist.utils.technologist_check import set_technologist_check_message
from bot.keyboards.shared import skip_keyboard
from bot.keyboards.technologist.technologist_check_keyboard import set_technologist_check_keyboard
from bot.loader import dp, bot
from bot.states.new_raw_meat_batch_form import NewRawMeatBatchForm
from bot.utils.api.vet import VetResponse


async def choice_end(call, state):
    data = await state.get_data()
    responses_json = data.get("chosen_responses")
    if responses_json:
        responses = [VetResponse.parse_raw(d) for d in responses_json]
        vet_numbers = [response.document_number for response in responses]
        vet_dates = [response.document_date for response in responses]
        await state.update_data(
            organization_vet=responses[0].organization,
            organization=responses[0].organization,
            manufacturer=responses[0].manufacturer,
            weight=str(sum((response.weight for response in responses))).replace(",", "."),
            link_vet="\n".join([response.link for response in responses]),
            document_number_vet="/".join(vet_numbers) if "None" not in vet_numbers else "",
            document_date_vet="/".join(vet_dates) if "None" not in vet_dates else "",
            manufacture_date_vet="/".join([response.manufacture_date for response in responses]),
            expiration_date_vet="/".join([response.expiration_date for response in responses]),
            weight_vet=str(sum((response.weight for response in responses))).replace(",", "."),
        )
        min_osg = min([int(vet_doc.split("ОСГ: ")[-1]) for vet_doc in [response.link for response in responses]])
        await state.update_data(min_osg=min_osg)
        if min_osg <= 0:
            state_data = await state.get_data()
            condition = state_data.get("condition")
            material_id = state_data.get("raw_material_id")
            raw_material = RawMaterial.objects.get(id=material_id)
            msg = await set_technologist_check_message(
                raw_material.name, condition, "manufacture_date_vet", f"просрочено на {abs(min_osg)}"
            )
            await bot.send_message(
                Users.objects.get(position__code_name=position_dict["technologist"]),
                msg,
                reply_markup=set_technologist_check_keyboard(call.from_user.id, "manufacture_date_vet", min_osg),
            )
            await bot.send_message(
                call.from_user.id, "Приёмка временно запрещена. Дождитесь ответа технолога, что бы продолжить."
            )
            await NewRawMeatBatchForm.set_check.set()
            await call.message.delete()
            await state.update_data(blocked=True)
            return False
        return True
    return False


async def set_slider_page(page=0, state=None):
    if page == -1:
        return
    data = await state.get_data()
    json_data = data.get("slider_data")
    data = [VetResponse.parse_raw(d) for d in json_data]
    total_weight = str(sum((d.weight for d in data))).replace(",", ".")
    message = (
        f"Общий вес: {total_weight}\n\n"
        f"Наименование продукции: {data[page].production}\n"
        f"Масса: {data[page].weight}\n\n"
        f"Ветка {page + 1}/{len(data)}"
    )

    prev_sign = "◀"
    next_sign = "▶"
    if page == 0:
        prev_sign = "⏹"
    if page + 1 == len(data):
        next_sign = "⏹"

    buttons = [
        [
            InlineKeyboardButton(text=prev_sign, callback_data=f"change_page:{page - 1 if page != 0 else None}"),
            InlineKeyboardButton(
                text=next_sign, callback_data=f"change_page:{page + 1 if page + 1 != len(data) else None}"
            ),
        ],
        [InlineKeyboardButton(text="Добавить", callback_data=f"choice:{page}")],
        [InlineKeyboardButton(text="Добавить всё", callback_data="add_all")],
        [InlineKeyboardButton(text="Завершить", callback_data="final")],
    ]

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    return message, keyboard


@dp.callback_query_handler(text_contains="choice", state=NewRawMeatBatchForm.set_choice_vet_doc)
async def choice_page_handler(call: CallbackQuery, state):
    page = int(call.data.split(":")[1])
    data = await state.get_data()
    slider_data = data.get("slider_data")
    chosen_responses = data.get("chosen_responses")
    chosen_responses.append(slider_data[page])
    slider_data.pop(page)
    await state.update_data(slider_data=slider_data)
    await state.update_data(chosen_responses=chosen_responses)

    if page == len(slider_data):
        page -= 1

    if len(slider_data) == 0:
        result = await choice_end(call, state)
        if result:
            await call.message.answer("Пришлите фото температурного режима продукции", reply_markup=skip_keyboard())
            await NewRawMeatBatchForm.set_photo_temperature.set()
        return

    msg, keyboard = await set_slider_page(page, state)
    await call.message.edit_text(msg, reply_markup=keyboard)


@dp.callback_query_handler(text_contains="add_all", state=NewRawMeatBatchForm.set_choice_vet_doc)
async def choice_all_pages_handler(call: CallbackQuery, state):
    data = await state.get_data()
    slider_data = data.get("slider_data")
    chosen_responses = data.get("chosen_responses")
    chosen_responses.extend(slider_data)
    await state.update_data(chosen_responses=chosen_responses)
    result = await choice_end(call, state)
    if result:
        await call.message.answer("Пришлите фото температурного режима продукции", reply_markup=skip_keyboard())
        await call.message.delete()
        await NewRawMeatBatchForm.set_photo_temperature.set()


@dp.callback_query_handler(text_contains="change_page", state=NewRawMeatBatchForm.set_choice_vet_doc)
async def change_page_handler(call: CallbackQuery, state):
    page = call.data.split(":")[1]
    if page == "None":
        return await call.answer("Веток больше нет")
    msg, keyboard = await set_slider_page(int(page), state)
    await call.message.edit_text(msg, reply_markup=keyboard)


@dp.callback_query_handler(text_contains="final", state=NewRawMeatBatchForm.set_choice_vet_doc)
async def final_handler(call: CallbackQuery, state):
    result = await choice_end(call, state)
    state_data = await state.get_data()
    if result and not state_data.get("blocked"):
        await call.message.delete()
        await call.message.answer("Пришлите фото температурного режима продукции", reply_markup=skip_keyboard())
        await NewRawMeatBatchForm.set_photo_temperature.set()
    return await call.answer("Выберите хотя бы 1 ветку")
