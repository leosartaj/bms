FROM python:3.6.8-jessie

RUN pip install --upgrade pip
RUN pip install pandas bs4 requests lxml

RUN mkdir /bms
WORKDIR /bms

CMD ["python3", "bms.py"]
