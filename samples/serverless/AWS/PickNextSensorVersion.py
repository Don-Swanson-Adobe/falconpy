#This automation will pick the next sensor version for you based off the current CS N-1 version and your current Dev version.
#Please see the attached PDF for how to setup Secrets Manager and the IAM role for these Lambda function
#The attached PDF Also includes instructions on how to setup and add an AWS Layer to this Lambda function to use FalconPy
#Required Layers for this Function: FalconPy

import json
import datetime
import boto3
from falconpy import APIHarness
import requests
from botocore.exceptions import ClientError

## Policy IDs/Platforms ##
dev_pols = {"windows": "<REPLACE ME>", "mac": "<REPLACE ME>", "linux": "<REPLACE ME>"}
platforms = ["windows", "mac", "linux"]
slackhook = "https://hooks.slack.com/services/<REPLACE ME>"

# Function to grab secrets
def get_secret(secret):
    session = boto3.session.Session()
    client = session.client(service_name='secretsmanager', region_name="us-east-1")
    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret)
    except ClientError as e:
        raise e

    # Decrypts secret using the associated KMS key.
    secrets = json.loads(get_secret_value_response['SecretString'])
    if secret == "CSKey":  # nosec
        clientid = secrets['clientid']
        clientsec = secrets['clientsec']
        return clientid, clientsec
    elif secret == "APIKey":  # nosec
        key = secrets['update_key']
        return key
    else:
        return "Something went wrong"


def alert_don(message):
    slack_data = json.dumps({'blocks': message})
    requests.post(url=slackhook, data=slack_data,headers={'Content-Type': 'application/json'}, timeout=5)
    print("Slack Message Sent:",message)

def grab_dates():
    dates = requests.get('https://<REPLACE ME>.execute-api.us-east-1.amazonaws.com/default/API/sensor_dates_changes', headers = {'auth': 'YOUR_API_KEY'}, timeout=5).text
    return dates

def grab_versions():
    versions = requests.get('https://<REPLACE ME>.execute-api.us-east-1.amazonaws.com/default/API/proposed_sensor_versions', headers = {'auth': 'YOUR_API_KEY'}, timeout=5).text.replace('[', '').replace(']', '')
    return versions

def set_new_versions(platform,version):
    url = 'https://<REPLACE ME>.execute-api.us-east-1.amazonaws.com/default/API/proposed_sensor_versions/up'
    payload = "{\""+platform+"\": \""+version+"\"}"
    headers = {'auth': EDR_Update_Key,'Content-Type': 'text/plain'}
    response = requests.patch(url, headers=headers, data=payload, timeout=5)
    print(response)

def lambda_handler(event, context):
    advance10days = (datetime.datetime.now() + datetime.timedelta(days=10)).strftime('%Y-%m-%d')
    dates = grab_dates()
    if advance10days in dates:
        print("Congrats! It's time to run this puppy and set some versions for the next update")
        global falcon, EDR_Update_Key
        EDR_Update_Key = get_secret("EDR_API")
        clientid, clientsec = get_secret("Falcon_key")
        falcon = APIHarness(client_id=clientid, client_secret=clientsec)

        ## Establish New Dev Versions ##
        print("\n###################\nGetting Current CS N-1 Version for Dev\n###################\n")
        for i in platforms:
            versions = falcon.command("queryCombinedSensorUpdateBuilds", platform=i)["body"]["resources"]
            for ver in versions:
                if "n-1" in ver["build"]:
                    set_new_versions(i+"_dev",".".join(ver["sensor_version"].split(".")[0:2]))
        
         ## Establish New Prd Versions ##
        for name,pol in dev_pols.items():
            version = falcon.command("getSensorUpdatePoliciesV2", ids=pol)["body"]["resources"][0]["settings"]["sensor_version"]
            set_new_versions(name+"_prd",'.'.join(version.split(".")[0:2]))

        ## Get Proposed version and output to slack ##
        proposed_versions = grab_versions()
        proposed_versions = json.loads(proposed_versions)
        message = []
        message.append({"type": "header","text": {"type": "plain_text","text": "Proposed Sensor Versions"}},)
        message.append({"type": "section", "text": {"type": "mrkdwn","text": "Please find below the proposed sensor versions for the automated change scheduled on "+advance10days+"\nIf the proposed versions are acceptable, please remember to post them in the Announcements Channel"}})
        message.append({"type": "divider"},)
        sorted_versions = dict(sorted(proposed_versions.items()))
        for key,value in sorted_versions.items():
            message.append({"type": "section", "text": {"type": "mrkdwn","text": key+": "+value}})
        alert_don(message)
    else:
        print("Not Today, old friend")