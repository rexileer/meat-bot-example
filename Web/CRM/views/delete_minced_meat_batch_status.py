from django.shortcuts import redirect
from django.views import View

from Web.CRM.models import TotalMincedMeatBatchStatus, MincedMeatBatch


class DeleteMincedMeatBatchStatus(View):

    def get(self, request, *args, **kwargs):
        status = TotalMincedMeatBatchStatus.objects.filter(pk=int(request.resolver_match.kwargs["status_id"])).first()
        status.delete()

        minced_meat_batch = MincedMeatBatch.objects.filter(
            pk=request.resolver_match.kwargs["minced_meat_batch_id"]
        ).first()

        return redirect(f"/admin/CRM/mincedmeatbatch/{minced_meat_batch.id}/change/")
