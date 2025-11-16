import asyncio
import re
from datetime import datetime
from decimal import Decimal

from django.contrib import admin
from django import forms
from django.contrib.admin import AdminSite
from django.contrib.admin.views.main import ChangeList
from django.db.models import Sum, QuerySet
from django.utils.safestring import mark_safe
from django_minio_backend import MinioBackend
from rangefilter.filters import DateRangeFilter, DateTimeRangeFilter

from Web.CRM.filters import (
    SecondMincedMeatFilter,
    MKOMincedMeatFilter,
    StorageStatusDateRangeFilter,
)
from Web.CRM.models import (
    Users,
    Recipe,
    MincedStandards,
    SecondMincedMeat,
    RawMeatBatch,
    MeatBlank,
    MeatBlankRawMeatBatch,
    ShockerCamera,
    MincedMeatBatch,
    Status,
    TotalMincedMeatBatchStatus,
    RawMaterialParams,
    ShockerMixLoad,
    BufferPalletMars,
    Shipment,
    MincedMeatBatchMix,
    MincedMeatBatchStatus,
    TTNType,
    Tilers,
    MincedMeatBatchRawMeatBatch,
    SecondMincedMeatStatus,
    MincedMeatBatchSecondMeatBlank,
    MincedMeatBatchMeatBlank,
    MincedMeatBatchMixConsumptionRaw,
    MincedMeatBatchMixConsumptionMeatBlank,
    MincedMeatBatchMixConsumptionSecondMeatBlank,
    WarehouseResponses,
)

from bot.utils.helpers import beautify_decimal, convert_to_localtime
from data.config import env
from aiogram import Bot
from django.contrib import messages
from django.utils.html import format_html
from django.db.models import Q


class CrmAdminSite(AdminSite):
    site_title = "CRM"
    site_header = "CRM"
    index_title = ""

    def get_app_list(self, request, *args):
        app_list = super().get_app_list(request)

        new_models = [
            {
                "name": "Добавить отгрузку",
                "admin_url": "/admin/CRM/set-recipe-new-shipment",
                "view_only": True,
            }
        ]

        for app in app_list:
            if app["app_label"] == "CRM":
                app["models"].extend(new_models)
        return app_list


crm_admin = CrmAdminSite()


@admin.register(Recipe, site=crm_admin)
class MincedRecipe(admin.ModelAdmin):
    fields = ("name",)
    readonly_fields = ("id",)


@admin.register(WarehouseResponses, site=crm_admin)
class WarehouseResponsesAdmin(admin.ModelAdmin):
    fields = ("res_date",)
    list_display = ("res_link",)

    def res_link(self, obj):
        day = obj.res_date.strftime("%Y%m%d")
        return format_html(
            f"<a href='/admin/CRM/datatables/minced_meat/{day}'>Отчет за {obj.res_date.strftime('%Y.%m.%d')}</a>"
        )

    res_link.short_description = "Ссылка на скачивание"


@admin.register(MincedStandards, site=crm_admin)
class MincedStandards(admin.ModelAdmin):
    fields = (
        "recipe",
        "protein_deviation_minus",
        "protein",
        "protein_deviation_plus",
        "fats_deviation_minus",
        "fats",
        "fats_deviation_plus",
        "moisture_deviation_minus",
        "moisture",
        "moisture_deviation_plus",
        "pitch_deviation_minus",
        "pitch",
        "pitch_deviation_plus",
    )
    list_display = (
        "recipe",
        "protein_deviation_minus",
        "protein",
        "protein_deviation_plus",
        "fats_deviation_minus",
        "fats",
        "fats_deviation_plus",
        "moisture_deviation_minus",
        "moisture",
        "moisture_deviation_plus",
        "pitch_deviation_minus",
        "pitch",
        "pitch_deviation_plus",
    )


class MyChangeList(ChangeList):
    def get_results(self, *args, **kwargs):
        super(MyChangeList, self).get_results(*args, **kwargs)
        q = self.result_list.aggregate(weight=Sum("weight"))
        if q["weight"]:
            type_second_minced_meat = (
                "Вторфарш"
                if self.result_list[0].type == 0
                else f"МКО{self.result_list[0].type}"
            )
            if "second_meat_type" in str(*args):
                self.weight = mark_safe(
                    f"<br>Суммарный вес для {type_second_minced_meat}: {q['weight']} "
                )
            else:
                self.weight = mark_safe(f"<br>Суммарный вес: {q['weight']} ")


@admin.register(SecondMincedMeat, site=crm_admin)
class SecondMincedMeatAdmin(admin.ModelAdmin):
    list_filter = (
        SecondMincedMeatFilter,
        ("created_at", DateTimeRangeFilter),
    )

    def get_changelist(self, request):
        return MyChangeList

    @admin.display(description="Дополнительные данные")
    def additional_data(self):
        texts = []
        if self.additional_data:
            if self.type in [2, 3]:
                texts.append(
                    "<br>".join(
                        [
                            f"Номер паллета: {self.additional_data['pallet']}",
                            f"Вес паллета: {self.additional_data['pallet_weight']}",
                            f"Кол-во коробок: {self.additional_data['box_count']}",
                            f"Вес брутто: {self.additional_data['brutto_weight']}",
                            f"Вес нетто: {self.additional_data['net_weight']}",
                            f"Камера шоковой заморозки: {self.additional_data['shock_chamber_num']}",
                        ]
                    )
                )
            else:
                texts.append(
                    "<br>".join(
                        [f"Вес тележки: {self.additional_data.get('cart_weight', 0)}"]
                    )
                )
        return mark_safe("<br>".join(texts))

    list_display = (
        "production_id",
        "created_at",
        "weight",
        additional_data,
    )
    fields = ("created_at", "weight", "additional_data")
    readonly_fields = ("created_at", "weight", "additional_data")
    search_fields = ("created_at",)

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return True

    def has_view_contenttype_permission(self, request, obj=None):
        return False


@admin.register(ShockerCamera, site=crm_admin)
class ShockerAdmin(admin.ModelAdmin):
    @admin.display(description="Свободных мест")
    def available(self):
        return mark_safe(ShockerCamera.get_available_shocker()[self.shocker_id])

    list_display = ("shocker_id", "max_pallet_count", available)
    fields = (
        "shocker_id",
        "max_pallet_count",
    )
    readonly_fields = (available,)


@admin.register(ShockerMixLoad, site=crm_admin)
class ShockerMixLoadAdmin(admin.ModelAdmin):
    @admin.display(description="Дополнительные данные")
    def additional_data(self):
        if self.additional_data:
            if self.second_minced_meat_id:
                return mark_safe(
                    "<br>".join(
                        [
                            f"Номер паллета: {self.additional_data['pallet']}",
                            f"Вес паллета: {self.additional_data['pallet_weight']}",
                            f"Кол-во ящиков: {self.additional_data['box_count']}",
                            f"Вес брутто: {self.additional_data['brutto_weight']}",
                            f"Вес нетто: {self.additional_data['net_weight']}",
                        ]
                    )
                )
            else:
                return mark_safe(
                    "<br>".join(
                        [
                            f"Номер паллета: {self.additional_data['pallet']}",
                            f"Вес паллета: {self.additional_data['pallet_weight']}",
                            f"Кол-во ящиков: {self.additional_data['box_count']}",
                        ]
                    )
                )
        else:
            return ""

    list_display = (
        "minced_meat_batch_mix",
        "second_minced_meat",
        "shocker",
        additional_data,
        "status_unload",
    )
    fields = (
        "minced_meat_batch_mix",
        "second_minced_meat",
        "shocker",
        "status_unload",
        additional_data,
    )
    readonly_fields = (additional_data,)
    list_display_links = (
        "minced_meat_batch_mix",
        "second_minced_meat",
    )


