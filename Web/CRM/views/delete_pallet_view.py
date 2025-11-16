import json

from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.views import View

from Web.CRM.models import MincedMeatBatchMix


class DeletePalletView(View):
    template_name = "admin/custom_message.html"

    def get(self, request, *args, **kwargs):
        minced_meat_batch_mix_id = request.resolver_match.kwargs["minced_meat_batch_mix_id"]
        pallet_number = request.resolver_match.kwargs["pallet_number"]
        minced_meat_batch_mix = MincedMeatBatchMix.objects.get(pk=minced_meat_batch_mix_id)

        if not self.request.user.is_superuser:
            raise PermissionDenied()

        status = minced_meat_batch_mix.statuses.filter(status__codename="palletizing").first()
        if status and status.additional_data.get("pallets"):
            additional_data = status.additional_data
            for pallet in additional_data["pallets"]:
                if pallet["number"] == pallet_number:
                    additional_data["pallets"].remove(pallet)
            status.additional_data = json.dumps(additional_data)
            status.save()

        return redirect(f"/admin/CRM/mincedmeatbatch/{minced_meat_batch_mix.minced_meat_batch.id}/change/")
