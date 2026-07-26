import json
import os

def lambda_handler(event, context):

    print(json.dumps(event))

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "Kiro Agent funcionando",
            "knowledge_table": os.getenv("KNOWLEDGE_TABLE"),
            "tickets_table": os.getenv("TICKETS_TABLE"),
            "incidents_table": os.getenv("INCIDENTS_TABLE")
        })
    }