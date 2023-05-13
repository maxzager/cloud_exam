import boto3
import pandas as pd
from datetime import datetime
from add_variables import adding_variables
from decimal import Decimal, Context, ROUND_HALF_EVEN
import math



dynamodb = boto3.resource('dynamodb', region_name='eu-central-1')
table = dynamodb.Table('MeffScrapping')
DYNAMODB_CONTEXT = Context(prec=3, rounding=ROUND_HALF_EVEN)

def convert_floats_to_decimals(df: pd.DataFrame) -> pd.DataFrame:
    """
    Converts all float values in a DataFrame to Decimal values with a precision of 3.
    
    Args:
        df (pd.DataFrame): The input DataFrame whose float values are to be converted.
        
    Returns:
        pd.DataFrame: The DataFrame with all float values converted to Decimal values.
    """
    for column in df.columns:
        if df[column].dtype == 'float64':
            df[column] = df[column].apply(lambda x: DYNAMODB_CONTEXT.create_decimal_from_float(x).quantize(Decimal(".001"), rounding=ROUND_HALF_EVEN))
    return df


def calculate_variables_and_store(): 
    """
    Fetches options data from a DynamoDB table, calculates additional variables using the adding_variables class,
    cleans the data, and then stores the updated data back in the DynamoDB table.

    This function doesn't require any parameters and doesn't return anything. It performs the following steps:
    - Fetches the options data for the current date from the DynamoDB table.
    - If data is found, it uses the adding_variables class to calculate additional variables for the options data.
    - It then cleans the data by removing any rows with NaN or infinite values in the 'IV' column.
    - The cleaned data is then converted from float to Decimal.
    - Finally, the updated data is stored back in the DynamoDB table.
    """
    today = datetime.today().strftime('%Y-%m-%d')
    response = table.get_item(Key={'Date': today})
    data = response.get('Item', None)

    if data is not None:
        options_data = pd.DataFrame(data['Options'])
        futures = float(data['Futures'])

        instance = adding_variables(options_data, futures)
        instance.run()

        options = instance.options
        #delete rows with NaN or Inf values 
        options = options[~options['IV'].apply(lambda x: math.isnan(x) or math.isinf(x))]

        options = convert_floats_to_decimals(options)
        options = options.to_dict(orient='records')
        futures = DYNAMODB_CONTEXT.create_decimal_from_float(instance.futuros).quantize(Decimal(".01"), rounding=ROUND_HALF_EVEN)
        
        item = {
            'Date': today,
            'Futures': futures,
            'Options': options
        }
        table.put_item(Item=item)
