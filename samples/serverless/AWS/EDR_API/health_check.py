import json
import boto3
from botocore.exceptions import ClientError
from falconpy import APIHarness

# Function to grab secrets
def get_falcon_secret():
    session = boto3.session.Session()
    client = session.client(service_name='secretsmanager', region_name="us-east-1")
    try:
        get_secret_value_response = client.get_secret_value(SecretId="HostSecretKey")
    except ClientError as e:
        raise e

    # Decrypts secret using the associated KMS key.
    secrets = json.loads(get_secret_value_response['SecretString'])
    clientid = secrets['clientid']
    clientsec = secrets['clientsec']
    return clientid, clientsec
    
def health_check(event):
    clientid, clientsec = get_falcon_secret()
    falcon = APIHarness(client_id=clientid, client_secret=clientsec)
    print("Getting host details")
    body=event["body"]
    if body is not None:
        data = json.loads(body)
        for key, value in data.items():
            if key.lower() == "aid":
                aid = value.lower().replace("-","")
            else:
                return 400, "Error: Invalid JSON body, missing 'aid' key"
    else:
        return 400, "Error: Invalid JSON body, missing 'aid' key"
    response = falcon.command("GetDeviceDetails", ids=aid)
    if response["status_code"] == 200:
        print("Formatting host details")
        from datetime import datetime, timedelta
        offset = (datetime.utcnow() - timedelta(minutes = 15)).strftime('%Y-%m-%dT%H:%M:%SZ')
        host_detail=response["body"]["resources"]
        print(host_detail)
        tag = []
        for detail in host_detail:
            rfm = detail["reduced_functionality_mode"]
            last_seen = detail["last_seen"]
            tag = detail["tags"]
            groups = detail["groups"]
        tags = ""   
        for i in tag:
            tags += i.replace('SensorGroupingTags/','')
            tags += ", "
    else:
        return response["status_code"], response["body"]["errors"][0]["message"]
    if last_seen > offset:
        online = True
    else:
        online = False
    if rfm == "no":
        rfm = False
    if rfm == "yes":
        rfm = True
    message = {"AID": aid, "RFM (Should be False)": rfm, "Online": online, "Tags": tags, "Groups": groups}
    print(message)
    data_body = json.dumps(message)
    code = 200
    return code,data_body
