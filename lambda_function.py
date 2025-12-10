import json
import os
import boto3
from boto3.dynamodb.conditions import Key

TABLE_NAME = os.environ.get("EMP_TABLE_NAME", "Emp_Master")
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)


def lambda_handler(event, context):
    http_method = event.get("httpMethod")
    path = event.get("path")
    print(f"Received event: {json.dumps(event)}")

    if http_method == "POST" and "/employee" in path:
        body = event.get("body")
        if isinstance(body, str):
            body = json.loads(body)

        item = {
            "Emp_Id": body["Emp_Id"],
            "First_Name": body["First_Name"],
            "Last_Name": body["Last_Name"],
            "Date_Of_Joining": body["Date_Of_Joining"],
        }

        table.put_item(Item=item)
        print(f"Inserted item: {item}")

        return {
            "statusCode": 201,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(
                {"message": "Employee created", "item": item}
            ),
        }

    if http_method == "GET" and "/employee" in path:
        emp_id = event.get("queryStringParameters", {}).get("emp_id")
        if not emp_id:
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"message": "emp_id is required"}),
            }

        resp = table.get_item(Key={"Emp_Id": emp_id})
        item = resp.get("Item")
        print(f"Retrieved item: {item}")

        if not item:
            return {
                "statusCode": 404,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"message": "Employee not found"}),
            }

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(item),
        }

    # Fallback for unsupported routes
    return {
        "statusCode": 405,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"message": "Method Not Allowed"}),
    }
