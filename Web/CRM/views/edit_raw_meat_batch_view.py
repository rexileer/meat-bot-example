import asyncio
from typing import Optional

from aiogram.dispatcher.filters.state import StatesGroup, State
from django.views.generic import TemplateView

from bot.loader import bot


class EditRawMeatBatchForm(StatesGroup):
    set_photo_ypd = State()
    set_photo_ttn = State()
    set_photo_tn = State()
    set_photo_vet = State()
    set_photo_temperature = State()
    set_photo_pallet = State()


class EditRawMeatBatchView(TemplateView):
    template_name = "admin/custom_message.html"

    def get_state_by_field(self, field: str) -> Optional[State]:
        state_by_field_mapping = {
            "photo_ypd": EditRawMeatBatchForm.set_photo_ypd,
            "photo_ttn": EditRawMeatBatchForm.set_photo_ttn,
            "photo_tn": EditRawMeatBatchForm.set_photo_tn,
            "photo_vet": EditRawMeatBatchForm.set_photo_vet,
            "photo_temperature": EditRawMeatBatchForm.set_photo_temperature,
            "photo_pallet": EditRawMeatBatchForm.set_photo_pallet,
        }
        return state_by_field_mapping.get(field)

    def get_bot_message_by_field(self, field: str) -> Optional[str]:
        bot_message_by_field_mapping = {
            "photo_ypd": "Пришлите фото УПД",
            "photo_ttn": "Пришлите фото ТТН",
            "photo_tn": "Пришлите фото ТН",
            "photo_vet": "Пришлите фото ЭСВД",
            "photo_temperature": "Пришлите фото температурного режима",
            "photo_pallet": "Пришлите фото палетты",
        }
        return bot_message_by_field_mapping.get(field)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.request.GET.get("field"):
            # field = self.request.GET["field"]

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            bot_info = loop.run_until_complete(bot.get_me())
            # loop.run_until_complete(
            #     send_edit_raw_meat_batch_message(
            #         tg_message=self.get_bot_message_by_field(field),
            #         raw_meat_batch_id=context["raw_meat_batch_id"],
            #         state=self.get_state_by_field(field),
            #     )
            # )
            # loop.close()

            message = f"Продолжить редактирование можно в боте @{bot_info.username}"

        else:
            message = "Редактируемое поле не было передано"

        context["title"] = "Редактирование сырья"
        context["site_header"] = "CRM"
        context["has_permission"] = True
        context["message"] = message

        return context
