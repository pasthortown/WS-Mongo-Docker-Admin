FROM python:3.8

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install -r requirements.txt
RUN echo "America/Bogota" > /etc/timezone

COPY catalogadmin.py .

EXPOSE 5050

CMD [ "python", "catalogadmin.py" ]