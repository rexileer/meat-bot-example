import re
from datetime import datetime
from decimal import Decimal

from aiohttp import ClientSession
from bs4 import BeautifulSoup
from pydantic import BaseModel

from data.constants import DATE_FORMAT


class VetResponse(BaseModel):
    weight: Decimal
    organization: str
    manufacturer: str
    production: str
    document_number: str
    document_date: str
    manufacture_date: str
    expiration_date: str
    link: str


async def parse_document_text(text):

    try:
        if ";" in text:
            document_date_list = list()
            document_number_list = list()
            document_elems = text.split(";")
            for elem in document_elems:
                document_args = elem.split()
                document_number_list.append(document_args[1])
                document_date_list.append(document_args[3])
            document_number = "/".join(document_number_list)
            document_date = "/".join(document_date_list)
        else:
            document_args = text.split()
            document_number = document_args[1]
            document_date = document_args[3]
    except Exception:
        return "None", "None"

    return document_date, document_number


async def fetch_vet(link: str) -> VetResponse:
    async with ClientSession() as session:
        response = await session.get(link)
        html = await response.text()

    soup = BeautifulSoup(html, features="html.parser")

    weight_group_element = soup.find("div", text="Объём")
    weight_element = weight_group_element.find_next("div")
    weight = Decimal(weight_element.next_element.next_element.replace("кг", ""))

    product_name = (
        soup.find("div", text="Наименование продукции при производстве").find_next("div").find("span").getText()
    )

    organization_group_element = soup.find("small", text="Сведения об отправителе").parent.parent.find(
        "div", text="Название предприятия"
    )
    organization_element = organization_group_element.find_next("div")
    organization = organization_element.getText()

    manufacturer_element = soup.find("div", text="Выработанная").find_next("div").text
    manufacturer = re.sub(r"\s+", " ", manufacturer_element).lstrip()

    document_text = soup.find("div", text="Номер и дата входящего ВСД").find_next("div").find("span").getText()
    document_date, document_number = await parse_document_text(document_text)

    manufacture_date = (
        soup.find("div", text="Дата выработки продукции").find_next("div").find("span").getText().rstrip(":00")
    )

    now = datetime.now()
    expiration_date = soup.find("div", text="Годен до").find_next("div").find("span").getText().rstrip(":00")
    expiration_date_datetime = datetime.strptime(
        expiration_date if "-" not in expiration_date else expiration_date.split(" - ")[-1], DATE_FORMAT
    )

    return VetResponse(
        weight=weight,
        organization=organization,
        manufacturer=manufacturer,
        production=product_name,
        document_number=document_number,
        document_date=document_date,
        manufacture_date=manufacture_date,
        expiration_date=expiration_date,
        link=f"{link} - ОСГ: {(expiration_date_datetime - now).days}",
    )
