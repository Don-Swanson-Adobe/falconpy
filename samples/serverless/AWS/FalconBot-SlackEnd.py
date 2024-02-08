import base64
import json
import hmac
import hashlib
import boto3
from botocore.exceptions import ClientError
from urllib.parse import parse_qs

def get_secret():
    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(service_name='secretsmanager', region_name="us-east-1")

    try:
        get_secret_value_response = client.get_secret_value(SecretId="FalconBot")
    except ClientError as e:
        raise e

    # Decrypts secret using the associated KMS key.
    secrets = json.loads(get_secret_value_response['SecretString'])
    signing_secret= secrets['signing_secret']
    return signing_secret

def lambda_handler(event, context):
    
    #Check if authorized Channel
    if not verify_request(event):
        return{
            'statusCode': 200,
            'body': json.dumps("Unauthorized, Please run from the channel specified in the documentation")
        }

    
    #Setup SNS and Decode payload
    sns = boto3.client('sns')
    event_headers = event['headers']
    event = base64.b64decode(event["body"])
    event = parse_qs(event.decode("utf-8"))

    #Extract payload data to variables
    text = json.dumps(event["text"]).replace('"]','').replace('["','').split(" ")
    response_url = json.dumps(event["response_url"]).replace('["','').replace('"]','')
    user = json.dumps(event["user_id"]).replace('["','').replace('"]','')
    channel = json.dumps(event["channel_name"]).replace('["','').replace('"]','')
    command = json.dumps(event["command"]).replace('["/','').replace('"]','')
    print("Command: " + str(command))
    ccid = text[0]
    aid = text[1]
    cid = ccid[0:32]


    send = str(user)+"_"+str(response_url)+"_"+str(cid)+"_"+str(aid)+"_"+str(channel)+"_"+str(command)
    forward = sns.publish(
        TopicArn='arn:aws:sns:us-east-1:<REPLACEWITH SNS ARN>',
        Message=send
    )
    print("SNS Response")
    print(forward)
    
    #Return notice to user
    return {
        'statusCode': 200,
        'body': 'One moment while we gather your results, If you do not receive a response in 30 seconds, please verify your CID & AID and try again....'  
    }
    
def verify_request(event):

    # Security check, make sure that the request came from an authorized channel
    event_headers = event['headers']
    print(event_headers)
    event = base64.b64decode(event["body"])
    event = parse_qs(event.decode("utf-8"))
    print('Slash command called with params: ', event)
    channel_name = json.dumps(event["channel_name"]).replace('["','').replace('"]','')
    channel_id = json.dumps(event["channel_id"]).replace('["','').replace('"]','')
    print('Channel Name')
    print(str(channel_name))
    if str(channel_name) == 'falconbot':
        return True
    else:
        print("UNAUTHORZED CHANNEL")
        return False

# Additional Security Checking to validate the request came from Slack. 
# This is commented out as it can cause unexpectd results and may need to be customized for your environment to work properly.
#    timestamp = json.dumps(event_headers["X-Slack-Request-Timestamp"]).replace('["','').replace('"]','')
#    signing_secret = get_secret()
#    print(timestamp)
#    concat_message = ('v0:' + timestamp + ':' + body).encode()
#    slack_signature = event['headers']['X-Slack-Signature']
#    key = signing_secret.encode()
#    hashed_msg = 'v0=' + \
#        hmac.new(key, concat_message, hashlib.sha256).hexdigest()
#    return hashed_msg == slack_signature