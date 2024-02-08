#This Lambda function will query the Falcon API for the list of supported kernels and output them to an HTML file in an S3 bucket
#Please see the attached PDF for how to setup Secrets Manager and the IAM role for these Lambda function
#The attached PDF Also includes instructions on how to setup and add an AWS Layer to this Lambda function to use FalconPy
#Required Layers for this Function: FalconPy, natsort
#Developed by Don-Swanson-Adobe

import json
from falconpy import APIHarness
import requests
import boto3
from botocore.exceptions import ClientError
from datetime import datetime
from natsort import natsorted

slackhook = "https://hooks.slack.com/services/<Replace_With_Your_Slack_Hook>"
ignored_distros = ["clevos", "flatcar"]
dist_dict = {"amzn1": "Amazon 1", "amzn2": "Amazon 2", "debian9": "Debian 9", "debian10": "Debian 10", "debian11": "Debian 11", "elrepo7": "ELRepo 7", "elrepo8": "ELRepo 8", "oracle6": "Oracle 6", "oracle7": "Oracle 7", "oracle8": "Oracle 8", "oracle9": "Oracle 9", "rhel6": "RHEL/CentOS 6", "rhel7": "RHEL/CentOS 7", "rhel8": "RHEL/CentOS/Alma/Rocky 8", "rhel9": "RHEL/CentOS/Alma/Rocky 9", "suse11": "SUSE 11", "suse12": "SUSE 12", "suse15": "SUSE 15", "ubuntu14": "Ubuntu 14", "ubuntu16": "Ubuntu 16", "ubuntu18": "Ubuntu 18", "ubuntu20": "Ubuntu 20", "ubuntu22": "Ubuntu 22"}

def get_secret():
    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(service_name='secretsmanager', region_name="us-east-1")

    try:
        get_secret_value_response = client.get_secret_value(SecretId="Falcon_Key")
    except ClientError as e:
        raise e

    # Decrypts secret using the associated KMS key.
    secrets = json.loads(get_secret_value_response['SecretString'])
    clientid = secrets['clientid']
    clientsec = secrets['clientsec']
    return clientid, clientsec

def get_version(id):
    headersList = {"Accept": "*/*","auth": "YOUR_AUTH_KEY","version": id}
    response = requests.get("https://<REPLACE>.execute-api.us-east-1.amazonaws.com/default/API/sensor_versions", headers=headersList, timeout=5)
    version = json.loads(response.text)[0][id]
    return version

def lambda_handler(event, context):
    update_time = datetime.now().isoformat(timespec='minutes')
    
    #Login to the API
    clientid, clientsec = get_secret()
    global falcon
    falcon = APIHarness(client_id=clientid, client_secret=clientsec)

    #Get Current Prd Version
    prd_version = get_version('linux_prd')

    #Get Current DEV Version
    dev_version = get_version('linux_dev')

    outdata = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <link rel="stylesheet" href="style.css">
  </head>
<style>
table, th, td {
border:1px solid black;
}
</style>
<body>
    Last Updated:
    """
    outdata += update_time
    outdata += "UTC"
    #Get List of distros
    output = falcon.command("querySensorUpdateKernelsDistinct",distinct_field="distro")
    distros = output["body"]["resources"]

    for d in distros:
        print(d)
        if d in ignored_distros:
            pass
        elif d in dist_dict:
            dist = dist_dict[d]
            outdata += '<div class="header"><a href="#'+d+'collapse" class="hide" id="'+d+'collapse">'+dist+'</a><a href="#'+d+'expand" class="show" id="'+d+'expand">'+dist+'</a><div class="results"><p>'"""
<table class="wrapped">
<colgroup>
    <col/>
    <col/>
