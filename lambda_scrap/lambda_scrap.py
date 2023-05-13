import boto3
from datetime import datetime
from scrap import MeffScraper
from decimal import Decimal, Context, ROUND_HALF_EVEN
import pandas as pd

DYNAMODB_CONTEXT = Context(prec=3, rounding=ROUND_HALF_EVEN)

def convert_floats_to_decimals(df: pd.DataFrame) -> pd.DataFrame:
    """
    Converts all float values in the DataFrame to rounded decimal values.

    Args:
        df (pandas.DataFrame): The DataFrame to convert.

    Returns:
        pandas.DataFrame: The DataFrame with float values converted to decimals.
    """
    for column in df.columns:
        if df[column].dtype == 'float64':
            df[column] = df[column].apply(lambda x: DYNAMODB_CONTEXT.create_decimal_from_float(x).quantize(Decimal(".01"), rounding=ROUND_HALF_EVEN))
    return df


def run_web_scraping():
    """
    Scrapes the Meff website for financial derivatives data, cleans the data, 
    and stores it in a DynamoDB table.

    The function starts by initializing a connection to the DynamoDB service and the table 
    where the data will be stored. It then scrapes the Meff website for data and processes it. 
    The data is then stored in the DynamoDB table.

    Note:
        This function does not return a value. The result of the scraping is stored directly in the DynamoDB table.
    """
    dynamodb = boto3.resource('dynamodb', region_name='eu-central-1')
    table = dynamodb.Table('MeffScrapping')

    url = "https://www.meff.es/esp/Derivados-Financieros/Ficha/FIEM_MiniIbex_35"

    meff_scraper = MeffScraper(url)
    meff_scraper.run()
    
    today = datetime.today().strftime('%Y-%m-%d')
    options = convert_floats_to_decimals(meff_scraper.options)
    options = options.to_dict(orient='records')
    futures = DYNAMODB_CONTEXT.create_decimal_from_float(meff_scraper.futuros).quantize(Decimal(".01"), rounding=ROUND_HALF_EVEN)


    item = {
        'Date': today,
        'Futures': futures,
        'Options': options
    }

    table.put_item(Item=item)

