from lambda_scrap import run_web_scraping

def lambda_handler():
    run_web_scraping()
    return "OK"
    
if __name__ == '__main__':
    lambda_handler()