@admin.register(RawMaterialParams, site=crm_admin)
class RawMaterialParamstAdmin(admin.ModelAdmin):
    list_display = ("raw_material", "defrost", "second_minced_meat_exit")
    fields = ("raw_material", "defrost", "second_minced_meat_exit")


@admin.register(TTNType, site=crm_admin)
class TTNTypeAdmin(admin.ModelAdmin):
    list_display = ("type", "name", "custom")
    fields = ("type", "name", "custom")


@admin.register(Users, site=crm_admin)
class UsersAdmin(admin.ModelAdmin):
    list_display = ("position", "telegram_id", "name")
    fields = ("position", "telegram_id", "name")
    search_fields = ("position", "name")


@admin.register(RawMeatBatch, site=crm_admin)
class RawMeatBatchAdmin(admin.ModelAdmin):
    change_list_template = "admin/export_raw_meat_batch_datatable_change_list.html"
    list_display = (
        "production_id",
        "raw_material",
        "ttn_type",
        "number_ttn",
        "organization",
        "buh_accounting",
        "before_defrosting",
        "after_defrosting",
        "is_future",
    )
    fields = (
        "production_id",
        "company",
        "raw_material",
        "ttn_type",
        "condition",
        "photo_ypd_preview",
        "acceptance_certificate_download",
        "number_ttn",
        "link_vet",
        "photo_ref_truck_preview",
        "photo_body_temperature_truck_preview",
        "body_temperature_truck",
        "manufacture_date_vet",
        "photo_ttn_preview",
        "photo_tn_preview",
        "photo_vet_preview",
        "photo_temperature_preview",
        "photo_pallet_preview",
        "organization",
        "buh_accounting",
        "weight",
        "tags_number",
        "is_future",
        "status_info",
        "analyze_info",
    )

    readonly_fields = (
        "production_id",
        "photo_ref_truck_preview",
        "photo_body_temperature_truck_preview",
        "photo_ypd_preview",
        "is_future",
        "status_info",
        "analyze_info",
        "acceptance_certificate_download",
        "link_vet",
        "photo_ttn_preview",
        "photo_tn_preview",
        "photo_vet_preview",
        "photo_temperature_preview",
        "photo_pallet_preview",
    )
    list_filter = (("created_at", DateRangeFilter),)

    @admin.display(description="До дефростирования")
    def before_defrosting(self, raw_meat_batch: RawMeatBatch):
        defrosting_status = raw_meat_batch.statuses.filter(
            status__codename="defrosting"
        ).first()
        if defrosting_status:
            return f"{beautify_decimal(Decimal(defrosting_status.additional_data['old_weight']))} кг"
        else:
            return f"{beautify_decimal(raw_meat_batch.weight)} кг"

    @admin.display(description="После дефростирования")
    def after_defrosting(self, raw_meat_batch: RawMeatBatch):
        defrosting_status = raw_meat_batch.statuses.filter(
            status__codename="defrosting"
        ).first()
        if defrosting_status:
            return f"{beautify_decimal(raw_meat_batch.weight)} кг"
        else:
            return None

    @admin.display(description="Акт входного контроля")
    def acceptance_certificate_download(self, raw_meat_batch: RawMeatBatch):
        if raw_meat_batch.acceptance_certificate:
            acceptance_certificate_url = raw_meat_batch.acceptance_certificate.url
        else:
            acceptance_certificate_url = f"/admin/CRM/documents/acceptance_certificate?raw_meat_batch_id={raw_meat_batch.id}"

        return mark_safe(f'<a href="{acceptance_certificate_url}">Скачать</a>')

    @admin.display(description="Фото паказаний рефа фуры")
    def photo_ref_truck_preview(self, raw_meat_batch: RawMeatBatch):
        edit_tag = (
            f'<a href="/admin/CRM/edit-raw-meat-batch/{raw_meat_batch.id}?field=photo_ref_truck">'
            f"{'Изменить' if raw_meat_batch.photo_ref_truck else 'Добавить'}</a>"
        )

        if raw_meat_batch.photo_ref_truck:
            preview_tag = (
                f'<a href="{raw_meat_batch.photo_ref_truck.url}">'
                f'<img src="{raw_meat_batch.photo_ref_truck.url}" height="600"/></a>'
            )
            response = mark_safe(f"{edit_tag}<br><br>{preview_tag}")
        else:
            response = mark_safe(edit_tag)

        return response

    @admin.display(
        description="Фото замера температры в кузове в момент открытия машины"
    )
    def photo_body_temperature_truck_preview(self, raw_meat_batch: RawMeatBatch):
        edit_tag = (
            f'<a href="/admin/CRM/edit-raw-meat-batch/{raw_meat_batch.id}?field=photo_body_temperature_truck">'
            f"{'Изменить' if raw_meat_batch.photo_body_temperature_truck else 'Добавить'}</a>"
        )

        if raw_meat_batch.photo_body_temperature_truck:
            preview_tag = (
                f'<a href="{raw_meat_batch.photo_body_temperature_truck.url}">'
                f'<img src="{raw_meat_batch.photo_body_temperature_truck.url}" height="600"/></a>'
            )
            response = mark_safe(f"{edit_tag}<br><br>{preview_tag}")
        else:
            response = mark_safe(edit_tag)

        return response

    @admin.display(description="Фото УПД")
    def photo_ypd_preview(self, raw_meat_batch: RawMeatBatch):
        edit_tag = (
            f'<a href="/admin/CRM/edit-raw-meat-batch/{raw_meat_batch.id}?field=photo_ypd">'
            f"{'Изменить' if raw_meat_batch.photo_ypd else 'Добавить'}</a>"
        )

        if raw_meat_batch.photo_ypd:
            preview_tag = (
                f'<a href="{raw_meat_batch.photo_ypd.url}">'
                f'<img src="{raw_meat_batch.photo_ypd.url}" height="600"/></a>'
            )
            response = mark_safe(f"{edit_tag}<br><br>{preview_tag}")
        else:
            response = mark_safe(edit_tag)

        return response

    @admin.display(description="Фото ТТН")
    def photo_ttn_preview(self, raw_meat_batch: RawMeatBatch):
        files = raw_meat_batch.files.filter(name="photo_ttn").all()

        edit_tag = (
            f'<a href="/admin/CRM/edit-raw-meat-batch/{raw_meat_batch.id}?field=photo_ttn">'
            f"{'Изменить' if files else 'Добавить'}</a>"
        )

        if files:
            preview_tags = []
            for file in files:
                preview_tags.append(
                    f'<a href="{file.file_location.url}"><img src="{file.file_location.url}" height="600"/></a>'
                )
            response = mark_safe(f"{edit_tag}<br><br>{'<br><br>'.join(preview_tags)}")
        else:
            response = mark_safe(edit_tag)

        return response

    @admin.display(description="Фото ТН")
    def photo_tn_preview(self, raw_meat_batch: RawMeatBatch):
        edit_tag = (
            f'<a href="/admin/CRM/edit-raw-meat-batch/{raw_meat_batch.id}?field=photo_tn">'
            f"{'Изменить' if raw_meat_batch.photo_tn else 'Добавить'}</a>"
        )

        if raw_meat_batch.photo_tn:
            preview_tag = f'<a href="{raw_meat_batch.photo_tn.url}"><img src="{raw_meat_batch.photo_tn.url}" height="600"/></a>'
            response = mark_safe(f"{edit_tag}<br><br>{preview_tag}")
        else:
            response = mark_safe(edit_tag)

        return response

    @admin.display(description="Фото ЭСВД")
    def photo_vet_preview(self, raw_meat_batch: RawMeatBatch):
        edit_tag = (
            f'<a href="/admin/CRM/edit-raw-meat-batch/{raw_meat_batch.id}?field=photo_vet">'
            f"{'Изменить' if raw_meat_batch.photo_vet else 'Добавить'}</a>"
        )

        if raw_meat_batch.photo_vet:
            preview_tag = (
                f'<a href="{raw_meat_batch.photo_vet.url}">'
                f'<img src="{raw_meat_batch.photo_vet.url}" height="600"/></a>'
            )
            response = mark_safe(f"{edit_tag}<br><br>{preview_tag}")
        else:
            response = mark_safe(edit_tag)

        return response

    @admin.display(description="Фото температурного режима")
    def photo_temperature_preview(self, raw_meat_batch: RawMeatBatch):
        edit_tag = (
            f'<a href="/admin/CRM/edit-raw-meat-batch/{raw_meat_batch.id}?field=photo_temperature">'
            f"{'Изменить' if raw_meat_batch.photo_temperature else 'Добавить'}</a>"
        )
        if raw_meat_batch.photo_temperature:
            preview_tag = (
                f'<a href="{raw_meat_batch.photo_temperature.url}">'
                f'<img src="{raw_meat_batch.photo_temperature.url}" height="600"/></a>'
            )
            response = mark_safe(f"{edit_tag}<br><br>{preview_tag}")
        else:
            response = mark_safe(edit_tag)

        return response

    @admin.display(description="Фото палетты")
    def photo_pallet_preview(self, raw_meat_batch: RawMeatBatch):
        edit_tag = (
            f'<a href="/admin/CRM/edit-raw-meat-batch/{raw_meat_batch.id}?field=photo_pallet">'
            f"{'Изменить' if raw_meat_batch.photo_pallet else 'Добавить'}</a>"
        )

        if raw_meat_batch.photo_pallet:
            preview_tag = (
                f'<a href="{raw_meat_batch.photo_pallet.url}">'
                f'<img src="{raw_meat_batch.photo_pallet.url}" height="600"/></a>'
            )
            response = mark_safe(f"{edit_tag}<br><br>{preview_tag}")
        else:
            response = mark_safe(edit_tag)

        return response

    @admin.display(description="На складе")
    def is_future(self, raw_meat_batch: RawMeatBatch):
        return "В поставке" if raw_meat_batch.is_future_batch else "Да"

    @admin.display(description="Стадии обработки")
    def status_info(self, raw_meat_batch: RawMeatBatch):
        status_texts = []

        for status in raw_meat_batch.statuses.all():
            status_text = f"{status.created_at:%d-%m-%Y %H:%M} - {status.status.name} "
            status_texts.append(status_text)
        return mark_safe("<br>".join(status_texts))

    @admin.display(description="Анализ лаборатории")
    def analyze_info(self, raw_meat_batch: RawMeatBatch):
        mb = MinioBackend(bucket_name=env.MINIO_MAIN_BUCKET)

        status_text = ""

        for status in raw_meat_batch.statuses.all():
            if (
                status.status.codename == "laboratory_analyze"
                and status.additional_data
            ):
                status_text = f"""
{status.created_at:%d-%m-%Y %H:%M} - {status.status.name}
<br>Массовая доля жиров: {status.additional_data["fat_proportion"]} %
<br>Массовая доля белков: {status.additional_data["protein_proportion"]} %
<br>Массовая доля влаги: {status.additional_data["moisture_proportion"]} %
<br>Внешний вид: {"соотв." if status.additional_data["appearance"] else "не соотв."}
<br>Запах: {"соотв." if status.additional_data["smell"] else "не соотв."}
<br>Цвет: {"соотв." if status.additional_data["color"] else "не соотв."}
<br>Качество бульона при варке: {"соотв." if status.additional_data["broth_quality"] else "не соотв."}
<br>Аромат бульона: {"соотв." if status.additional_data["broth_flavor"] else "не соотв."}
<br>Бета-лактамы: {status.additional_data["betta_lactams"]}
<br>Хлорамфениколы: {status.additional_data["chloramphenicols"]}
<br>Тетрациклины: {status.additional_data["tetracyclines"]}
<br>Стрептомицины: {status.additional_data["streptomycins"]}
"""
                for photo in status.additional_data["organoleptic_photos"]:
                    photo_url = mb.url(photo)
                    status_text += f'<br><a href="{photo_url}"><img src="{photo_url}" height="250"/></a><br>'

        return mark_safe(status_text)


