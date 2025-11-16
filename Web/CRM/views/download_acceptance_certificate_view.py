from django.http import HttpResponse

from Web.CRM.models import RawMeatBatch
from bot.handlers.laboratory.utils.documents import generate_acceptance_certificate


def download_acceptance_certificate(request):
    raw_meat_batch_id = request.GET["raw_meat_batch_id"]

    raw_meat_batch = RawMeatBatch.objects.filter(id=raw_meat_batch_id).first()

    document = generate_acceptance_certificate(raw_meat_batch=raw_meat_batch)
    response = HttpResponse(
        document.read(), content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    response["Content-Disposition"] = 'attachment; filename="Акт входного контроля.docx"'.encode("utf-8")
    return response
