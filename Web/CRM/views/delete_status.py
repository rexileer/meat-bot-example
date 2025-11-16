from django.shortcuts import redirect
from django.views import View

from Web.CRM.models import RawMeatBatchStatus, RawMeatBatch


class DeleteStatus(View):

    def get(self, request, *args, **kwargs):
        status = RawMeatBatchStatus.objects.filter(pk=int(request.resolver_match.kwargs["status_id"])).first()
        status.delete()

        raw_meat_batch = RawMeatBatch.objects.filter(pk=request.resolver_match.kwargs["raw_meat_batch_id"]).first()

        return redirect(f"/admin/CRM/rawmeatbatch/{raw_meat_batch.id}/change/")
