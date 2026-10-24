FROM python:3.12

WORKDIR /app

COPY . .

RUN pip install -r requirements.txt
RUN playwright install chromium

CMD ["gunicorn","-w","2","-b","0.0.0.0:8000","wsgi:app"]
