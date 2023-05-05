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
    for column in df.columns:
        if df[column].dtype == 'float64':
            df[column] = df[column].apply(lambda x: DYNAMODB_CONTEXT.create_decimal_from_float(x).quantize(Decimal(".001"), rounding=ROUND_HALF_EVEN))
    return df


def calculate_variables_and_store(): 
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
