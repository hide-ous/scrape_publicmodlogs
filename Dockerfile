#Deriving the latest base image
FROM python:latest


WORKDIR /

ADD main.py /
ADD requirements.txt /

RUN pip install -r requirements.txt

CMD [ "python", "./main.py"]