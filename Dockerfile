FROM python:3.7-stretch

WORKDIR /root
ADD . /root

RUN pip install --upgrade pip
RUN pip install -r requirements.in

ENV PYTHONPATH=/root/src
