import boto3
import json
import uuid
import requests
import os
from datetime import datetime

# Initialize AWS resources
dynamodb = boto3.resource('dynamodb')
sqs = boto3.client('sqs')

# Constants
RECAPTCHA_SECRET_KEY = os.environ['RECAPTCHA_SECRET_KEY']  # Replace with 
your key
DYNAMO_TABLE_NAME = os.environ['DYNAMO_TABLE_NAME']  # Replace with 
your table 
name
REGION = os.environ['AWS_REGION']
AWS_ACCOUNT_ID = os.environ['AWS_ACCOUNT_ID']
SQS_QUEUE_NAME = os.environ['SQS_QUEUE_NAME']

SQS_QUEUE_URL = 
"https://sqs.{region}.amazonaws.com/{account}/{queue}".format(region=REGION, account=AWS_ACCOUNT_ID, queue=SQS_QUEUE_NAME)  # 
Replace with your SQS URL

def lambda_handler(event, context):
    try:
        # Parse the input
        body = json.loads(event.get('body', '{}'))
        phone_number = body.get('phoneNumber')
        email = body.get('email')
        recaptcha_token = body.get('recaptchaToken')

        # Validate input
        if not phone_number or not email or not recaptcha_token:
            return {
                "statusCode": 400,
                "body": json.dumps({"message": "Missing required fields"})
            }

        # Step 1: Verify reCAPTCHA
        recaptcha_response = requests.post(
            "https://www.google.com/recaptcha/api/siteverify",
            data={
                "secret": RECAPTCHA_SECRET_KEY,
                "response": recaptcha_token,
            }
        )
        recaptcha_result = recaptcha_response.json()

        if not recaptcha_result.get('success'):
            return {
                "statusCode": 400,
                "body": json.dumps({"message": "Invalid reCAPTCHA token"})
            }

        # Step 2: Store in DynamoDB
        table = dynamodb.Table(DYNAMO_TABLE_NAME)
        timestamp = datetime.utcnow().isoformat()
        item = {
            "id": str(uuid.uuid4()),
            "phoneNumber": phone_number,
            "email": email,
            "timestamp": timestamp,
        }

        table.put_item(Item=item)

        # Step 3: Send message to SQS
        message_body = f"Real Estate Lead:\nPhone: {phone_number}\nEmail: 
{email}"
        sqs.send_message(
            QueueUrl=SQS_QUEUE_URL,
            MessageBody=message_body
        )

        # Return success response
        return {
            "statusCode": 200,
            "body": json.dumps({"message": "Form submitted successfully"})
        }

    except Exception as e:
        print(f"Error processing request: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({"message": "Internal Server Error", 
"error": str(e)})
        }

