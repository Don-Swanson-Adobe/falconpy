import json
import boto3
from botocore.exceptions import ClientError


def get_secret(key_type):
    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(service_name='secretsmanager', region_name="us-east-1")

    try:
        get_secret_value_response = client.get_secret_value(SecretId="APIKEY")
    except ClientError as e:
        raise e

    # Decrypts secret using the associated KMS key.
    secrets = json.loads(get_secret_value_response['SecretString'])
    key = secrets[key_type]
    return key

def lambda_handler(event, context):    
    print(event)
    httpMethod = json.dumps(event["httpMethod"]).strip('"')
    resource = json.dumps(event["resource"]).strip('"')
    print("Request: "+httpMethod+" "+resource)
    if 'auth' in event["headers"]:
        auth = json.dumps(event["headers"]["auth"]).strip('"')
    elif 'Auth' in event["headers"]:
        auth = json.dumps(event["headers"]["Auth"]).strip('"')
    else:
        auth = "unauthorized"
    print("Auth: "+auth)
    
    if 'version' in event["headers"]:
        version = json.dumps(event["headers"]["version"]).strip('"')
    else: 
        version = "all"

    #Verify auth and run appropriate resource path
    if auth == "unauthorized":
        data_body = "Error: You are not authorized to utilize this API"
        code = 401

    elif httpMethod == "GET" and resource == "/API/health_check":
        HC_key = get_secret("health_check")
        if auth == HC_key:
            from health_check import health_check
            from health_check import get_falcon_secret
            from falconpy import APIHarness
            code,data_body = health_check(event)
        else:
            data_body = "Error: You are not authorized to utilize this API"
            print("Auth: "+auth+" is unauthorized")
            code = 401

    elif httpMethod == "GET":
        auth_keys = get_secret("auth_keys")
        
        if resource == "/API/sensor_versions" and auth in auth_keys:
            from sensor_versions import sensor_versions_db
            code,data_body = sensor_versions_db(version)
        
        elif resource == "/API/container_paths" and auth in auth_keys:
            from container_paths import container_paths_db
            code,data_body = container_paths_db(version)    
            
        elif resource == "/API/latest_kernels" and auth in auth_keys:
            from latest_kernels import kernel_list_db
            code,data_body = kernel_list_db(version)
            
        elif resource == "/API/proposed_sensor_versions" and auth in auth_keys:
            from proposed_sensor_versions import proposed_sensor_versions_db
            code,data_body = proposed_sensor_versions_db(version)
            
        elif resource == "/API/sensor_date_changes" and auth in auth_keys:
            from sensor_change_dates import sensor_change_dates_db
            code,data_body = sensor_change_dates_db(version)
        
        else:
            data_body = "Error: You are not authorized to utilize this API"
            print("Auth: "+auth+" is unauthorized")
            code = 401
        
    elif httpMethod == "PATCH":
        update_key = get_secret("update_key")

        if resource == "/API/sensor_versions/up" and auth == update_key:
            from sensor_versions import update_sensor_versions_db
            code,data_body = update_sensor_versions_db(event)
            
        elif resource == "/API/container_paths/up" and auth == update_key:
            from container_paths import update_container_paths_db
            code,data_body = update_container_paths_db(event)
            
        elif resource == "/API/latest_kernels/up" and auth == update_key:
            from latest_kernels import update_kernel_list_db
            code,data_body = update_kernel_list_db(event)
            
        elif resource == "/API/proposed_sensor_versions/up" and auth == update_key:
            from proposed_sensor_versions import update_proposed_sensor_versions_db
            code,data_body = update_proposed_sensor_versions_db(event)
        
        else:
            data_body = "Error: You are not authorized to utilize this API"
            print("Auth: "+auth+" is unauthorized")
            code = 401        
        
    else:
        data_body = "Error: You are not authorized to utilize this API Method"
        code = 401
 
    return {
        'statusCode': code,
        'headers': {"content-type": "application/json"},
        'body': data_body  
        }
