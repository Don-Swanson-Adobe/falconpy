import json
import boto3

def update_sensor_versions_db(event):
    dynamo_resource = boto3.resource("dynamodb")
    sensor_versions_table = dynamo_resource.Table("Sensor_Versions")
    body=event["body"]
    print(body)
    data = json.loads(body)
    for key, value in data.items():
        version_update = dict(
            os_landscape = key,
            version = value)
        sensor_versions_table.put_item(Item = version_update)
   
    message = []
    message.append({"Update Status": "Complete"},)
    data_body = json.dumps(message)
    code = 200
    return code,data_body
    
def sensor_versions_db(version):
    dynamo_resource = boto3.resource("dynamodb")
    sensor_versions_table = dynamo_resource.Table("Sensor_Versions")
    print(version)
    message = []
    if version == "all":
        response = sensor_versions_table.scan()
        data = {}
        for i in response["Items"]:
            out = {i["os_landscape"]: str(i["version"])}
            data.update(out)
        message.append(data)
    else: 
        response = sensor_versions_table.get_item(Key={"os_landscape": version})["Item"]["version"]
        message.append({version: response},)
    print(response)
   
    data_body = json.dumps(message)
    code = 200
    return code,data_body

