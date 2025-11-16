from aiogram.dispatcher import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from Web.CRM.models import MincedMeatBatchMix, Status, MeatBlank, MincedMeatBatch
from Web.CRM.dataclasses import RolesModel


from bot.keyboards.shared import skip_keyboard
from bot.keyboards.technologist.technologist_check_keyboard import set_continue_keyboard
from bot.loader import dp, bot
from bot.states.fhp_analysis import FHPAnalysis
from bot.states.new_raw_meat_batch_form import NewRawMeatBatchForm


@dp.callback_query_handler(text_contains="tech_check_app", state="*")
async def technologist_check_approve_handler(call: CallbackQuery, state: FSMContext, roles: RolesModel):
    from bot.utils.text_info import get_meat_blank_text_before_storekeepr

    from bot.handlers.laboratory.mixed_list_select import get_text_for_fhp_mix

    data = call.data.split(":")
    user_id, stage, value = data[1], data[2], data[3]
    if stage == "fhp_is_bad":
        mix = MincedMeatBatchMix.objects.get(pk=value)
        mix.statuses.get_or_create(status_id=Status.objects.get(codename="laboratory_analyze_again").pk)
        await bot.send_message(
            user_id,
            f"Разрешен повторный анализ ФХП - Гл.технолог Лузин Е.С\n\n{await get_text_for_fhp_mix(mix)}",
            reply_markup=set_continue_keyboard(stage, value),
        )
    elif stage == "defrost_again":
        meat_blank: MeatBlank = await MeatBlank.objects.filter(pk=value).afirst()
        date = await meat_blank.statuses.acreate(status=Status.objects.get(codename="loaded_to_defroster"))
        reply_markup = InlineKeyboardMarkup().add(
            InlineKeyboardButton(text="Выключить дефростер", callback_data=f"d_defrost-{meat_blank.pk}")
        )
        await bot.send_message(
            roles.defrost_manager.telegram_id,
            text=(await get_meat_blank_text_before_storekeepr(meat_blank.pk))
            + f"\nЗагружен в дефростер в {date.created_at:%d-%m-%Y %H:%M}",
            reply_markup=reply_markup,
        )

    else:
        await bot.send_message(
            user_id, "Приёмка согласована - Гл.технолог Лузин Е.С", reply_markup=set_continue_keyboard(stage, value)
        )
    await call.message.delete()


@dp.callback_query_handler(text_contains="tech_line", state="*")
async def technologist_check_cancel_handler_2(call: CallbackQuery, state: FSMContext):
    call_data, answer, mix_id = call.data.split(":")
    if answer == "no":
        await call.message.answer("Не принимаем ни каких действие с данной линией.")
        await call.message.delete()
    if answer == "yes":
        # print(call_data,answer,mix_id)
        mix = MincedMeatBatchMix.objects.get(pk=mix_id)
        prod_line_two_data = mix.minced_meat_batch.production_id.split("/")
        previos_num = int(prod_line_two_data[1]) - 1
        # print(f'{prod_line_two_data[0]}/{previos_num}')
        minced_meat_batch = MincedMeatBatch.objects.filter(production_id__contains=f"/{previos_num}").first()
        minced_meat_batch.line_type = 10
        minced_meat_batch.save()
        await call.message.answer("Линия переключена на совместную работу")
        await call.message.delete()


@dp.callback_query_handler(text_contains="tech_check_can", state="*")
async def technologist_check_cancel_handler(call: CallbackQuery, state: FSMContext, roles: RolesModel):
    data = call.data.split(":")
    stage, user_id, value = data[2], data[1], data[3]
    if stage == "fhp_is_bad":
        mix = MincedMeatBatchMix.objects.get(pk=value)
        from bot.handlers.mixer.mixer import mixer_notify_good_fhp_mix_meat

        mix.statuses.get_or_create(status_id=Status.objects.get(codename="mix_is_blocked_analyze").pk)
        await mixer_notify_good_fhp_mix_meat(mix.pk, roles, True)
        await bot.send_message(user_id, "Замес заблокирован! - Гл.технолог Лузин Е.С")
    elif stage == "defrost_again":
        await call.message.answer("Повторное включение отклонено!")
        await bot.send_message(roles.defrost_manager.telegram_id, "Повторное включение дефростера отклонено!")
    else:
        await bot.send_message(user_id, "Приёмка запрещена. Оформлять на возврат - Гл.технолог Лузин Е.С")
    await call.message.delete()


@dp.callback_query_handler(text_contains="check_continue", state="*")
async def technologist_check_approve_handler_2(call: CallbackQuery, state: FSMContext):
    data = call.data.split(":")
    stage, value = data[1], data[2]
    if stage == "body_temperature_truck":
        await state.update_data(body_temperature_truck=value)
        await call.message.answer(text="Введите дату производства (пример: 20.01.2022)", reply_markup=skip_keyboard())
        await call.message.delete()
        await NewRawMeatBatchForm.set_manufacture_date.set()
    elif stage == "temperature":
        await state.update_data(temperature=value)
        await call.message.answer("Пришлите фотографию паллеты", reply_markup=skip_keyboard())
        await call.message.delete()
        await NewRawMeatBatchForm.set_photo_pallet.set()

    elif stage == "fhp_is_bad":
        await state.update_data(mix_id=value)
        await call.message.answer("Введите массовую долю жиров")
        await FHPAnalysis.set_fats.set()
        await call.message.delete()
    else:
        await call.message.answer("Пришлите фото температурного режима продукции", reply_markup=skip_keyboard())
        await call.message.delete()
        await NewRawMeatBatchForm.set_photo_temperature.set()