@admin.register(MeatBlank, site=crm_admin)
class MeatBlankAdmin(admin.ModelAdmin):
    @admin.display(description="Заготовка Марс")
    def production_id(self):
        if self.type_meat_blank:
            return self.production_id + " Марс"
        return self.production_id

    list_display = (production_id, "arrival_date")

    fields = (
        production_id,
        "arrival_date",
        "protein",
        "fat",
        "moisture",
        "meat_info",
        "status_info",
    )
    readonly_fields = (
        production_id,
        "arrival_date",
        "protein",
        "fat",
        "moisture",
        "meat_info",
        "status_info",
    )
    search_fields = (production_id, "created_at")
    list_filter = (MKOMincedMeatFilter,)

    @admin.display(description="используемое сырье")
    def meat_info(self, meat_blank: MeatBlank):
        text_elements = []
        meat_blank_raw_meat_batches = MeatBlankRawMeatBatch.objects.filter(
            meat_blank=meat_blank
        ).all()
        for meat_blank_raw_meat_batch in meat_blank_raw_meat_batches:
            link = (
                f'<a href="/admin/CRM/rawmeatbatch/{meat_blank_raw_meat_batch.raw_meat_batch.id}/">'
                f"{meat_blank_raw_meat_batch.raw_meat_batch.production_id}</a>"
            )
            text_elements.append(
                (
                    f"{meat_blank_raw_meat_batch.raw_meat_batch.raw_material.name} - "
                    f"{meat_blank_raw_meat_batch.weight} кг ({link})"
                )
            )
        return mark_safe("<br>".join(text_elements))

    @admin.display(description="Стадии обработки")
    def status_info(self, meat_blank: MeatBlank):
        status_texts = []

        for status in meat_blank.statuses.all():
            status_text = (
                f"{convert_to_localtime(status.created_at)} - {status.status.name} "
                f"<a href='/admin/CRM/delete_meat_blank_status/{meat_blank.id}/p/{status.id}'>Удалить</a>"
            )
            status_texts.append(status_text)
        return mark_safe("<br>".join(status_texts))

    def has_add_permission(self, request, obj=None):
        return False


# @admin.register(ShockerCamera, site=crm_admin)
class ShockerCameraAdmin(admin.ModelAdmin):
    @admin.display(description="Дополнительные данные")
    def additional_data(self):
        texts = []
        add_data = self.additional_data
        if add_data["type"] in [2, 3]:
            add_data = add_data["additional_data"]
            texts.append(
                "<br>".join(
                    [
                        f"МКО{add_data['type']}",
                        f"Номер паллета: {add_data['pallet']}",
                        f"Вес паллета: {add_data['brutto_weight']}",
                        f"Кол-во коробок: {add_data['box_count']}",
                        f"Вес брутто: {add_data['brutto_weight']}",
                        f"Вес нетто: {add_data['net_weight']}",
                        f"Камера шоковой заморозки: {add_data['shock_chamber_num']}",
                    ]
                )
            )
        return mark_safe("<br>".join(texts))

    @admin.display(description="Статус загрузки")
    def status_loaded_func(self):
        text = "Загружен"
        if not self.status_loaded:
            text = "Выгружен"
        return mark_safe("<br>".join([text]))

    list_display = ("created_at", status_loaded_func, additional_data)
    fields = ("created_at", status_loaded_func, additional_data)
    readonly_fields = ("created_at", status_loaded_func, additional_data)
    search_fields = "created_at"

    def has_change_permission(self, request, obj=None):
        return True

    def has_add_permission(self, request, obj=None):
        return False


async def send_message(message):
    # Отключено уведомление из админки, чтобы не падать с Unauthorized
    return None


