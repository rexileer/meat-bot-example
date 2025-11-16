"""
URL configuration for web project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from datetime import datetime

from django.conf.urls.static import static
from django.urls import path, register_converter

from Web.CRM.admin import crm_admin
from Web.CRM.views.delete_meat_blank_status import DeleteMeatBlankStatus
from Web.CRM.views.delete_minced_meat_batch_status import DeleteMincedMeatBatchStatus
from Web.CRM.views.delete_pallet_view import DeletePalletView
from Web.CRM.views.delete_status import DeleteStatus
from Web.CRM.views.download_acceptance_certificate_view import download_acceptance_certificate
from Web.CRM.views.edit_pallet_view import EditPalletView
from Web.CRM.views.edit_raw_meat_batch_view import EditRawMeatBatchView
from Web.CRM.views.minced_meat_export import process_export_minced_meat
from Web.CRM.views.new_shipment_view import SetRecipeNewShipmentView, NewShipmentView
from Web.CRM.views.raw_meat_batch_export import process_export_raw_meat_batch
from Web.web import settings


class DateConverter:
    regex = r"\d{4}\d{2}\d{2}"

    def to_python(self, value):
        return datetime.strptime(value, "%Y%m%d")

    def to_url(self, value):
        return value


register_converter(DateConverter, "yyyymmdd")

urlpatterns = (
    [
        path("admin/CRM/rawmeatbatch/export/change/", process_export_raw_meat_batch),
        path("admin/CRM/datatables/minced_meat/<yyyymmdd:date>", process_export_minced_meat),
        path("admin/CRM/documents/acceptance_certificate", download_acceptance_certificate),
        path("admin/CRM/edit-raw-meat-batch/<int:raw_meat_batch_id>", EditRawMeatBatchView.as_view()),
        path(
            "admin/CRM/delete-pallet/<int:minced_meat_batch_mix_id>/p/<str:pallet_number>", DeletePalletView.as_view()
        ),
        path("admin/CRM/edit-pallet/<int:minced_meat_batch_mix_id>/p/<str:pallet_number>", EditPalletView.as_view()),
        path("admin/CRM/set-recipe-new-shipment", SetRecipeNewShipmentView.as_view()),
        path("admin/CRM/new-shipment/<int:recipe_id>", NewShipmentView.as_view()),
        path("admin/CRM/delete_status/<int:raw_meat_batch_id>/p/<int:status_id>", DeleteStatus.as_view()),
        path(
            "admin/CRM/delete_meat_blank_status/<int:meat_blank_id>/p/<int:status_id>", DeleteMeatBlankStatus.as_view()
        ),
        path(
            "admin/CRM/delete_minced_meat_batch_status/<int:minced_meat_batch_id>/p/<int:status_id>",
            DeleteMincedMeatBatchStatus.as_view(),
        ),
        path("admin/", crm_admin.urls),
    ]
    + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
)
