import logging

from django.apps import AppConfig
from django.contrib.auth import get_user_model
from django.db import ProgrammingError

from Web.CRM.constans.companies import COMPANIES_LIST
from Web.CRM.constans.positions import position_dict
from Web.CRM.constans.raw_material import DEFAULT_RAW_MATERIAL_LIST
from Web.CRM.constans.recipe import DEFAULT_RECIPES
from Web.CRM.constans.status import DEFAULT_STATUS_LIST
from data.config import env


class CrmConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "Web.CRM"

    def ready(self):
        user_model = get_user_model()

        try:
            user_model.objects.get(username=env.ADMIN_USER)
            self.auto_upload_positions()
            self.auto_upload_recipe()
            self.auto_upload_statuses()
            self.auto_upload_raw_materials()
            self.auto_upload_company()
            self.auto_upload_shocker()
        except user_model.DoesNotExist:
            user_model.objects.create_superuser(env.ADMIN_USER, f"{env.ADMIN_USER}@meatbot.com", env.ADMIN_PASSWORD)
        except ProgrammingError as e:
            print(e)

    def auto_upload_shocker(self):
        MyModel = self.get_model("ShockerCamera")
        logging.info("Загрузка шокеров в бд")
        for val in range(1, 5):
            MyModel.objects.get_or_create(shocker_id=val)
        logging.info("Успех!")

    def auto_upload_company(self):
        MyModel = self.get_model("Company")
        logging.info("Загрузка компаний в бд")
        for val in COMPANIES_LIST:
            MyModel.objects.get_or_create(**val)
        logging.info("Успех!")

    def auto_upload_raw_materials(self):
        MyModel = self.get_model("RawMaterial")
        logging.info("Загрузка типов сырья в бд")
        for val in DEFAULT_RAW_MATERIAL_LIST:
            MyModel.objects.get_or_create(type=val["type"], name=val["name"])
        logging.info("Успех!")

    def auto_upload_positions(self):
        MyModel = self.get_model("Position")
        logging.info("Загрузка должностей в бд")
        for key, val in position_dict.items():
            MyModel.objects.get_or_create(name=val, code_name=key)
        logging.info("Успех!")

    def auto_upload_recipe(self):
        MyModel = self.get_model("Recipe")
        logging.info("Загрузка рецептов в бд")
        for val in DEFAULT_RECIPES:
            MyModel.objects.get_or_create(name=val["name"])
        logging.info("Успех!")

    def auto_upload_statuses(self):
        MyModel = self.get_model("status")
        logging.info("Загрузка статусов в бд")
        for val in DEFAULT_STATUS_LIST:
            MyModel.objects.get_or_create(name=val["name"], codename=val["codename"])
        logging.info("Успех!")
