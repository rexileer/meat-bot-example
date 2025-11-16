from Web.CRM.models import RawMeatBatch


async def get_bzv(raw_meat_batch: RawMeatBatch):
    for status in raw_meat_batch.statuses.all():
        if status.status.codename == "laboratory_analyze" and status.additional_data:
            bzd = (
                float(status.additional_data["protein_proportion"]),
                float(status.additional_data["fat_proportion"]),
                float(status.additional_data["moisture_proportion"]),
            )
            return bzd
    return 0, 0, 0
