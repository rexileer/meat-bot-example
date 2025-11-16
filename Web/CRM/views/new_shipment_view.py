from datetime import datetime
from decimal import Decimal

from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.views.generic import FormView

from Web.CRM.forms.edit_pallet_form import EditPalletForm
from Web.CRM.forms.new_shipment_form import NewShipmentForm, SetRecipeNewShipmentForm
from Web.CRM.models import MincedMeatBatchMix, Shipment, ShipmentPallet


class SetRecipeNewShipmentView(FormView):
    form_class = SetRecipeNewShipmentForm
    template_name = "admin/custom_form.html"

    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def form_valid(self, form: EditPalletForm):
        recipe = form.cleaned_data["recipe"]
        return redirect(f"/admin/CRM/new-shipment/{recipe}")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["title"] = "Новая отгрузка, выбор рецепта"
        context["site_header"] = "Главная"
        context["has_permission"] = True

        return context


class NewShipmentView(FormView):
    form_class = NewShipmentForm
    template_name = "admin/custom_form.html"

    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs

    def get_available_pallets(self, recipe_id):
        pallets = []
        minced_meat_batch_mixes = MincedMeatBatchMix.objects.filter(
            minced_meat_batch__recipe_id=recipe_id, statuses__status__codename="work_is_finished"
        ).all()
        excludes = [
            i.minced_meat_batch_mix_id
            for i in ShipmentPallet.objects.filter(minced_meat_batch_mix__in=minced_meat_batch_mixes).all()
        ]

        for mix in minced_meat_batch_mixes:
            if mix.pk in excludes:
                continue
        return pallets

    def form_valid(self, form: EditPalletForm):

        pallets = form.cleaned_data["pallets"]
        customer = form.cleaned_data["customer"]

        shipment = Shipment.objects.create(customer=customer, created_at=datetime.utcnow())

        for pallet in pallets:
            minced_meat_batch_mix_id, number, weight = pallet.split(":")
            ShipmentPallet.objects.create(
                minced_meat_batch_mix_id=minced_meat_batch_mix_id,
                shipment=shipment,
                number=number,
                weight=Decimal(weight),
                created_at=datetime.utcnow(),
            )

        return redirect("/admin")

    def get_initial(self):
        initial = super().get_initial()
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Новая отгрузка "
        context["site_header"] = "Главная"
        context["has_permission"] = True

        return context
