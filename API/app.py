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
    """
    Fetches and returns the partition Key from a DynamoDB table, that uses "Date"
    as a partition key.

    Args:
        table: A DynamoDB table.

    Returns:
        set: A set containing the partition keys.
    """
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
    """
    Retrieves an item from a DynamoDB table based on a given date.

    Args:
        table (boto3.resources.factory.dynamodb.Table): A DynamoDB table.
        date (str): The date for which to fetch the item.

    Returns:
        dict: The item corresponding to the given date.
    """
    response = table.get_item(
        Key={
            'Date': date
        }
    )
    item = response.get('Item')
    return item

def decimal_to_float(obj):
    """
    Converts a Decimal object to a float.

    Args:
        obj (Decimal): The Decimal object to convert.

    Returns:
        float: The float representation of the Decimal object.

    Raises:
        TypeError: If the object is not of type Decimal.
    """
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError("Type not serializable")

#Routes
@app.route("/", methods=["GET"])
def welcome():
    """
    Defines the home route that provides API documentation.

    Returns:
        str: A string containing HTML-formatted API documentation.
    """
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
    """
    Defines the /ping route that checks the API status.

    Returns:
        Response: A Flask Response object containing a JSON with the status of the API.
    """
    return jsonify({"status": "ok"})

@app.route('/get_partitions', methods=['GET'])
def unique_dates():
    """
    Defines the /get_partitions route that fetches the partition keys from the DynamoDB table.

    Returns:
        Response: A Flask Response object containing a JSON with the list of partition keys.
    """
    dates = get_unique_dates(table)
    return jsonify(list(dates))


@app.route("/get_item", methods=["GET"])
def get_item_route():
    """
    Defines the /get_item route that fetches an item from the DynamoDB table based on a given date.

    Returns:
        Response: A Flask Response object containing a JSON with the fetched item.
        If the date parameter is not provided, returns a JSON with an error message.
    """
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