@admin.register(MincedMeatBatchMix, site=crm_admin)
class MincedMeatBatchMixAdmin(admin.ModelAdmin):
    list_filter = (("created_at", DateRangeFilter),)

    @staticmethod
    def production_id(mix: MincedMeatBatchMix):
        return mix.production_id

    @staticmethod
    def recipe_name(mix: MincedMeatBatchMix):
        return mix.minced_meat_batch.recipe.name

    @staticmethod
    def pallet_id(mix: MincedMeatBatchMix):
        pallet_data = MincedMeatBatchStatus.objects.filter(
            minced_meat_batch_mix_id=mix.pk,
            status__codename="mixer_tiller_mix_meat_end",
        ).first()
        return f"{pallet_data.additional_data.get('pallet') if pallet_data else ''}"

    @staticmethod
    def status(mix: MincedMeatBatchMix):
        check_block = MincedMeatBatchStatus.objects.filter(
            minced_meat_batch_mix_id=mix.pk,
            minced_meat_batch_mix__statuses__status__codename="mix_is_blocked_analyze",
        ).first()
        if check_block:
            return mark_safe(
                '<b style="color: red;">Заблокирован, замес не прошел ФХП</b>'
            )
        if not mix.minced_meat_batch:
            return mark_safe('<b style="color: green;">Готов к отгрузке</b>')
        if mix.minced_meat_batch.type == "МКО":
            check_all_analyze = MincedMeatBatchStatus.objects.filter(
                minced_meat_batch_mix_id=mix.pk,
                status__codename="laboratory_analyze_finish",
            ).first()
            if check_all_analyze and not check_all_analyze.additional_data.get(
                "pitch", None
            ):
                return mark_safe(
                    '<b style="color: orange;">Отсутствует анализ на золу, отгрузка невозможна!</b>'
                )

        return mark_safe('<b style="color: green;">Готов к отгрузке</b>')

    @staticmethod
    def second_minced_status(mix: MincedMeatBatchMix):
        check_all_analyze = SecondMincedMeatStatus.objects.filter(
            second_minced_meat__id=mix.pk, status__codename="laboratory_analyze_finish"
        ).first()
        if check_all_analyze and not check_all_analyze.additional_data.get(
            "pitch", None
        ):
            return mark_safe(
                '<b style="color: orange;">Отсутствует анализ на золу, отгрузка невозможна!</b>'
            )

        return mark_safe('<b style="color: green;">Готов к отгрузке</b>')

    @staticmethod
    def additional_data(mix: MincedMeatBatchMix):
        palletizing = MincedMeatBatchStatus.objects.filter(
            minced_meat_batch_mix_id=mix.pk, status__codename="palletizing_end"
        ).first()
        texts = []
        if palletizing.additional_data:
            texts.append(
                f"""       {"&nbsp;" * 4}• Вес брутто - {palletizing.additional_data["all_weight"]} кг <br>
                                    {"&nbsp;" * 4}• Вес палеты - {palletizing.additional_data["weight_pallet"]} кг <br>
                                   {"&nbsp;" * 4}•  Вес упаковки - {palletizing.additional_data["weight_pack"]} <br>
                                  {"&nbsp;" * 4}•   Вес нетто {palletizing.additional_data["weight_raw"]} кг <br>
                                     """
            )

        return mark_safe("<br>".join(texts))

    @staticmethod
    def second_minced_additional_data(mix: SecondMincedMeat):
        palletizing = SecondMincedMeatStatus.objects.filter(
            second_minced_meat__id=mix.pk, status__codename="palletizing_end"
        ).first()
        texts = []
        if palletizing and palletizing.additional_data:
            texts.append(
                f"""       {"&nbsp;" * 4}• Вес брутто - {palletizing.additional_data["all_weight"]} кг <br>
                           {"&nbsp;" * 4}• Вес палеты - {palletizing.additional_data["weight_pallet"]} кг <br>
                           {"&nbsp;" * 4}•  Вес упаковки - {palletizing.additional_data["weight_pack"]} <br>
                           {"&nbsp;" * 4}•   Вес нетто {palletizing.additional_data["weight_raw"]} кг <br>
                           """
            )
        else:
            return
        return mark_safe("<br>".join(texts))

    @staticmethod
    def get_weight(mix: MincedMeatBatchMix):
        palletizing = MincedMeatBatchStatus.objects.filter(
            minced_meat_batch_mix_id=mix.pk, status__codename="palletizing_end"
        ).first()
        if palletizing.additional_data:
            return palletizing.additional_data["weight_raw"]

    @staticmethod
    def second_minced_get_weight(mix: MincedMeatBatchMix):
        palletizing = SecondMincedMeatStatus.objects.filter(
            second_minced_meat__id=mix.pk, status__codename="palletizing_end"
        ).first()
        if palletizing and palletizing.additional_data:
            return palletizing.additional_data["weight_raw"]

    change_list_template = "admin/change_list_results_store.html"

    def changelist_view(self, request, extra_context=None):
        qs: QuerySet[MincedMeatBatchMix] = super(
            MincedMeatBatchMixAdmin, self
        ).get_queryset(request)
        if request.GET:
            dates = {}
            if request.GET.get("created_at__range__gte"):
                dates.update(
                    {
                        "created_at__gte": datetime.strptime(
                            f"{request.GET['created_at__range__gte']} 00:00:00",
                            "%d.%m.%Y %H:%M:%S",
                        )
                    }
                )
            if request.GET.get("created_at__range__lte"):
                dates.update(
                    {
                        "created_at__lte": datetime.strptime(
                            f"{request.GET['created_at__range__lte']} 00:00:00",
                            "%d.%m.%Y %H:%M:%S",
                        )
                    }
                )
            mixes = qs.filter(
                statuses__status__codename="work_is_finished", **dates
            ).exclude(shipment_pallets__isnull=False)
        else:
            mixes = qs.filter(statuses__status__codename="work_is_finished").exclude(
                shipment_pallets__isnull=False
            )

        recipies = sorted(
            set(
                [
                    mix.minced_meat_batch.recipe.name
                    for mix in mixes
                    if mix.minced_meat_batch
                ]
            )
        )[::-1]
        mixes_for_dates = {}
        for recipe in recipies:
            if "Марс" in recipe:
                continue
            mixes_data = {}
            dates = sorted(
                set(
                    list([i.date() for i in mixes.values_list("created_at", flat=True)])
                )
            )[::-1]
            weight = 0
            for date in dates:
                mix_list = (
                    mixes.filter(
                        Q(minced_meat_batch__recipe__name=recipe)
                        | Q(minced_meat_batch__isnull=True),
                        created_at__day=date.day,
                        created_at__month=date.month,
                        created_at__year=date.year,
                    )
                    .exclude(minced_meat_batch__type="МКО")
                    .order_by("created_at")
                )

                for mix in mix_list:
                    if mix.minced_meat_batch and mix.minced_meat_batch.type == "МКО":
                        continue
                    if not mix.minced_meat_batch and mix.production_id.split("/")[
                        -1
                    ] != re.sub("ВторФарш ", "", recipe):
                        continue
                    mix_weight = self.get_weight(mix)
                    if mix_weight:
                        weight += int(mix_weight)
                mixes_with_data = [
                    {
                        "id": mix.pk,
                        "production_id": self.production_id(mix),
                        "recipe_name": (
                            self.recipe_name(mix)
                            if mix.minced_meat_batch
                            else mix.production_id.split("/")[-1]
                        ),
                        "pallet_id": self.pallet_id(mix),
                        "status": self.status(mix),
                        "additional_data": self.additional_data(mix),
                        "meat_id": mix.minced_meat_batch.id
                        if mix.minced_meat_batch
                        else None,
                    }
                    for mix in mix_list
                    if mix.minced_meat_batch
                    or mix.production_id.split("/")[-1]
                    == re.sub("ВторФарш ", "", recipe)
                ]

                if not mixes_data.get(date):
                    mixes_data.update({date: mixes_with_data})
                else:
                    mixes_data[date] += mixes_with_data

                if not mixes_data[date]:
                    mixes_data.pop(date)
            recipe = re.sub("ВторФарш ", "", recipe)
            if weight:
                mixes_for_dates.update({f"{recipe} {weight} кг": mixes_data})

        # МАРС
        mixes_data = {}
        dates = sorted(
            set(list([i.date() for i in mixes.values_list("created_at", flat=True)]))
        )[::-1]
        weight = 0
        for date in dates:
            mix_list = mixes.filter(
                Q(minced_meat_batch__type="МКО") | Q(minced_meat_batch__isnull=True),
                created_at__day=date.day,
                created_at__month=date.month,
                created_at__year=date.year,
            ).order_by("created_at")
            for mix in mix_list:
                # if not mix.minced_meat_batch and mix.production_id.split("/")[-1] != "Марс": continue
                mix_weight = self.get_weight(mix)
                if mix_weight:
                    weight += int(mix_weight)
            mixes_with_data = [
                {
                    "id": mix.pk,
                    "production_id": self.production_id(mix),
                    "recipe_name": (
                        self.recipe_name(mix)
                        if mix.minced_meat_batch
                        else mix.production_id.split("/")[-1]
                    ),
                    "pallet_id": self.pallet_id(mix),
                    "status": self.status(mix),
                    "additional_data": self.additional_data(mix),
                    "meat_id": mix.minced_meat_batch.id
                    if mix.minced_meat_batch
                    else None,
                }
                for mix in mix_list
            ]

            if not mixes_data.get(date):
                mixes_data.update({date: mixes_with_data})
            else:
                mixes_data[date] += mixes_with_data

            if not mixes_data[date]:
                mixes_data.pop(date)
        if weight:
            mixes_for_dates.update({f"Марс {weight} кг": mixes_data})

        mixes_data = {}
        dates = sorted(
            set(
                list(
                    [
                        i.date()
                        for i in SecondMincedMeat.objects.values_list(
                            "created_at", flat=True
                        )
                    ]
                )
            )
        )[::-1]
        weight = 0
        for date in dates:
            mix_list = SecondMincedMeat.objects.filter(
                production_id__icontains="Продажа",
                created_at__day=date.day,
                created_at__month=date.month,
                created_at__year=date.year,
            ).order_by("created_at")
            for mix in mix_list:
                # if not mix or not mix.additional_data: continue
                mix_weight = self.second_minced_get_weight(mix)
                if mix_weight:
                    weight += int(mix_weight)
            mixes_with_data = [
                {
                    "id": mix.pk,
                    "production_id": re.sub("МКО[123]", "МКО", str(mix.production_id)),
                    "recipe_name": "recipe_name",
                    "pallet_id": (
                        mix.additional_data["pallet"]
                        if mix.additional_data and "pallet" in mix.additional_data
                        else 0
                    ),
                    "status": self.second_minced_status(mix),
                    "additional_data": self.second_minced_additional_data(mix),
                }
                for mix in mix_list
                if mix.additional_data and self.second_minced_additional_data(mix)
            ]

            if not mixes_data.get(date):
                mixes_data.update({date: mixes_with_data})
            else:
                mixes_data[date] += mixes_with_data

            if not mixes_data[date]:
                mixes_data.pop(date)
        if weight:
            mixes_for_dates.update({f"МКО Продажа {weight} кг": mixes_data})

        mixes_data = {}
        dates = sorted(
            set(
                list(
                    [
                        i.date()
                        for i in SecondMincedMeat.objects.values_list(
                            "created_at", flat=True
                        )
                    ]
                )
            )
        )[::-1]
        weight = 0
        for date in dates:
            mix_list = (
                SecondMincedMeat.objects.filter(
                    created_at__day=date.day,
                    created_at__month=date.month,
                    created_at__year=date.year,
                )
                .exclude(production_id__icontains="Продажа")
                .order_by("created_at")
            )
            for mix in mix_list:
                # if not mix or not mix.additional_data: continue
                mix_weight = self.second_minced_get_weight(mix)
                if mix_weight:
                    weight += int(mix_weight)
            mixes_with_data = [
                {
                    "id": mix.pk,
                    "production_id": re.sub("МКО[123]", "МКО", str(mix.production_id)),
                    "recipe_name": "recipe_name",
                    "pallet_id": (
                        mix.additional_data["pallet"]
                        if mix.additional_data and "pallet" in mix.additional_data
                        else 0
                    ),
                    "status": self.second_minced_status(mix),
                    "additional_data": self.second_minced_additional_data(mix),
                }
                for mix in mix_list
                if mix.additional_data and self.second_minced_additional_data(mix)
            ]

            if not mixes_data.get(date):
                mixes_data.update({date: mixes_with_data})
            else:
                mixes_data[date] += mixes_with_data

            if not mixes_data[date]:
                mixes_data.pop(date)
        if weight:
            mixes_for_dates.update({f"МКО {weight} кг": mixes_data})

        extra_context = extra_context or {"mixes": mixes_for_dates}
        return super().changelist_view(request, extra_context=extra_context)

    list_display = (production_id, recipe_name, status, pallet_id, additional_data)

    def get_queryset(self, request):
        qs: QuerySet[MincedMeatBatchMix] = super(
            MincedMeatBatchMixAdmin, self
        ).get_queryset(request)

        return qs.filter(statuses__status__codename="work_is_finished").exclude(
            shipment_pallets__isnull=False
        )

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return True

    def has_view_contenttype_permission(self, request, obj=None):
        return False


