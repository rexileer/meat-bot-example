import asyncio
import datetime
import logging
import random
import requests
import time
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, field
from multiprocessing import Pipe
from typing import List


from bs4 import BeautifulSoup
from bs4 import BeautifulSoup as Soup


from data.config import env

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36"
    ),
    "content-type": "text/xml",
}
executor = ProcessPoolExecutor(10)
REQUESTS_COUNT = 5
NEW_APPL_URL = "https://api.vetrf.ru/platform/services/2.1/ApplicationManagementService"
RECEIVE_APPL_RES_URL = (
    "https://api.vetrf.ru/platform/services/2.1/ApplicationManagementService/receiveApplicationResult"
)
VET_DOC_TEMPLATE_URL = "https://mercury.vetrf.ru/pub/operatorui?_action=findVetDocumentFormByUuid&uuid="


@dataclass
class AppsData:
    statuses: List[str] = field(default_factory=lambda: ["" for m in range(REQUESTS_COUNT)])
    soups: List[Soup] = field(default_factory=lambda: [Soup() for m in range(REQUESTS_COUNT)])


def get_new_app_xml(company, date):
    local_id = f"a{random.randint(1000, 9999)}"
    return f"""
        <SOAP-ENV:Envelope xmlns:dt="http://api.vetrf.ru/schema/cdm/dictionary/v2"
                           xmlns:bs="http://api.vetrf.ru/schema/cdm/base"
                           xmlns:merc="http://api.vetrf.ru/schema/cdm/mercury/g2b/applications/v2"
                           xmlns:apldef="http://api.vetrf.ru/schema/cdm/application/ws-definitions"
                           xmlns:apl="http://api.vetrf.ru/schema/cdm/application"
                           xmlns:vd="http://api.vetrf.ru/schema/cdm/mercury/vet-document/v2"
                           xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
          <SOAP-ENV:Header/>
          <SOAP-ENV:Body>
            <apldef:submitApplicationRequest>
              <apldef:apiKey>{company.apikey}</apldef:apiKey>
              <apl:application>
                <apl:serviceId>mercury-g2b.service:2.1</apl:serviceId>
                <apl:issuerId>{company.issuerid}</apl:issuerId>
                <apl:issueDate>{date[0].strftime('%Y-%m-%dT%H:%M:%S')}</apl:issueDate>
                <apl:data>
                  <merc:getVetDocumentListRequest>
                    <merc:localTransactionId>{local_id}</merc:localTransactionId>
                    <merc:initiator>
                      <vd:login>{env.LOGIN}</vd:login>
                    </merc:initiator>
                    <bs:listOptions>
                      <bs:count>1000</bs:count>
                    </bs:listOptions>
                    <vd:issueDateInterval>
                      <bs:beginDate>{date[1].strftime('%Y-%m-%dT%H:%M:%S')}</bs:beginDate>
                      <bs:endDate>{date[0].strftime('%Y-%m-%dT%H:%M:%S')}</bs:endDate>
                    </vd:issueDateInterval>
                    <dt:enterpriseGuid>{company.guid}</dt:enterpriseGuid>
                  </merc:getVetDocumentListRequest>
                </apl:data>
              </apl:application>
            </apldef:submitApplicationRequest>
          </SOAP-ENV:Body>
        </SOAP-ENV:Envelope>
        """


def execute_app_xml(app_id, company):
    return f"""
        <env:Envelope xmlns:env="http://schemas.xmlsoap.org/soap/envelope/"
                      xmlns:ws="http://api.vetrf.ru/schema/cdm/application/ws-definitions">
        <env:Header/>
          <env:Body>
            <ws:receiveApplicationResultRequest>
            <ws:apiKey>{company.apikey}</ws:apiKey>
            <ws:issuerId>{company.issuerid}</ws:issuerId>
            <ws:applicationId>{app_id}</ws:applicationId>
          </ws:receiveApplicationResultRequest>
          </env:Body>
        </env:Envelope>
        """


def new_applications(company):
    app_ids = list()

    # (end, start)
    now = datetime.datetime.now() + datetime.timedelta(hours=3)
    intervals = list()
    for d in range(REQUESTS_COUNT):
        intervals.append((now, now - datetime.timedelta(days=1)))
        now = now - datetime.timedelta(days=1)

    for date in intervals:
        body = get_new_app_xml(company, date)
        response = requests.post(
            NEW_APPL_URL, auth=(company.api_login, company.api_pass), data=body, verify=False, headers=headers
        )
        html = response.content
        parsed_html = BeautifulSoup(html)
        app_ids.append(parsed_html.find("applicationid").text)
    return app_ids


async def check_process(state, output):

    resource = 1000
    while resource:
        if output.poll():
            msg = output.recv()
            await state.update_data(vet_docs_list=msg)
            break
        resource -= 1
        await asyncio.sleep(5)
    logging.info("process success")


async def start_process(state, ttn_number, company):
    import django

    django.setup()
    output_p, input_p = Pipe()

    await asyncio.to_thread(get_vet_document, ttn_number, company, input_p)
    await state.update_data(vet_docs_list=None)
    await check_process(state, output_p)


def receive_appls_data(company, appls, apps_data):
    for i in range(len(appls)):
        if apps_data.statuses[i] != "COMPLETED":
            response = requests.post(
                RECEIVE_APPL_RES_URL, auth=(company.api_login, company.api_pass), data=appls[i], headers=headers
            )
            soup = Soup(response.content, "xml")
            status = soup.find("status").text
            apps_data.soups.append(soup)
            apps_data.statuses[i] = status
            time.sleep(5)
        logging.info(apps_data.statuses)

    return apps_data


def get_vet_document(ttn_number, company, input_p):
    app_ids = new_applications(company)
    apps = [execute_app_xml(app_id, company) for app_id in app_ids]
    apps_data = AppsData()
    while apps_data.statuses != ["COMPLETED"] * REQUESTS_COUNT:
        if "REJECTED" in apps_data.statuses:
            input_p.send(0)
            input_p.close()
            return

        time.sleep(5)
        apps_data = receive_appls_data(company, apps, apps_data)

    documents = list()
    docs_with_ttn = list()
    for soup in apps_data.soups:
        documents.extend([offer for offer in soup.find_all("vd:vetDocument")])
    logging.info(len(documents))
    for doc in documents:
        referenced_docs = doc.find_all("vd:referencedDocument")
        for ref_doc in referenced_docs:
            if ref_doc.find("vd:type").text == "1" or ref_doc.find("vd:type").text == "5":
                number = ref_doc.find("vd:issueNumber").text
                logging.info(number)
                if number == ttn_number:
                    uuid = doc.find("bs:uuid").text
                    docs_with_ttn.append(uuid)
    if docs_with_ttn:
        input_p.send(docs_with_ttn)
    else:
        input_p.send(1)
    input_p.close()
