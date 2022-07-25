FROM python:3.8

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install -r requirements.txt
RUN echo "America/Bogota" > /etc/timezone

COPY server.py .
COPY mailer.py .
COPY Templates ./Templates

EXPOSE 5050

CMD [ "python", "server.py" ]