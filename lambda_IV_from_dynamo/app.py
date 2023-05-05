from lambda_iv_from_dynamo import calculate_variables_and_store

def lambda_handler():
    calculate_variables_and_store()
    return "OK"
    
if __name__ == '__main__':
    lambda_handler()