@admin.register(MincedMeatBatch, site=crm_admin)
class MincedMeatBatchAdmin(admin.ModelAdmin):
    actions = [
        "action_reset_palletizing_unfinished",
        "action_force_finish_palletizing_unfinished",
    ]

    class MincedMeatBatchForm(forms.ModelForm):
        class Meta:
            model = MincedMeatBatch
            fields = "__all__"

        def clean_number_mix(self):
            number_mix = self.cleaned_data.get("number_mix")
            obj: MincedMeatBatch = self.instance
            if obj and obj.pk and number_mix is not None:
                produced_via_status = (
                    MincedMeatBatchStatus.objects.filter(
                        minced_meat_batch_mix__minced_meat_batch=obj,
                        status__codename__in=["palletizing_end", "work_is_finished"],
                    )
                    .values("minced_meat_batch_mix_id")
                    .distinct()
                    .count()
                )
                raw_ids = set(
                    MincedMeatBatchMixConsumptionRaw.objects.filter(
                        minced_meat_batch_mix__minced_meat_batch=obj
                    ).values_list("minced_meat_batch_mix_id", flat=True)
                )
                blank_ids = set(
                    MincedMeatBatchMixConsumptionMeatBlank.objects.filter(
                        minced_meat_batch_mix__minced_meat_batch=obj
                    ).values_list("minced_meat_batch_mix_id", flat=True)
                )
                produced_via_consumption = len(raw_ids.union(blank_ids))
                produced = max(produced_via_status, produced_via_consumption)
                if number_mix < produced:
                    raise forms.ValidationError(
                        f"Нельзя установить количество замесов меньше уже произведённых ({produced})."
                    )
            return number_mix

    form = MincedMeatBatchForm

    @admin.display(description="ID фарша")
    def production_id(self):
        return self.production_id + (" Марс" if self.type == "МКО" else "")

    change_list_template = "admin/export_minced_meat_batch_datatable_change_list.html"
    list_display = (
        "id",
        production_id,
        "recipe_reformat",
        "number_mix",
        "arrival_date_formatted",
    )
    fields = (
        production_id,
        "recipe",
        "number_mix",
        "edit_number_mix",
        "protein",
        "fat",
        "moisture",
        "arrival_date_formatted",
        "consumption_summary",
        "used_meat_blanks",
        "used_raw_material_batches",
        "used_second_minced_meat",
        "status_info",
    )
    readonly_fields = (
        production_id,
        "recipe",
        "edit_number_mix",
        "protein",
        "fat",
        "moisture",
        "arrival_date_formatted",
        "consumption_summary",
        "used_meat_blanks",
        "used_raw_material_batches",
        "used_second_minced_meat",
        "status_info",
    )
    list_filter = (("mixes__statuses__created_at", StorageStatusDateRangeFilter),)

    def get_readonly_fields(self, request, obj=None):
        fields = (
            list(super().get_readonly_fields(request, obj))
            if hasattr(super(), "get_readonly_fields")
            else list(self.readonly_fields)
        )
        # По умолчанию делаем number_mix read-only; включаем редактирование при ?edit_number_mix=1
        if not request.GET.get("edit_number_mix"):
            fields.append("number_mix")
        return fields

    @admin.display(description="Изменить количество замесов")
    def edit_number_mix(self, obj: MincedMeatBatch):
        return mark_safe("<a href='?edit_number_mix=1'>Редактировать</a>")

    @admin.display(description="Рецепт")
    def recipe_reformat(self, minced_meat_batch: MincedMeatBatch):
        return re.sub("ВторФарш ", "", minced_meat_batch.recipe.name)

    # @admin.display(description="Стадии обработки")
    def status_info_meat_batch(self, minced_meat_batch: MincedMeatBatch):
        status_texts = []

        for status in minced_meat_batch.statuses.all():
            status_text = (
                f"{convert_to_localtime(status.created_at)} - {status.status.name} "
            )
            # f"<a href='/admin/CRM/delete_minced_meat_batch_status/{minced_meat_batch.id}/p/{status.id}'>Удалить</a>"

            if status.status.codename == "to_tiler":
                status_text += f"({status.additional_data['tiler']})"
            status_texts.append(status_text)
        return mark_safe("<br>".join(status_texts))

    @admin.display(description="дата отгрузки на склад")
    def storage_status_date(self, minced_meat_batch: MincedMeatBatch):
        if minced_meat_batch.storage_status_date:
            return minced_meat_batch.storage_status_date.strftime("%d.%m.%Y")
        else:
            return "-"

    @admin.display(description="дата прихода в цех")
    def arrival_date_formatted(self, minced_meat_batch: MincedMeatBatch):
        return minced_meat_batch.arrival_date.strftime("%d.%m.%Y")

    @admin.display(description="используемые заготовки")
    def used_meat_blanks(self, minced_meat_batch: MincedMeatBatch):
        text_elements = []
        for meat_blank in minced_meat_batch.meat_blanks.all():
            link = f'<a href="/admin/CRM/meatblank/{meat_blank.meat_blank.id}/">{meat_blank.meat_blank.production_id}</a>'
            text_elements.append(
                f"{meat_blank.meat_blank.production_id} - {meat_blank.weight} кг ({link})"
            )
        text_elements.append(
            f'<a href="/admin/CRM/mincedmeatbatchmeatblank/?minced_meat_batch__id={minced_meat_batch.id}">Изменить</a>'
        )
        return mark_safe("<br>".join(text_elements))

    @admin.display(description="Остатки/перераспределение")
    def consumption_summary(self, minced_meat_batch: MincedMeatBatch):
        # Сводка по сырью
        raw_lines = ["<b>Сырьё</b>"]
        for rel in MincedMeatBatchRawMeatBatch.objects.filter(
            minced_meat_batch=minced_meat_batch
        ).all():
            consumed = (
                MincedMeatBatchMixConsumptionRaw.objects.filter(
                    minced_meat_batch_mix__minced_meat_batch=minced_meat_batch,
                    raw_meat_batch=rel.raw_meat_batch,
                ).aggregate(Sum("weight"))["weight__sum"]
                or 0
            )
            remaining = max(float(rel.weight) - float(consumed), 0.0)
            produced = (
                MincedMeatBatchMixConsumptionRaw.objects.filter(
                    minced_meat_batch_mix__minced_meat_batch=minced_meat_batch
                )
                .values("minced_meat_batch_mix_id")
                .distinct()
                .count()
            )
            remaining_mixes = max((minced_meat_batch.number_mix or 0) - produced, 0)
            per_mix = f"{remaining / remaining_mixes:.2f}" if remaining_mixes else "-"
            raw_lines.append(
                f"{rel.raw_meat_batch.raw_material.name}: план {rel.weight} кг, списано {consumed:.2f} кг, остаток {remaining:.2f} кг, на замес {per_mix} кг"
            )

        # Сводка по заготовкам
        blank_lines = ["<b>Заготовки</b>"]
        for rel in MincedMeatBatchMeatBlank.objects.filter(
            minced_meat_batch=minced_meat_batch
        ).all():
            consumed = (
                MincedMeatBatchMixConsumptionMeatBlank.objects.filter(
                    minced_meat_batch_mix__minced_meat_batch=minced_meat_batch,
                    meat_blank=rel.meat_blank,
                ).aggregate(Sum("weight"))["weight__sum"]
                or 0
            )
            remaining = max(float(rel.weight) - float(consumed), 0.0)
            produced = (
                MincedMeatBatchMixConsumptionMeatBlank.objects.filter(
                    minced_meat_batch_mix__minced_meat_batch=minced_meat_batch
                )
                .values("minced_meat_batch_mix_id")
                .distinct()
                .count()
            )
            remaining_mixes = max((minced_meat_batch.number_mix or 0) - produced, 0)
            per_mix = f"{remaining / remaining_mixes:.2f}" if remaining_mixes else "-"
            blank_lines.append(
                f"{rel.meat_blank.production_id}: план {rel.weight} кг, списано {consumed:.2f} кг, остаток {remaining:.2f} кг, на замес {per_mix} кг"
            )

        # Сводка по вторфаршу
        second_meat_lines = ["<b>Вторфарш</b>"]
        for rel in MincedMeatBatchSecondMeatBlank.objects.filter(
            minced_meat_batch=minced_meat_batch
        ).all():
            consumed = (
                MincedMeatBatchMixConsumptionSecondMeatBlank.objects.filter(
                    minced_meat_batch_mix__minced_meat_batch=minced_meat_batch,
                    second_minced_meat=rel.second_minced_meat,
                ).aggregate(Sum("weight"))["weight__sum"]
                or 0
            )
            remaining = max(float(rel.weight) - float(consumed), 0.0)
            produced = (
                MincedMeatBatchMixConsumptionSecondMeatBlank.objects.filter(
                    minced_meat_batch_mix__minced_meat_batch=minced_meat_batch
                )
                .values("minced_meat_batch_mix_id")
                .distinct()
                .count()
            )
            remaining_mixes = max((minced_meat_batch.number_mix or 0) - produced, 0)
            per_mix = f"{remaining / remaining_mixes:.2f}" if remaining_mixes else "-"
            second_meat_lines.append(
                f"{rel.second_minced_meat.production_id}: план {rel.weight} кг, списано {consumed:.2f} кг, остаток {remaining:.2f} кг, на замес {per_mix} кг"
            )

        return mark_safe("<br>".join(raw_lines + ["<br>"] + blank_lines + ["<br>"] + second_meat_lines))

    @admin.display(description="используемое сырье")
    def used_raw_material_batches(self, minced_meat_batch: MincedMeatBatch):
        text_elements = []
        for raw_meat_batch in minced_meat_batch.raw_meat_batches.all():
            link = (
                f'<a href="/admin/CRM/rawmeatbatch/{raw_meat_batch.raw_meat_batch.id}/">'
                f"{raw_meat_batch.raw_meat_batch.production_id}</a>"
            )
            text_elements.append(
                f"{raw_meat_batch.raw_meat_batch.raw_material.name} - {raw_meat_batch.weight} кг ({link})"
            )
        text_elements.append(
            (
                f'<a href="/admin/CRM/mincedmeatbatchrawmeatbatch/?minced_meat_batch__id={minced_meat_batch.id}">'
                "Изменить</a>"
            )
        )
        return mark_safe("<br>".join(text_elements))

    @admin.display(description="используемый вторфарш")
    def used_second_minced_meat(self, minced_meat_batch: MincedMeatBatch):
        text_elements = []
        for second_meat in minced_meat_batch.second_minced_meat.all():
            link = (
                '<a href="/admin/CRM/secondmincedmeat/'
                f'{second_meat.second_minced_meat.pk}/">{second_meat.second_minced_meat.production_id}</a>'
            )
            text_elements.append(
                f"{second_meat.second_minced_meat.production_id} - {second_meat.weight} кг ({link})"
            )
        text_elements.append(
            (
                f'<a href="/admin/CRM/mincedmeatbatchsecondmeatblank/?minced_meat_batch__id={minced_meat_batch.id}">'
                "Изменить</a>"
            )
        )
        return mark_safe("<br>".join(text_elements))

    #   @admin.display(description="Информация о паллете")
    def pallet_info(self, minced_meat_batch: MincedMeatBatch):
        mb = MinioBackend(bucket_name=env.MINIO_MAIN_BUCKET)
        texts = []
        status_id = Status.objects.filter(codename="palletizing").first()
        data = TotalMincedMeatBatchStatus.objects.filter(
            status_id=status_id.id, minced_meat_batch_id=minced_meat_batch.id
        ).first()
        additional_data = data.additional_data
        if additional_data:
            texts.append(
                f"""
                     Вес брутто - {additional_data["all_weight"]} кг <br>
                     Вес палеты - {additional_data["weight_pallet"]} кг <br>
                     Вес упаковки - {additional_data["weight_pack"]} <br>
                     Вес нетто - {additional_data["weight_raw"]} кг <br>
                     """
            )
            # mb = MinioBackend(bucket_name=env.MINIO_MAIN_BUCKET)
            for photo in additional_data["photos"]:
                photo_url = mb.url(photo)
                texts.append(
                    f'<br><a href="{photo_url}"><img src="{photo_url}" height="250"/></a><br>'
                )

        return mark_safe("<br><br>".join(texts))

    @admin.display(description="Стадии обработки замесов")
    def status_info(self, minced_meat_batch: MincedMeatBatch):
        status_texts = []

        for mix in sorted(
            minced_meat_batch.mixes.all(), key=lambda m: m.get_mix_number()
        ):
            text = f"Замес {mix.production_id}:"
            for status in mix.statuses.all().order_by("created_at"):
                add_data = status.additional_data
                if add_data:
                    tiler_id = add_data.get("tiler_id", None) or add_data.get(
                        "tiller_id", None
                    )
                    if tiler_id:
                        text += f"<br>• Номер плиточника - {tiler_id}"

                text += f"<br>• {status.status.name} - {convert_to_localtime(status.created_at)}"

                if status.status.codename == "laboratory_analyze_finish":
                    if len(status.additional_data) >= 3:
                        text += f"""
                            <br>{"&nbsp;" * 4}• Массовая доля жиров: {status.additional_data["fat_proportion"]} %
                            <br>{"&nbsp;" * 4}• Массовая доля белков: {status.additional_data["protein_proportion"]} %
                            <br>{"&nbsp;" * 4}• Массовая доля влаги: {status.additional_data["moisture_proportion"]} %
                        """
                        if "pitch" in status.additional_data:
                            text += f"<br>{'&nbsp;' * 4}• Доля смол: {status.additional_data['pitch']} %"

                elif status.status.codename == "palletizing_end":
                    mb = MinioBackend(bucket_name=env.MINIO_MAIN_BUCKET)
                    texts = []
                    additional_data = status.additional_data
                    if additional_data:
                        texts.append(
                            f"""
                                                  <br>
                                                {"&nbsp;" * 4}• Вес брутто - {additional_data["all_weight"]} кг <br>
                                                {"&nbsp;" * 4}• Вес палеты - {additional_data["weight_pallet"]} кг <br>
                                               {"&nbsp;" * 4}•  Вес упаковки - {additional_data["weight_pack"]} <br>
                                              {"&nbsp;" * 4}•   Вес нетто - {additional_data["weight_raw"]} кг <br>
                                                 """
                        )
                        for photo in additional_data["photos"]:
                            photo_url = mb.url(photo)
                            texts.append(
                                (
                                    "<br>"
                                    '{"&nbsp;" * 4}'
                                    f'<a href="{photo_url}"><img src="{photo_url}" height="250"/></a><br>'
                                )
                            )
                    text += "\n".join(texts)
            status_texts.append(text)
        return mark_safe("<br><br>".join(status_texts))

    def get_queryset(self, request):
        qs = super(MincedMeatBatchAdmin, self).get_queryset(request)

        return qs

    @admin.action(description="Сбросить паллетирование незавершённых замесов в партии")
    def action_reset_palletizing_unfinished(
        self, request, queryset: QuerySet[MincedMeatBatch]
    ):
        palletizing = Status.objects.get(codename="palletizing")
        count = 0
        for batch in queryset:
            for mix in batch.mixes.all():
                if (
                    mix.statuses.filter(status=palletizing).exists()
                    and not mix.statuses.filter(
                        status__codename="palletizing_end"
                    ).exists()
                ):
                    mix.statuses.filter(status=palletizing).delete()
                    count += 1
        self.message_user(request, f"Сброшено паллетирование у {count} замесов.")

    @admin.action(
        description="Принудительно завершить паллетирование незавершённых замесов"
    )
    def action_force_finish_palletizing_unfinished(
        self, request, queryset: QuerySet[MincedMeatBatch]
    ):
        palletizing = Status.objects.get(codename="palletizing")
        palletizing_end = Status.objects.get(codename="palletizing_end")
        count = 0
        for batch in queryset:
            for mix in batch.mixes.all():
                if not mix.statuses.filter(status=palletizing_end).exists():
                    pal = (
                        mix.statuses.filter(status=palletizing)
                        .order_by("-created_at")
                        .first()
                    )
                    add = pal.additional_data if pal and pal.additional_data else {}
                    additional_data = {
                        "all_weight": add.get("all_weight", 0),
                        "weight_pallet": add.get("weight_pallet", 0),
                        "weight_pack": add.get("weight_pack", 0),
                        "weight_raw": add.get("weight_raw", 0),
                        "pallet": add.get("pallet", 0),
                    }
                    mix.statuses.get_or_create(
                        status=palletizing_end,
                        defaults={"additional_data": additional_data},
                    )
                    count += 1
        self.message_user(
            request, f"Добавлен статус palletizing_end для {count} замесов."
        )

    def save_model(self, request, obj, form, change):
        # При изменении количества замесов помечаем непройденные замесы как remake
        # и сбрасываем их статусы, чтобы в боте пришло уведомление «замес отправлен повторно»
        if change and form and ("number_mix" in getattr(form, "changed_data", [])):
            for mix in sorted(obj.mixes.all(), key=lambda m: m.get_mix_number()):
                end_processed = False
                for status in mix.statuses.all().order_by("created_at"):
                    if status.status.name in [
                        "Загрузка в плиточник",
                        "Загрузка в шокер",
                        "Загрузка в плиточник завершена",
                    ]:
                        end_processed = True
                if not end_processed:
                    for status in mix.statuses.all().order_by("created_at"):
                        status.delete()
                    mix.remake = True
                    mix.save()

            # Если число замесов уменьшили, удалить лишние незапущенные замесы (с номерами > number_mix)
            for mix in list(obj.mixes.all()):
                try:
                    suffix = int(str(mix.production_id).split("/")[-1])
                except Exception:
                    continue
                if suffix > (obj.number_mix or 0):
                    # удаляем только если замес не был начат
                    end_processed = False
                    for status in mix.statuses.all().order_by("created_at"):
                        if status.status.name in [
                            "Загрузка в плиточник",
                            "Загрузка в шокер",
                            "Загрузка в плиточник завершена",
                            "palletizing",
                            "palletizing_end",
                            "work_is_finished",
                        ]:
                            end_processed = True
                    if not end_processed:
                        mix.delete()

            # Если число замесов увеличили, дозаводим недостающие пустые замесы
            existing_suffixes = set()
            for mix in obj.mixes.all():
                try:
                    existing_suffixes.add(int(str(mix.production_id).split("/")[-1]))
                except Exception:
                    continue
            # production_id партии вида DDMM/NN, замес DDMM/NN/i
            base = obj.production_id
            for i in range(1, (obj.number_mix or 0) + 1):
                if i not in existing_suffixes:
                    MincedMeatBatchMix.objects.create(
                        minced_meat_batch=obj,
                        production_id=f"{base}/{i}",
                    )

        super().save_model(request, obj, form, change)

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return True


