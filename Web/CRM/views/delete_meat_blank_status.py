from django.shortcuts import redirect
from django.views import View

from Web.CRM.models import MeatBlankStatus, MeatBlank


class DeleteMeatBlankStatus(View):

    def get(self, request, *args, **kwargs):
        status = MeatBlankStatus.objects.filter(pk=int(request.resolver_match.kwargs["status_id"])).first()
        status.delete()

        meat_blank = MeatBlank.objects.filter(pk=request.resolver_match.kwargs["meat_blank_id"]).first()

        return redirect(f"/admin/CRM/meatblank/{meat_blank.id}/change/")
