import os
import boto3
import pandas as pd

def get_unique_dates(table):
    """
    Fetches unique dates from the provided DynamoDB table.

    Args:
        table(boto3 table): The DynamoDB table to fetch unique dates from.

    Returns:
        set: A set containing unique dates found in the DynamoDB table.
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
    Fetches an item from the provided DynamoDB table using the given date as the key.

    Args:
        table (boto3.resources.factory.dynamodb.Table): The DynamoDB table to fetch the item from.
        date (str): The date used as a key to fetch the item.

    Returns:
        pandas.DataFrame: A DataFrame containing the fetched item if it exists, otherwise an empty DataFrame.
    """
    response = table.get_item(
        Key={
            'Date': date
        }
    )
    item = response.get('Item')
    if item:
        return pd.DataFrame(item["Options"])
    return pd.DataFrame()