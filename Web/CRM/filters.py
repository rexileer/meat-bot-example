import datetime

from django.db.models import OuterRef, Subquery, DateTimeField
from rangefilter.filters import DateRangeFilter

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from Web.CRM.models import MincedMeatBatchStatus


class StorageStatusDateRangeFilter(DateRangeFilter):
    def __init__(self, field, request, params, model, model_admin, field_path):
        super(StorageStatusDateRangeFilter, self).__init__(field, request, params, model, model_admin, field_path)
        self.title = "Дата отгрузки на склад"

    def queryset(self, request, qs):
        qs = super(StorageStatusDateRangeFilter, self).queryset(request=request, queryset=qs)

        if self.form.is_valid():
            validated_data = dict(self.form.cleaned_data.items())

            date_value_gte = validated_data.get(self.lookup_kwarg_gte, None)
            date_value_lte = validated_data.get(self.lookup_kwarg_lte, None)

            storage_status_subquery = MincedMeatBatchStatus.objects.filter(
                minced_meat_batch_mix__minced_meat_batch=OuterRef("pk"), status__codename="storage"
            ).values("created_at")
            qs = qs.annotate(
                storage_status_date=Subquery(
                    storage_status_subquery, output_field=DateTimeField(verbose_name="Дата отгрузки на склад")
                )
            )
            qs = qs.filter(
                storage_status_date__gte=self.make_dt_aware(
                    datetime.datetime.combine(date_value_gte, datetime.time.min), self.get_timezone(request)
                ),
                storage_status_date__lte=self.make_dt_aware(
                    datetime.datetime.combine(date_value_lte, datetime.time.max), self.get_timezone(request)
                ),
            )

        return qs


class MKOMincedMeatFilter(admin.SimpleListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = _("Тип заготовок")

    parameter_name = "is_mko"

    def lookups(self, request, model_admin):
        return (
            ("is_mko", _("Марс")),
            ("is_mmo", _("Обычный")),
        )

    def queryset(self, request, queryset):
        if self.value() == "is_mko":
            return queryset.filter(
                type_meat_blank=1,
            )
        if self.value() == "is_mmo":
            return queryset.filter(
                type_meat_blank=0,
            )


class SecondMincedMeatFilter(admin.SimpleListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = _("Тип")

    parameter_name = "second_meat_type"

    def lookups(self, request, model_admin):
        return (
            ("is_second_meat_1", _("МКО1")),
            ("is_second_meat_2", _("МКО2")),
            ("is_second_meat_3", _("МКО3")),
            ("is_second_meat_release", _("Вторфарш")),
        )

    def queryset(self, request, queryset):
        if self.value() == "is_second_meat_1":
            return queryset.filter(
                type=1,
            )
        if self.value() == "is_second_meat_release":
            return queryset.filter(
                type=0,
            )
        if self.value() == "is_second_meat_2":
            return queryset.filter(
                type=2,
            )
        if self.value() == "is_second_meat_3":
            return queryset.filter(
                type=3,
            )
