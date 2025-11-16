from Web.CRM.models import MincedMeatBatchMix

stages = {
    "body_temperature_truck": "не соответ. температуры в машине",
    "temperature": "не соответ. температуры сырья",
    "manufacture_date_vet": "не соответствие даты производства и эВСД",
    "fhp_is_bad": "ФХП анализ не прошел по стандартам!",
}

conditions = {"chilled": "Охлажденное", "frozen": "Замороженое"}


async def set_technologist_check_message(type, condition, stage, value):
    message = (
        f"Заблокирована приёмка сырья.\n\n"
        f"Тип сырья - {type}, {conditions[condition]}\n\n"
        f"Причина - {stages[stage]}: {value}"
    )

    return message


async def set_technologist_check_message_fhp(mix_id):
    mix = MincedMeatBatchMix.objects.get(pk=mix_id)
    message = f"""Фарш не прошел проверку на ФХП анализ!
ID фарша {mix.minced_meat_batch.production_id}
Замес {mix.production_id}
"""
    return message
