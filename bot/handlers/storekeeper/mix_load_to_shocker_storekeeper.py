import re
from datetime import datetime, timedelta

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import StatesGroup, State

from Web.CRM.dataclasses import RolesModel
from Web.CRM.models import MincedMeatBatchMix, ShockerMixLoad, Status, ShockerCamera, MincedMeatBatchMixConsumptionRaw, MincedMeatBatchMixConsumptionMeatBlank, MincedMeatBatchMixConsumptionSecondMeatBlank, MincedMeatBatchRawMeatBatch, MincedMeatBatchMeatBlank, MincedMeatBatchSecondMeatBlank
from data.constants import FLOAT_REGEX
from bot.keyboards.second_minced_meat.second_minced_meat_kb import back_to_main_menu, select_shocker
from bot.loader import dp
import pytz


class ShockCameraLoad(StatesGroup):
    shock_chamber_num = State()
    pallet_number = State()
    weight_pallet = State()
    box_count = State()
    weight_bruto = State()
    unload = State()


async def create_consumption_for_shocker_load(mix: MincedMeatBatchMix):
    """
    Создает записи consumption для списания сырья при загрузке в шокер.
    Это обновляет графу "Остатки/перераспределение" в админке фарша.
    """
    batch = mix.minced_meat_batch
    
    # 1. Создаем consumption записи для сырья, привязанного к партии фарша
    raw_rels = MincedMeatBatchRawMeatBatch.objects.filter(minced_meat_batch=batch).all()
    for rel in raw_rels:
        # Проверяем, не создана ли уже запись consumption для этого замеса и сырья
        existing_consumption = MincedMeatBatchMixConsumptionRaw.objects.filter(
            minced_meat_batch_mix=mix,
            raw_meat_batch=rel.raw_meat_batch
        ).first()
        
        if not existing_consumption:
            # Создаем consumption запись с весом, пропорциональным количеству замесов
            total_mixes = batch.number_mix or 1
            weight_per_mix = float(rel.weight) / float(total_mixes)
            
            await MincedMeatBatchMixConsumptionRaw.objects.acreate(
                minced_meat_batch_mix=mix,
                raw_meat_batch=rel.raw_meat_batch,
                weight=weight_per_mix
            )
    
    # 2. Создаем consumption записи для заготовок, привязанных к партии фарша
    blank_rels = MincedMeatBatchMeatBlank.objects.filter(minced_meat_batch=batch).all()
    for rel in blank_rels:
        # Проверяем, не создана ли уже запись consumption для этого замеса и заготовки
        existing_consumption = MincedMeatBatchMixConsumptionMeatBlank.objects.filter(
            minced_meat_batch_mix=mix,
            meat_blank=rel.meat_blank
        ).first()
        
        if not existing_consumption:
            # Создаем consumption запись с весом, пропорциональным количеству замесов
            total_mixes = batch.number_mix or 1
            weight_per_mix = float(rel.weight) / float(total_mixes)
            
            await MincedMeatBatchMixConsumptionMeatBlank.objects.acreate(
                minced_meat_batch_mix=mix,
                meat_blank=rel.meat_blank,
                weight=weight_per_mix
            )

    # 3. Создаем consumption записи для вторфарша, привязанного к партии фарша
    second_meat_rels = MincedMeatBatchSecondMeatBlank.objects.filter(minced_meat_batch=batch).all()
    for rel in second_meat_rels:
        # Проверяем, не создана ли уже запись consumption для этого замеса и вторфарша
        existing_consumption = MincedMeatBatchMixConsumptionSecondMeatBlank.objects.filter(
            minced_meat_batch_mix=mix,
            second_minced_meat=rel.second_minced_meat
        ).first()
        
        if not existing_consumption:
            # Создаем consumption запись с весом, пропорциональным количеству замесов
            total_mixes = batch.number_mix or 1
            weight_per_mix = float(rel.weight) / float(total_mixes)
            
            await MincedMeatBatchMixConsumptionSecondMeatBlank.objects.acreate(
                minced_meat_batch_mix=mix,
                second_minced_meat=rel.second_minced_meat,
                weight=weight_per_mix
            )


