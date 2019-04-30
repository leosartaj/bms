FROM python:3.6.8-jessie

RUN pip install --upgrade pip
RUN pip install pandas bs4 requests lxml

RUN mkdir -p /bms/examples
RUN mkdir /bms/data

COPY README.md /bms/README.md

COPY examples/ /bms/examples

COPY bms.py /bms/bms.py

WORKDIR /bms

CMD ["python3", "bms.py", "data/movies.txt", \
    "data/theaters.txt", "-e", "data/emails.txt", \
     "-c", "data/.bms_history.csv", "-d", "10"]