@admin.register(MincedMeatBatchRawMeatBatch, site=crm_admin)
class MincedMeatBatchRawMeatBatchAdmin(admin.ModelAdmin):
    list_display = ["raw_meat_batch", "weight"]
    list_editable = ("weight",)

    # ?minced_meat_batch__id=126
    def has_module_permission(self, request):
        return False

    def save_model(self, request, obj, form, change):
        old_br = MincedMeatBatchRawMeatBatch.objects.get(id=obj.id)
        if old_br.raw_meat_batch.weight + old_br.weight - obj.weight < 0:
            return messages.error(
                request,
                f"Вы превысили остаток на складе. Остаток на складе: {old_br.raw_meat_batch.weight}",
            )
        old_br.raw_meat_batch.weight += old_br.weight - obj.weight
        old_br.raw_meat_batch.save()
        super().save_model(request, obj, form, change)
        text = ""
        print("save_modelsave_modelsave_modelsave_model")
        for mix in sorted(
            obj.minced_meat_batch.mixes.all(), key=lambda m: m.get_mix_number()
        ):
            text += f"Замес {mix.production_id}:"
            end_processed = False
            for status in mix.statuses.all().order_by("created_at"):
                if status.status.name in ["Загрузка в плиточник", "Загрузка в шокер"]:
                    end_processed = True
            text += "end_processed = " + str(end_processed) + "\n"
            if not end_processed:
                for status in mix.statuses.all().order_by("created_at"):
                    status.delete()
                mix.remake = True
                mix.save()
                # status = Status.objects.filter(codename="remake").first()
                # if not status:
                #     status = Status(codename="remake")
                #     status.save()
                # mix.statuses.create(status=status)
        # уведомления отключены


