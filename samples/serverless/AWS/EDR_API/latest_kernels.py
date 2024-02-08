import json
import boto3

def update_kernel_list_db(event):
    dynamo_resource = boto3.resource("dynamodb")
    kernel_list_table = dynamo_resource.Table("Latest_Kernel")
    body=event["body"]
    print(body)
    data = json.loads(body)
    for key, value in data.items():
        kernel_update = dict(
            distro_type = key,
            kernel = value)
        kernel_list_table.put_item(Item = kernel_update)
   
    message = []
    message.append({"Update Status": "Complete"},)
    data_body = json.dumps(message)
    code = 200
    return code,data_body
    
def kernel_list_db(distro_type):
    dynamo_resource = boto3.resource("dynamodb")
    kernel_list_table = dynamo_resource.Table("Latest_Kernel")
    print(distro_type)
    message = []
    if distro_type == "all":
        response = kernel_list_table.scan()
        data = {}
        for i in response["Items"]:
            out = {i["distro_type"]: str(i["kernel"])}
            data.update(out)
        message.append(data)
    else: 
        response = kernel_list_table.get_item(Key={"distro_type": distro_type})["Item"]["kernel"]
        message.append({distro_type: response},)
    print(response)
   
    data_body = json.dumps(message)
    code = 200
    return code,data_body