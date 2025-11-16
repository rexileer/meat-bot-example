import logging
from django.forms import Form, ChoiceField, CharField, MultipleChoiceField
from django.utils.safestring import mark_safe

from Web.CRM.models import Recipe, MincedMeatBatchMix, ShipmentPallet

logger = logging.getLogger("logger")


class SetRecipeNewShipmentForm(Form):
    # Важно: не выполнять запросы к БД на уровне модуля (ломает migrate на пустой БД)
    recipe = ChoiceField(choices=[], label="Рецепт", required=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Заполняем варианты уже при создании формы, когда БД гарантированно готова
        self.fields["recipe"].choices = [(r.id, r.name) for r in Recipe.objects.all()]


class NewShipmentForm(Form):
    customer = CharField(label="Кому отгружаем?", required=True)

    def get_available_pallets(self):
        self.recipe_id = self.request.resolver_match.kwargs["recipe_id"]
        pallets = []
        minced_meat_batch_mixes = MincedMeatBatchMix.objects.filter(
            minced_meat_batch__recipe_id=self.recipe_id, statuses__status__codename="work_is_finished"
        ).all()
        released_mixes = [i.minced_meat_batch_mix for i in ShipmentPallet.objects.all()]
        finished_mixes = [x for x in minced_meat_batch_mixes if x not in released_mixes]
        for mix in finished_mixes:
            mix_pallet_id = mix.statuses.filter(status__codename="mixer_tiller_mix_meat_end").first()
            if mix_pallet_id:
                pallet_id = mix_pallet_id.additional_data.get("pallet")
                if pallet_id:
                    status = mix.statuses.filter(status__codename="palletizing_end").first()
                    if status and len(status.additional_data) > 4 and pallet_id:
                        status_data = status.additional_data
                        pallets.append(
                            (
                                mark_safe(
                                    f"{mix.id}:{pallet_id}:{status_data['weight_raw'] if status_data.get('weight_raw') else '0'}"  # NOQA
                                ),
                                mark_safe(
                                    f"Паллет: {pallet_id} ({status_data['weight_raw'] if status_data.get('weight_raw') else '0'} кг.) Дата паллетирования: {status.created_at:%d-%m-%Y %H-%M}"  # NOQA
                                ),
                            )
                        )
        return pallets

    def __init__(self, *args, **kwargs):

        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)
        self.fields["pallets"] = MultipleChoiceField(
            label="Паллеты (для выбора нескольких зажать CTRL)", required=True, choices=self.get_available_pallets()
        )
        self.desc = mark_safe(f"Название рецепта: <strong>{Recipe.objects.get(id=self.recipe_id).name}</strong>")
