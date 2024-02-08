import json
import boto3

def update_container_paths_db(event):
    dynamo_resource = boto3.resource("dynamodb")
    container_table = dynamo_resource.Table("Container_Paths")
    body=event["body"]
    print(body)
    data = json.loads(body)
    for key, value in data.items():
        path_update = dict(
            version = key,
            location = value)
        container_table.put_item(Item = path_update)
   
    message = []
    message.append({"Update Status": "Complete"},)
    data_body = json.dumps(message)
    code = 200
    return code,data_body
    
def container_paths_db(version):
    dynamo_resource = boto3.resource("dynamodb")
    container_table = dynamo_resource.Table("Container_Paths")
    print(version)
    message = []
    if version == "all":
        response = container_table.scan()
        data = {}
        for i in response["Items"]:
            out = {i["version"]: i["location"]}
            data.update(out)
        message.append(data)
    else: 
        response = container_table.get_item(Key={"version": version})["Item"]["location"]
        message.append({version: response},)
    print(response)
   
    data_body = json.dumps(message)
    code = 200
    return code,data_body