@admin.register(MincedMeatBatchSecondMeatBlank, site=crm_admin)
class MincedMeatBatchSecondMeatBlankAdmin(admin.ModelAdmin):
    list_display = ["second_minced_meat", "weight"]
    list_editable = ("weight",)

    # ?minced_meat_batch__id=126
    def has_module_permission(self, request):
        return False

    def save_model(self, request, obj, form, change):
        old_br = MincedMeatBatchSecondMeatBlank.objects.get(id=obj.id)
        if old_br.second_minced_meat.weight + old_br.weight - obj.weight < 0:
            return messages.error(
                request,
                f"Вы превысили остаток на складе. Остаток на складе: {old_br.second_minced_meat.weight}",
            )
        old_br.second_minced_meat.weight += old_br.weight - obj.weight
        old_br.second_minced_meat.save()
        super().save_model(request, obj, form, change)
        text = ""
        for mix in sorted(
            obj.minced_meat_batch.mixes.all(), key=lambda m: m.get_mix_number()
        ):
            text += f"Замес {mix.production_id}:"
            end_processed = False
            for status in mix.statuses.all().order_by("created_at"):
                if status.status.name in [
                    "Загрузка в плиточник",
                    "Загрузка в шокер",
                    "Загрузка в плиточник завершена",
                ]:
                    end_processed = True
            text += "end_processed = " + str(end_processed) + "\n"
            if not end_processed:
                for status in mix.statuses.all().order_by("created_at"):
                    status.delete()
                mix.remake = True
                mix.save()
        # уведомления отключены


