FROM python:3.10
ENV TZ="Europe/Moscow"
RUN apt-get update && \
    apt-get install -y locales && \
    sed -i -e 's/# ru_RU.UTF-8 UTF-8/ru_RU.UTF-8 UTF-8/' /etc/locale.gen && \
    dpkg-reconfigure --frontend=noninteractive locales
ENV LANG ru_RU.UTF-8
ENV LC_ALL ru_RU.UTF-8

WORKDIR /src
COPY ./requirements.txt /src
RUN pip install -r requirements.txt
COPY . /src
ENV PYTHONPATH /src
