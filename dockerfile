FROM python:3.8-slim

RUN pip install --upgrade pip

WORKDIR /code

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

EXPOSE 8080

ENV PORT=8080

ENV AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}

ENV AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}

CMD ["python", "app.py"]

