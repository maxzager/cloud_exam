import os, json
from flask import Flask
from lambda_scrap import run_web_scraping

app = Flask(__name__)
@app.route('/')
def lambda_handler():
    run_web_scraping()
    return {
        
        'statusCode': 200,
        'body': json.dumps('Success')
    }
    
if __name__ == '__main__':
    app.run(os.getenv("HOST", "0.0.0.0"), port=os.getenv("PORT", 8080))

