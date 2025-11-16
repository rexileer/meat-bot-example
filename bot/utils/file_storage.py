import mimetypes
import uuid
from io import BytesIO

from data.config import env
from bot.loader import bot, minio
from bot.utils.datatables import fill_wws


def get_mime_type(file_type: str) -> str:
    if mimetypes.types_map.get(file_type):
        mime_type = mimetypes.types_map[file_type]
    else:
        mime_type = "application/octet-stream"
    return mime_type


async def save_file_from_telegram(file_id: str, dir_name: str, file_type: str, is_report: bool = False) -> str:
    file = BytesIO()
    await bot.download_file_by_id(file_id=file_id, destination=file)
    if is_report:
        file = fill_wws(file)

    object_name = f"{dir_name}/{uuid.uuid4().hex}{file_type}"

    minio.put_object(
        bucket_name=env.MINIO_MAIN_BUCKET,
        object_name=object_name,
        data=file,
        length=len(file.getvalue()),
        content_type=get_mime_type(file_type),
    )
    return object_name


def save_file_from_bytesio(bytesio: BytesIO, dir_name: str, file_type: str) -> str:
    object_name = f"{dir_name}/{uuid.uuid4().hex}{file_type}"

    minio.put_object(
        bucket_name=env.MINIO_MAIN_BUCKET,
        object_name=object_name,
        data=bytesio,
        length=len(bytesio.getvalue()),
        content_type=get_mime_type(file_type),
    )
    return object_name
