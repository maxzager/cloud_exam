from flask import Flask, request, jsonify
import boto3
import os
import json
from decimal import Decimal

app = Flask(__name__)
#Configuration DynamoDB
aws_access_key_id = os.environ.get("aws_access_key_id")
aws_secret_access_key = os.environ.get("aws_secret_access_key")

dynamodb = boto3.resource(
    "dynamodb",
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key,
    region_name="eu-central-1"
)
table = dynamodb.Table('MeffScrapping')

#Functions
def get_unique_dates(table):
    unique_dates = set()
    response = table.scan()
    for item in response['Items']:
        unique_dates.add(item['Date'])
    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        for item in response['Items']:
            unique_dates.add(item['Date'])
    return unique_dates


def get_item(table, date):
    response = table.get_item(
        Key={
            'Date': date
        }
    )
    item = response.get('Item')
    return item

def decimal_to_float(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError("Type not serializable")

#Routes
@app.route("/", methods=["GET"])
def welcome():
    documentation = """
    <strong>Welcome to the Meff Scrapping API.</strong> 
    The following endpoints are available:

    1. <strong>/ping</strong>
        Method: GET
        Description: Checks the API status, returns {"status": "ok"}

    2. <strong>/get_partitions</strong>
        Method: GET
        Description: Returns a list of the partition keys ("Date") present in the DynamoDB table

    3. <strong>/get_item</strong>
        Method: GET
        Parameters: date (format 'YYYY-MM-DD')
        Description: Returns the item with the specified date in the DynamoDB table

    To use the endpoints, make an HTTP request using the specified method and route.

    Web scraping project by:
    - <strong>Maximiliano Zambelli Greminger</strong>

    As a practice for the "Cloud Module" from the Master in AI, mIAx 10, Instituto BME.

    The data is scraped for educational purposes only.

    """
    return documentation.replace("\n", "<br>")



@app.route("/ping", methods=["GET"])
def ping():
    return jsonify({"status": "ok"})

@app.route('/get_partitions', methods=['GET'])
def unique_dates():
    dates = get_unique_dates(table)
    return jsonify(list(dates))


@app.route("/get_item", methods=["GET"])
def get_item_route():
    date = request.args.get("date")
    if date:
        # Implementa la función para obtener el ítem según la fecha
        item = get_item(table, date)
        response = app.response_class(
            response=json.dumps({"item": item}, indent=2, default=decimal_to_float),
            status=200,
            mimetype="application/json"
        )
        return response
    else:
        return jsonify({"error": "Date parameter is required"}), 400

if __name__ == '__main__':
    app.run(os.getenv("HOST", "0.0.0.0"), port=os.getenv("PORT", 8080))