@admin.register(MincedMeatBatchMeatBlank, site=crm_admin)
class MincedMeatBatchMeatBlankAdmin(admin.ModelAdmin):
    list_display = ["meat_blank", "weight"]
    list_editable = ("weight",)

    # ?minced_meat_batch__id=126
    def has_module_permission(self, request):
        return False

    def save_model(self, request, obj, form, change):
        old_br = MincedMeatBatchMeatBlank.objects.get(id=obj.id)
        if old_br.meat_blank.weight + old_br.weight - obj.weight < 0:
            return messages.error(
                request,
                f"Вы превысили остаток на складе. Остаток на складе: {old_br.meat_blank.weight}",
            )
        old_br.meat_blank.weight += old_br.weight - obj.weight
        old_br.meat_blank.save()
        super().save_model(request, obj, form, change)
        text = ""
        for mix in sorted(
            obj.minced_meat_batch.mixes.all(), key=lambda m: m.get_mix_number()
        ):
            text += f"Замес {mix.production_id}:"
            end_processed = False
            for status in mix.statuses.all().order_by("created_at"):
                if status.status.name in [
                    "Загрузка в плиточник",
                    "Загрузка в шокер",
                    "Загрузка в плиточник завершена",
                ]:
                    end_processed = True
            text += "end_processed = " + str(end_processed) + "\n"
            if not end_processed:
                for status in mix.statuses.all().order_by("created_at"):
                    status.delete()
                mix.remake = True
                mix.save()
        # уведомления отключены


@admin.register(BufferPalletMars, site=crm_admin)
class BufferPalletMarsAdmin(admin.ModelAdmin):
    list_filter = (("created_at", DateRangeFilter),)

    list_display = (
        "created_at",
        "updated_at",
        "pallet_id",
        "box_count",
        "brutto_weight",
        "netto_weight",
    )
    fields = ("pallet_id", "box_count", "brutto_weight", "netto_weight")
    search_fields = ("created_at",)

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Shipment, site=crm_admin)
class ShipmentAdmin(admin.ModelAdmin):
    list_display = (
        "__str__",
        "customer",
        "recipe",
        "minced_meat_batch_link",
        "weight",
        "created_at_format",
    )
    fields = (
        "customer",
        "recipe",
        "minced_meat_batch_link",
        "weight",
        "created_at_format",
    )
    list_filter = (("created_at", DateRangeFilter),)

    @admin.display(description="Рецепт")
    def recipe(self, shipment: Shipment):
        shipment_pallets = shipment.pallets.all()
        if shipment_pallets:
            shipment_pallet = shipment_pallets[0]
            return shipment_pallet.minced_meat_batch_mix.minced_meat_batch.recipe.name

    @admin.display(description="Вес")
    def weight(self, shipment: Shipment):
        w = 0
        shipment_pallets = shipment.pallets.all()
        for shipment_pallet in shipment_pallets:
            w += shipment_pallet.weight
        return f"{round(w, 2)} кг."

    @admin.display(description="Заготовка")
    def minced_meat_batch_link(self, shipment: Shipment):
        shipment_pallets = shipment.pallets.all()
        if shipment_pallets:
            shipment_pallet = shipment_pallets[0]
            return mark_safe(
                (
                    f'<a href="/admin/CRM/mincedmeatbatch/{shipment_pallet.minced_meat_batch_mix.minced_meat_batch.id}'
                    '/change/">Перейти</a>'
                )
            )

    @admin.display(description="Дата отгрузки")
    def created_at_format(self, shipment: Shipment):
        date_format = "%d.%m.%Y"
        return shipment.created_at.strftime(date_format)

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Tilers, site=crm_admin)
class TilersAdmin(admin.ModelAdmin):
    list_display = ("id", "minced_meat_batch_mix", "status")

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Status, site=crm_admin)
class StatusAdmin(admin.ModelAdmin):
    list_display = ("id", "codename", "name")

    def has_add_permission(self, request, obj=None):
        return False
