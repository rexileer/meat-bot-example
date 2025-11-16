from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.types import Message

from Web.CRM.dataclasses import RolesModel
from Web.CRM.models import MeatBlankRawMeatBatch, MeatBlank, Status
from bot.keyboards.rastarshik import rastarshchik_action
from bot.loader import dp, bot
from bot.states.actual_weight_form import ActualWeight
from bot.utils.text_info import raw_meat_blank_text_final


@dp.callback_query_handler(Text(startswith="start_actual_weight"))
async def start_actual_weight_blank(call: types.CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    product_id = int(call.data.split("-")[1])
    data = MeatBlankRawMeatBatch.objects.filter(meat_blank_id=product_id).all()
    all_weight = sum(float(meat_blank.weight) for meat_blank in data)
    if "actual_weight_state" not in state_data:
        await state.update_data(
            {"actual_weight_state": len(data) - 1, "meat_blank_id": product_id, "all_weight": all_weight}
        )

    text = "\n".join(
        [
            "Укажите фактический вес для сырья:\n",
            f"{data[len(data) - 1].raw_meat_batch.raw_material.name} - "
            f"{data[len(data) - 1].raw_meat_batch.production_id}",
        ]
    )
    await call.message.answer(text)
    await call.message.edit_reply_markup(None)
    await ActualWeight.weight.set()


@dp.message_handler(state=ActualWeight.weight)
async def set_actual_weight(message: Message, state: FSMContext, roles: RolesModel):
    try:
        new_weight = float(message.text)
    except Exception:
        await message.answer("Введенное значение должно быть числом!")
        return
    state_data = await state.get_data()
    data_batches = MeatBlankRawMeatBatch.objects.filter(meat_blank_id=state_data["meat_blank_id"]).all()
    current_raw_material = data_batches[state_data["actual_weight_state"]]
    if current_raw_material.raw_meat_batch.weight <= 0 and new_weight > current_raw_material.weight:
        await message.answer("Ошибка! Вы не можете взять больше продукции, т.к нехватка на складе!")
        return
    if not (float(current_raw_material.weight) - 100 <= new_weight <= float(current_raw_material.weight) + 200):
        await message.answer("Ошибка! Вес отличается от норм! перепроверьте и введите данные сначала!")
        text = "\n".join(
            [
                "Укажите фактический вес для сырья:\n",
                f"{current_raw_material.raw_meat_batch.raw_material.name} - "
                f"{current_raw_material.raw_meat_batch.production_id}",
            ]
        )
        await message.answer(text)
        return

    await state.update_data({f"old-weight_{current_raw_material.pk}": float(current_raw_material.weight)})
    if state_data["actual_weight_state"] - 1 < 0:
        state_data.update({f"weight_{current_raw_material.pk}": new_weight})
        new_summ_weight = sum([state_data[f"weight_{batch.pk}"] for batch in data_batches])
        for data_batch in data_batches:
            data_batch.weight = state_data[f"weight_{data_batch.pk}"]
            data_batch.save()
        current_raw_material.raw_meat_batch.weight -= new_weight - current_raw_material.weight
        current_raw_material.raw_meat_batch.save()
        current_raw_material.weight += new_weight - current_raw_material.weight
        current_raw_material.save()

        await state.update_data(all_weight=new_summ_weight)
        meat_blank: MeatBlank = await MeatBlank.objects.aget(pk=state_data["meat_blank_id"])
        meat_blank.weight_receipt = meat_blank.weight
        meat_blank.weight = new_summ_weight
        meat_blank.save()
        await meat_blank.statuses.acreate(
            status=Status.objects.get(codename="storekeeper_outputed"), additional_data=(await state.get_data())
        )
        await state.finish()
        await message.answer("Заготовка отправлена растращику!")
    else:
        await state.update_data(
            {
                "actual_weight_state": state_data["actual_weight_state"] - 1,
                f"weight_{current_raw_material.pk}": float(new_weight),
            }
        )
        next_raw_material = data_batches[state_data["actual_weight_state"] - 1]
        text = "\n".join(
            [
                "Укажите фактический вес для сырья:\n",
                f"{next_raw_material.raw_meat_batch.raw_material.name} - "
                f"{next_raw_material.raw_meat_batch.production_id}",
            ]
        )
        await message.answer(text)


async def rastarshik_notify_meat_blank(meat_blank_id, roles: RolesModel):
    meat_blank = MeatBlank.objects.get(pk=meat_blank_id)
    raw_materials_info = await raw_meat_blank_text_final(meat_blank_id)
    status = await meat_blank.statuses.filter(status__codename="storekeeper_outputed").afirst()
    text = "\n".join(
        [
            "Была создана новая заготовка",
            f"ID заготовки: {meat_blank.production_id}",
            "Используемое сырье:",
            f"{raw_materials_info}",
            f'\nСуммарный вес {status.additional_data["all_weight"]}',
        ]
    )
    await bot.send_message(
        chat_id=roles.rastarshchik_meat_blanks.telegram_id, text=text, reply_markup=rastarshchik_action(meat_blank_id)
    )
