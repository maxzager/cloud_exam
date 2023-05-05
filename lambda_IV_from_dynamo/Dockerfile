FROM python:3.8-slim

RUN pip install --upgrade pip

WORKDIR /code

COPY . .

RUN pip install -r requirements.txt


EXPOSE 8080

ENV PORT=8080

CMD ["python", "app.py"]

