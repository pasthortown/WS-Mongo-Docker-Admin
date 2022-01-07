FROM python:3.8

WORKDIR /usr/src/app

RUN apt-get update
RUN apt-get install -y libsasl2-dev libldap2-dev libssl-dev
COPY requirements.txt ./
RUN pip install -r requirements.txt
RUN echo "America/Bogota" > /etc/timezone

COPY auth.py .
COPY mailer.py .
COPY Templates ./Templates

EXPOSE 5050

CMD [ "python", "auth.py" ]