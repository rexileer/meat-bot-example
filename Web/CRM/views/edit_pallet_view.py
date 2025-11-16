import json

from django.shortcuts import redirect
from django.views.generic import FormView

from Web.CRM.forms.edit_pallet_form import EditPalletForm
from Web.CRM.models import MincedMeatBatchMix


class EditPalletView(FormView):
    form_class = EditPalletForm
    template_name = "admin/custom_form.html"

    def form_valid(self, form: EditPalletForm):
        minced_meat_batch_mix_id = self.request.resolver_match.kwargs["minced_meat_batch_mix_id"]
        pallet_number = self.request.resolver_match.kwargs["pallet_number"]
        minced_meat_batch_mix = MincedMeatBatchMix.objects.get(pk=minced_meat_batch_mix_id)
        weight = form.cleaned_data["weight"]

        status = minced_meat_batch_mix.statuses.filter(status__codename="palletizing").first()
        if status and status.additional_data.get("pallets"):
            additional_data = status.additional_data
            for pallet in additional_data["pallets"]:
                if pallet["number"] == pallet_number:
                    pallet["weight"] = str(weight)
            status.additional_data = json.dumps(additional_data)
            status.save()

        return redirect(f"/admin/crm/mincedmeatbatch/{minced_meat_batch_mix.minced_meat_batch.id}/change/")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["title"] = "Изменить информацию о палетте"
        context["site_header"] = "Главная"
        context["has_permission"] = True

        return context
