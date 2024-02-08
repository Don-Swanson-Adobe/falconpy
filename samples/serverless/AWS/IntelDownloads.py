#!/usr/bin/env python3
#This automation is used to download the daily intel report from the Falcon Console and send it to a distribution list via email and Slack
#Please see the attached PDF for how to setup Secrets Manager and the IAM role for these Lambda function
#The attached PDF Also includes instructions on how to setup and add an AWS Layer to this Lambda function to use FalconPy
#Required Layers for this Function: FalconPy

from falconpy import APIHarness
import requests
import boto3
import smtplib
from botocore.exceptions import ClientError
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import json

relayhost = "smtp.office365.com"
port = 587
dest_em = "<DESTINATION EMAIL>"
slackhook = "https://hooks.slack.com/services/<REPLACE WITH YOUR SLACK HOOK URL>" 
pdf_path = "/tmp/CS_Daily_Intel_Report.pdf"  # nosec
em_message = "This is an automated email sent from an unmonitored inbox. \nFor issues with this automation, please reach out to the Operations Team"

# Function to grab secrets
def get_secret(secid):
    session = boto3.session.Session()
    client = session.client(service_name='secretsmanager', region_name="us-east-1")
    try:
        get_secret_value_response = client.get_secret_value(SecretId=secid)
    except ClientError as e:
        raise e

    # Decrypts secret using the associated KMS key.
    secrets = json.loads(get_secret_value_response['SecretString'])
    if secid == "CSIntel_key":
        sec1 = secrets['clientid']
        sec2 = secrets['clientsec']
        return sec1, sec2
    elif secid == "Email_Login":
        sec1 = secrets['email_username']
        sec2 = secrets['email_password']
        return sec1, sec2
    else:
        sec1 = secrets['slack_token']
        return sec1

def upload_to_slack(slack_token, subject):
    title = subject
    payload={'title': subject, 'initial_comment': title, "filename":"CS_Daily_Intel_Report.pdf", "filetype": "pdf", "channels": "<REPLACE ME>"}
    headers = {"authorization": f"Bearer {slack_token}",}
    with open(pdf_path, "rb") as f:
        files = {"file": f}
        output = requests.post('https://slack.com/api/files.upload', data=payload, headers=headers, files=files, timeout=5)
    print(output.text)

def alert_don(message):
    requests.post(slackhook, headers = {"Content-Type": "application/json"}, json = {"text": message}, timeout=5)
    print("Slack Message Sent:",message)

def send_email_pdf(subject, dest_em, email_un, email_pw, desc):
    server = smtplib.SMTP(relayhost, port)
    server.starttls()
    server.login(email_un, email_pw)
    # Craft message (obj)
    msg = MIMEMultipart('alternative')

    message = f'{em_message}\n\n{subject}\n{desc}...\nPlease see the attachement for the full report\n\nYou can also find the new intel content at https://falcon.us-2.crowdstrike.com/intelligence/reports/subscriptions.\n\nYou are recieving this email because you are subscribed to the Daily Intel Distro Group'
    html = '''\
<!DOCTYPE html>
<html>
    <body>
        <div>
        <p><h5>This is an automated email sent from an unmonitored inbox. </br>For issues with this automation, please reach out to the Operations Team</h5></p>
        </br></br>
        <img width="360" alt="CrowdStrike Logo" border="0" style="display:block; border:none; outline:none;" src="https://www.crowdstrike.com/wp-content/img/cs_logo_email_header.png" />
        </div>
        <div class=3D"cs-message-body" style=3D"margin: 20px auto; max-width: 800px; padding: 0 20px;">
        <h1>CROWDSTRIKE INTEL NOTIFICATION</h1>
        </div>
        <div style="background-color:#eee;padding:10px 20px;">
            <h3 style="font-family:Georgia, 'Times New Roman', Times, serif;color#454349;">{subject}</h3>
        </div>
        <hr class="double">
            <div">
                <div>
                    <p>{desc}...
                    </br><b>Please see the attached PDF for the full report.</b>.
                    </br></br></br>You can also find additional new intel content at: <a href="https://falcon.us-2.crowdstrike.com/intelligence/reports/subscriptions">https://falcon.us-2.crowdstrike.com/intelligence/reports/subscriptions</a>.
                    </br></br><hr class="double"><h6>You are recieving this email because you are subscribed to the Daily Intel Distro Group</h6>
                    
                    </br>
                    </p>
                </div>
            </div>
        </div>
    </body>
</html>
'''.format(vars="variables", subject=subject, desc=desc)
    msg['Subject'] = subject
    msg['From'] = "Operations Team <opsteam@company.com>"
    msg['To'] = dest_em
    # Insert the text to the msg going by e-mail
    msg.attach(MIMEText(message, "plain"))
    msg.attach(MIMEText(html, "html"))
    
    # Attach the pdf to the msg going by e-mail
    with open(pdf_path, "rb") as f:
        attach = MIMEApplication(f.read(),_subtype="pdf")
    attach.add_header('Content-Disposition','attachment',filename="CS_Daily_Intel_Report.pdf")
    msg.attach(attach)
    # send msg
    server.send_message(msg)

def lambda_handler(event, context):
    clientid, clientsec = get_secret("CSIntel_key")
    email_un, email_pw = get_secret("Email_Login")
    slack_token = get_secret("Slack_Token")
    falcon = APIHarness(client_id=clientid, client_secret=clientsec)
    reportid = falcon.command("QueryIntelReportEntities", sort="created_date|desc", filter="type.slug:'periodic-report'+sub_type.slug:'daily'", limit=1)
    print("Report ID:",reportid)
    r_id = reportid["body"]["resources"][0]["id"]
    response = falcon.command("GetIntelReportPDF", id=r_id)
    open(pdf_path, 'wb').write(response)
    subject = reportid["body"]["resources"][0]["name"]
    desc = reportid["body"]["resources"][0]["short_description"]

    print("Report written to temp")
    send_email_pdf(subject, dest_em, email_un, email_pw, desc)
    upload_to_slack(slack_token, subject)

    message = "The Daily Intel Email has been sent. :lambda_lambda_lambda:"
    alert_don(message)
    print("\n**********************")
    print("****Email Complete!***")
    print("**********************")