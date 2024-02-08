import json
import boto3
   
def sensor_change_dates_db(version):
    dynamo_resource = boto3.resource("dynamodb")
    sensor_dates_table = dynamo_resource.Table("Sensor_Change_Dates")
    print(version)
    message = []
    if version == "all":
        response = sensor_dates_table.scan()
        for i in response["Items"]:
            out = i["dates"]
            message.append(out)
   
    data_body = json.dumps(message)
    code = 200
    return code,data_body