</colgroup>
<tbody>
    <tr>
    <th>Distro Version</th>
    <th>Kernel</th>
    <th>Kernel Version</th>
    <th>Supported?</th>
    </tr>
        """
            off = 0
            kernels = []
            output = falcon.command("queryCombinedSensorUpdateKernels",filter="distro:'"+d+"'",offset=off,limit=1)
            total = output["body"]["meta"]["pagination"]["total"]
            while total > 0:
                output = falcon.command("queryCombinedSensorUpdateKernels",filter="distro:'"+d+"'",offset=off,limit=500)
                results = output["body"]["resources"]
                for i in results:
                    temp_dict = {}
                    if i["base_package_supported_sensor_versions"]:
                        basepackage = i["base_package_supported_sensor_versions"][0]
                    else:
                        basepackage = "999999999999999999999999999999999999999999"
                    if i["ztl_supported_sensor_versions"]:
                        ztl = i["ztl_supported_sensor_versions"][0]
                    else:
                        ztl = "999999999999999999999999999999999999999999"
                    if i["ztl_module_supported_sensor_versions"]:
                        ztl_module = i["ztl_module_supported_sensor_versions"][0]
                    else:
                        ztl_module = "999999999999999999999999999999999999999999"
                    if basepackage > dev_version and ztl > dev_version and ztl_module > dev_version:
                        pass
                    elif basepackage <= prd_version:
                        temp_dict['version'] = i['distro_version']+"_"+i['architecture']
                        temp_dict['kernel'] = i['release']
                        temp_dict['support'] = "Yes - Native Support"
                        temp_dict['ver'] = i['version']

                    elif basepackage > prd_version and basepackage <= dev_version and ztl > basepackage and ztl_module > basepackage:
                        temp_dict['version'] = i['distro_version']+"_"+i['architecture']
                        temp_dict['kernel'] = i['release']
                        temp_dict['support'] = "DEV Hosts ONLY - Native"
                        temp_dict['ver'] = i['version']

                    elif ztl <= prd_version:
                        temp_dict['version'] = i['distro_version']+"_"+i['architecture']
                        temp_dict['kernel'] = i['release']
                        temp_dict['support'] = "Yes - Via ZTL"
                        temp_dict['ver'] = i['version']

                    elif ztl_module <= prd_version:
                        temp_dict['version'] = i['distro_version']+"_"+i['architecture']
                        temp_dict['kernel'] = i['release']
                        temp_dict['support'] = "Yes - Via ZTLv2"
                        temp_dict['ver'] = i['version']

                    elif ztl > prd_version and ztl <= dev_version:
                        temp_dict['version'] = i['distro_version']+"_"+i['architecture']
                        temp_dict['kernel'] = i['release']
                        temp_dict['support'] = "DEV Hosts ONLY - Via ZTL"
                        temp_dict['ver'] = i['version']

                    elif ztl_module > prd_version and ztl_module <= dev_version:
                        temp_dict['version'] = i['distro_version']+"_"+i['architecture']
                        temp_dict['kernel'] = i['release']
                        temp_dict['support'] = "DEV Hosts ONLY - Via ZTLv2"
                        temp_dict['ver'] = i['version']

                    else:
                        pass

                    if temp_dict:
                        kernels.append(temp_dict)

                total -= 500
                off += 500

            sorted_kernels = natsorted(kernels, key=lambda x: x['kernel'],reverse=True)
            for i in sorted_kernels:
                outdata += "<tr><td>"+str(i['version'])+"</td><td>"+str(i['kernel'])+"</td><td>"+str(i['ver'])+"</td><td>"+str(i['support'])+"</td></tr>\n"
            outdata +="</tbody></table></p></div></div>"
              
        else:
            body = ":warning: Hey Team,\n there's a new distro you haven't accounted for yet\n"+d
            output = requests.post(slackhook, headers = {"Content-Type": "application/json"}, json = {"text": body}, timeout=5)

    outdata +="</body></html>"

    #Send output to S3 Bucket
    client = boto3.client('s3')
    response = client.put_object(
    Body=outdata.encode("utf-8"),
    Bucket='kernel_listings',
    ContentEncoding='utf-8',
    ContentType='text/html',
    Key='kernel.html',
    )
    print(response)

    #Send completion Message to Slack
    output = requests.post(slackhook, 
        headers = {"Content-Type": "application/json"},
        json = {"text": "The Linux Supported Kernels Page has been updated"},
        timeout=5)
    print("Slack post status: "+output.text)
