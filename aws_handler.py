import os
import boto3
import pandas as pd

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
    if item:
        return pd.DataFrame(item["Options"])
    return pd.DataFrame()