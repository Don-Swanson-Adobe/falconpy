#This Lambda function will Update the Sensor Versions in accordance with the change schedule. It will also update the Sensor Versions in the EDR API Database and the Wiki page.
#Please see the attached PDF for how to setup Secrets Manager and the IAM role for these Lambda function
#The attached PDF Also includes instructions on how to setup and add an AWS Layer to this Lambda function to use FalconPy
#Required Layers for this Function: FalconPy

import json
import datetime
import boto3
from falconpy import APIHarness
import requests
from botocore.exceptions import ClientError
from time import sleep

## Policy IDs/Platforms ##
policies = { #Replace with the policy IDs for your environments
    "windows_dev":"123456789012345678901234567890", 
    "mac_dev":"123456789012345678901234567890", 
    "linux_dev":"123456789012345678901234567890", 
    "windows_prd":"123456789012345678901234567890", 
    "mac_prd":"123456789012345678901234567890", 
    "linux_prd":"123456789012345678901234567890"}
platforms = ["windows_dev", "mac_dev", "linux_dev", "windows_prd", "mac_prd", "linux_prd"]
slackhook = "https://hooks.slack.com/services/<Replace_With_Your_Slack_Hook>"

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
    if secret == "Falcon_Key":  # nosec
        clientid = secrets['clientid']
        clientsec = secrets['clientsec']
        return clientid, clientsec
    else:
        key = secrets['update_key']
        return key

def slack_alert(message):
    slack_data = json.dumps({'blocks': message})
    response = requests.post(url=slackhook, data=slack_data,headers={'Content-Type': 'application/json'}, timeout=5)
    print("Slack Message Sent:",message)
    print(response)

def grab_dates():
    dates = requests.get('https://<Replace>.execute-api.us-east-1.amazonaws.com/default/API/sensor_date_changes', headers = {'auth': 'YOUR_API_KEY'}, timeout=5).text
    return dates

def grab_versions():
    versions = requests.get('https://<Replace>.execute-api.us-east-1.amazonaws.com/default/API/proposed_sensor_versions', headers = {'auth': 'YOUR_API_KEY'}, timeout=5).text.replace('[', '').replace(']', '')
    return versions

def set_new_versions(policy,version,platform):
    ## Establish New Versions ##
    print("Updating " + platform)
    plat = platform.split('_')[0]

    ver_list = falcon.command("queryCombinedSensorUpdateBuilds", platform=plat)["body"]["resources"]
    build_list = []
    for ver in ver_list:
        if version in ver["sensor_version"]:
            build_list.append(ver["build"])
    build_list.sort(reverse=True)
    build = build_list[0].split('|')[0]
    print("Build: ",build)
    if plat == "linux":
        BODY = {"resources": [{"id": policy,"settings": {"build": build,"variants": [{"build": build,"platform": "LinuxArm64"}]}}]}
    else:
        BODY = {"resources": [{"id": policy,"settings": {"build": build}}]}

    response = falcon.command("updateSensorUpdatePoliciesV2", body=BODY)
    print(response)

    for ver in ver_list:
        if build in ver["build"]:
            full_version = ver["sensor_version"]
    return full_version        

def patch_api(platform,version):
    payload = "{\""+platform+"\": \""+version+"\"}"
    print(payload)
    response = requests.patch("https://<Replace>.execute-api.us-east-1.amazonaws.com/default/API/sensor_versions/up", headers = {'auth': EDR_Update_Key,'Content-Type': 'text/plain'}, data=payload, timeout=5)
    print("Update in EDR API: ",response)

#####!!!!! Need to Send Slack Start alert 
def lambda_handler(event, context):
    today = (datetime.datetime.now()).strftime('%Y-%m-%d')
    dates = grab_dates()
    if today in dates:
        print("Congrats! It's time to run this puppy and update the Sensor Versions!!!")
        # Send Slack Start alert 
        body = "Hello Teams!\n This is a reminder that the scheduled change of the Standard Sensor Versions is about to occur in 5 minutes."
        output = requests.post('https://hooks.slack.com/services/<Replace_With_Your_Slack_Hook',headers = {"Content-Type": "application/json"},json = {"text": body}, timeout=5)
        print("Slack post status: "+output.text)
        print("Sleeping for 5 minutes")
        sleep(300)
        global falcon, EDR_Update_Key
        EDR_Update_Key = get_secret("EDR_API")
        clientid, clientsec = get_secret("Falcon_Key")
        falcon = APIHarness(client_id=clientid, client_secret=clientsec)

        ## Establish New Versions ##
        versions = json.loads(grab_versions())
        for i in platforms:
            policy = policies[i]
            version = versions[i]
            full_version = set_new_versions(policy,version,i)
            print(full_version)

            #Patch the API Data
            patch_api(i,full_version)

        ## Set Data For Wiki ##
        outdata = """<!DOCTYPE html>
<html>
<head>
<style>
table {{
  font-family: arial, sans-serif;
  border-collapse: collapse;
}}

td, th {{
  border: 1px solid #dddddd;
  text-align: left;
  padding: 8px;
}}

tr:nth-child(even) {{
  background-color: #dddddd;
}}
</style>
</head>
<body>

<table>
  <tr>
    <th>OS</th>
    <th>PRD</th>
    <th>DEV</th>
  </tr>
  <tr>
    <td>Linux</td>
    <td>{linux_prd}</td>
    <td>{linux_dev}</td>
  </tr>
  <tr>
    <td>MacOS</td>
    <td>{mac_prd}</td>
    <td>{mac_dev}</td>
  </tr>
  <tr>
    <td>Windows</td>
    <td>{windows_prd}</td>
    <td>{windows_dev}</td>
  </tr>
</table>
Last Updated: {today}
</body>
</html>
""".format(linux_prd=versions["linux_prd"], linux_dev=versions["linux_dev"], mac_prd=versions["mac_prd"], mac_dev=versions["mac_dev"], windows_prd=versions["windows_prd"], windows_dev=versions["windows_dev"], today=today)
        
        #Send output to S3 Bucket
        client = boto3.client('s3')
        response = client.put_object(
        Body=outdata.encode("utf-8"),
        Bucket='page-data',
        ContentEncoding='utf-8',
        ContentType='text/html',
        Key='version.html',
        )
        print(response)
        message = []
        message.append({"type": "section", "text": {"type": "mrkdwn","text": "The Sensor Version Change Script has completed running. Please verify no errors were posted to this channel and verify the following:\n\nThat Sensor Versions are correct on each policy\nThat the versions in the API Database are correct\nThat the current sensor versions Wiki page is updated"}})
        slack_alert(message)
    else:
        print("Not Today, old friend")