@dp.callback_query_handler(Text(startswith="mars_to_shocker"))
async def load_minced_meat_to_shocker(call: types.CallbackQuery, state: FSMContext, roles: RolesModel):
    await call.message.delete()
    await call.message.answer("Введите номер палета", reply_markup=back_to_main_menu())
    await ShockCameraLoad.pallet_number.set()


@dp.callback_query_handler(Text(startswith="select_shocker"), state=ShockCameraLoad.shock_chamber_num)
async def farshov_tiler(call: types.CallbackQuery, state: FSMContext):
    shocker_id = int(call.data.split("-")[1])
    await state.update_data(shocker_id=shocker_id)
    await call.message.answer("Введите вес паллеты", reply_markup=back_to_main_menu())
    await ShockCameraLoad.weight_pallet.set()


@dp.message_handler(lambda message: re.match(FLOAT_REGEX, message.text), state=ShockCameraLoad.box_count)
async def load_minced_meat_to_box_count(message: types.Message, state: FSMContext):
    await state.update_data(box_count=int(message.text), type=1)
    state_data = await state.get_data()
    mix = MincedMeatBatchMix.objects.get(pk=state_data["mix_id"])
    mix.statuses.create(status_id=Status.objects.get(codename="to_shocker_finish").pk)
    
    # Создаем consumption записи для обновления графы "Остатки/перераспределение"
    await create_consumption_for_shocker_load(mix)
    
    await ShockerMixLoad.objects.acreate(
        shocker_id=state_data["shocker_id"], minced_meat_batch_mix_id=state_data["mix_id"], additional_data=state_data
    )
    await state.finish()
    await message.answer("Загрузка в шокер успешна")


@dp.message_handler(lambda message: re.match(FLOAT_REGEX, message.text), state=ShockCameraLoad.pallet_number)
async def load_minced_meat_to_pallet_number(message: types.Message, state: FSMContext, roles: RolesModel):
    moscow_tz = pytz.timezone("Europe/Moscow")
    now_moscow = datetime.now(moscow_tz)
    start = now_moscow.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)
    mix = MincedMeatBatchMix.objects.filter(
        statuses__additional_data={"pallet": int(message.text)}, created_at__gt=start, created_at__lt=end
    ).first()

    if not mix or mix.statuses.filter(status=Status.objects.get(codename="unload_shocker_finish")).first():
        await message.answer("Замес на указанном палете не найден!", reply_markup=back_to_main_menu())
        return

    mix.statuses.create(status_id=Status.objects.get(codename="to_shocker").pk)
    await state.update_data(mix_id=mix.pk)
    await state.update_data(pallet=int(message.text))
    shocker_list = sorted([key for key, val in ShockerCamera.get_available_shocker().items() if val > 0])
    if not shocker_list:
        await message.bot.send_message(
            roles.technologist.telegram_id,
            "Все шокеры заняты! Нету возможности загрузить новые замес фарша! Требуется ваше внимение!",
        )

    await message.answer("Выберите камеру шоковой заморозки", reply_markup=select_shocker())
    await ShockCameraLoad.shock_chamber_num.set()


@dp.message_handler(lambda message: re.match(FLOAT_REGEX, message.text), state=ShockCameraLoad.weight_pallet)
async def load_minced_meat_to_pallet_weight(message: types.Message, state: FSMContext):
    await state.update_data(pallet_weight=int(message.text))
    await message.answer("Введите вес брутто", reply_markup=back_to_main_menu())
    await ShockCameraLoad.weight_bruto.set()


@dp.message_handler(lambda message: re.match(FLOAT_REGEX, message.text), state=ShockCameraLoad.weight_bruto)
async def load_minced_meat_to_pallet_weight_2(message: types.Message, state: FSMContext):
    await state.update_data(brutto_weight=int(message.text))
    await message.answer("Введите кол-во ящиков", reply_markup=back_to_main_menu())
    await ShockCameraLoad.box_count.set()


@dp.message_handler(state=ShockCameraLoad.box_count)
@dp.message_handler(state=ShockCameraLoad.pallet_number)
async def num_error(message: types.Message, state: FSMContext):
    await message.answer("Данный параметр должен быть числом!")


@dp.message_handler(state=ShockCameraLoad.weight_pallet)
@dp.message_handler(state=ShockCameraLoad.weight_bruto)
async def set_weight_error(message: types.Message, state: FSMContext):
    await message.answer("Масса должна быть числом", reply_markup=back_to_main_menu())
