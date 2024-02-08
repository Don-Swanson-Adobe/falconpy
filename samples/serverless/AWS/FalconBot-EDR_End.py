
#Please see the attached PDF for how to setup Secrets Manager and the IAM role for these Lambda function
#The attached PDF Also includes instructions on how to setup and add an AWS Layer to this Lambda function to use FalconPy
#Required Layers for this Function: FalconPy, Tabulate

import re
import json
from falconpy import APIHarness
import requests
import boto3
from botocore.exceptions import ClientError
from tabulate import tabulate
from datetime import datetime, timedelta

# Function to grab secrets
def get_secret():
    session = boto3.session.Session()
    client = session.client(service_name='secretsmanager', region_name="us-east-1")
    try:
        get_secret_value_response = client.get_secret_value(SecretId="FalconBot")
    except ClientError as e:
        raise e

    # Decrypts secret using the associated KMS key.
    secrets = json.loads(get_secret_value_response['SecretString'])
    clientid = secrets['clientid']
    clientsec = secrets['clientsec']
    print(clientid)
    return clientid, clientsec

#Function to grab host details and build the response message
def grabdetails(aid):
    response = falcon.command("GetDeviceDetails", ids=aid)
    if response["status_code"] == 200:
        host_detail=response["body"]["resources"]
        print(host_detail)
        tag = []
        for detail in host_detail:
            aid = detail["device_id"]
            rfm = detail["reduced_functionality_mode"]
            hostname = detail["hostname"]
            last_seen = detail["last_seen"]
            tag = detail["tags"]
            actual_cid = detail["cid"]
            if "linux_sensor_mode" in detail:
                sensor_mode = detail["linux_sensor_mode"]
            else:
                sensor_mode = "Kernel Mode"
        compare_last_seen = datetime.strptime(last_seen, '%Y-%m-%dT%H:%M:%SZ')
        now = datetime.now()
        tags = ""   
        for i in tag:
            tags += i.replace('SensorGroupingTags/','')
            tags += ", "
        if rfm == "yes":
            result = "rfm"
        elif sensor_mode != "Kernel Mode":
            rfm = "USER MODE"
            result = "usermode"
        elif now - compare_last_seen > timedelta(days = 2):
            result = "old_checkin"
        else:
            result = "good"
        data = tabulate([["Hostname", hostname], ["AID", aid], ["Last_Seen", last_seen], ["RFM Status", rfm], ["Tags", tags]], tablefmt="fancy_grid")
        return result, data, actual_cid
    else:
        result = "error"
        return result, response

def errorreturned(response):
    error_detail = response["body"]["errors"]
    for error in error_detail:
        # Display the API error detail
        error_code = error["status_code"]
        error_message = error["message"]
        print(error_code)
        print(error_message)
        message = []
        message.append({"type": "header","text": {"type": "plain_text","text": "Results Error"}},)
        message.append({"type": "section", "text": {"type": "mrkdwn","text": "Hello <@"+user+">, there was an error with your search:\n"}})
        message.append({"type": "divider"},)
        if str(error_code) == "404":
            message.append({"type": "section", "text": {"type": "mrkdwn","text": "Error Code:      "+str(error_code)+"\nError Message:       "+error_message+" in CID"+cid}})
        else:
            message.append({"type": "section", "text": {"type": "mrkdwn","text": "Error Code:      "+str(error_code)+"\nError Message:       "+error_message}})
        return message

def format_slack_message(data):
    message = []
    message.append({"type": "header","text": {"type": "plain_text","text": "Results"}},)
    if "es-falconbot" in channel:
        message.append({"type": "section", "text": {"type": "mrkdwn","text": "Hello <@"+user+">, here are your results:\n"}})
    else:
        message.append({"type": "section", "text": {"type": "mrkdwn","text": "Hello <@"+user+">,\nCongrats! FalconBot has determined that your install was successful and your sensor is healthy!"}})
    message.append({"type": "divider"},)
    message.append({"type": "section", "text": {"type": "mrkdwn","text": "```"+data+"```"}},)
    return message

def slack_post(message):
    slack_data = json.dumps({
        "response_type": "in_channel",
        'blocks': message
    })
    print(slack_data)
        
    final_response = requests.post(
        url=response_url, data=slack_data, timeout=5,
        headers={'Content-Type': 'application/json'}
        )   
    print(final_response.text)


def lambda_handler(event, context):
    now = datetime.now()
    global falcon, cid, aid, user, response_url, channel
    event = event['Records'][0]['Sns']['Message']
    print(event)
    user = event.split("_")[0]
    response_url = event.split("_")[1]
    cid = event.split("_")[2]
    aid = event.split("_")[3]
    channel = event.split("_")[4]
    command = event.split("_")[5]
    aid = aid.lower()
    cid = cid.lower()
    print(response_url)
    print("CID: "+cid)
    print("AID: "+aid)
    print("User: "+user)
    print("Channel: "+channel)
    print("Command: "+command)

    #Login to the API
    clientid, clientsec = get_secret()
    falcon = APIHarness(client_id=clientid, client_secret=clientsec, member_cid=cid)
     
    #FalconBot will perform a search for the host details
    result, data, actual_cid = grabdetails(aid)
    print(result)
    print(data)
    if result == "error":
        message = errorreturned(data)
    
    elif result == "rfm":
        message = []
        message.append({"type": "header","text": {"type": "plain_text","text": ":warning: WARNING! :warning:"}},)
        message.append({"type": "section", "text": {"type": "mrkdwn","text": "Hello <@"+user+">, \n*WARNING:* Your host is in RFM. Please verify your OS and kernel are supported by reviewing step 1 of the Install guide!\n"}})
        message.append({"type": "divider"},)
        message.append({"type": "section", "text": {"type": "mrkdwn","text": "If you have verified that your OS and kernel are supported, please ask for help in the #support channel. Otherwise, please install a supported OS and kernel and re-check your host with FalconBot."}})
        message.append({"type": "section", "text": {"type": "mrkdwn","text": "AID: "+aid}},)
    
    elif result == "old_checkin":
        message = []
        message.append({"type": "header","text": {"type": "plain_text","text": ":warning: WARNING! :warning:"}},)
        message.append({"type": "section", "text": {"type": "mrkdwn","text": "Hello <@"+user+">, \n*WARNING:* FalconBot has determined your host has not checked in to the Falcon Cloud in the past 48 hours. Please verify your host has network commuinication to the Falcon Cloud and that the sensor is running. Please check and verify the network requirements are met. If you have verified all network requirements and that the sensor is running, please ask for help in the #support channel."}})
        message.append({"type": "divider"},)
        message.append({"type": "section", "text": {"type": "mrkdwn","text": "```"+data+"```"}},)

    else:
        message = format_slack_message(data)
    
    slack_post(message)
    return