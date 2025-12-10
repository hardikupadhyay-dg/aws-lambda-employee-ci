import json
import os

import boto3

dynamodb = boto3.resource("dynamodb")
TABLE_NAME = os.environ.get("TABLE_NAME", "Emp_Master")
table = dynamodb.Table(TABLE_NAME)


def build_response(status_code: int, body_dict: dict) -> dict:
    """Build a standard API Gateway-compatible HTTP response."""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
        },
        "body": json.dumps(body_dict),
    }


def handle_post(event: dict) -> dict:
    """Handle POST /employee - inserts a new employee record."""
    body = event.get("body")

    if isinstance(body, str):
        body = json.loads(body or "{}")

    required_fields = ["Emp_Id", "First_Name", "Last_Name", "Date_Of_Joining"]
    missing = [field for field in required_fields if field not in body]

    if missing:
        return build_response(
            400,
            {"error": f"Missing fields: {', '.join(missing)}"},
        )

    item = {
        "Emp_Id": body["Emp_Id"],
        "First_Name": body["First_Name"],
        "Last_Name": body["Last_Name"],
        "Date_Of_Joining": body["Date_Of_Joining"],
    }

    table.put_item(Item=item)
    print(f"Inserted item: {item}")

    return build_response(
        201,
        {"message": "Employee created", "item": item},
    )


def handle_get(event: dict) -> dict:
    """Handle GET /employee?emp_id=<id> - retrieves a record."""
    query_params = event.get("queryStringParameters") or {}
    emp_id = query_params.get("emp_id")

    if not emp_id:
        return build_response(
            400,
            {"error": "emp_id query parameter is required"},
        )

    response = table.get_item(Key={"Emp_Id": emp_id})
    item = response.get("Item")

    print(f"Fetched item for Emp_Id={emp_id}: {item}")

    if not item:
        return build_response(
            404,
            {"error": "Employee not found"},
        )

    return build_response(200, {"item": item})


def lambda_handler(event, context):
    """
    Main Lambda handler.

    Supports:
    - HTTP API v2 events
    - REST API proxy events
    - Simple local testing by passing a 'method' field in the event.
    """
    method = None

    # HTTP API v2
    if "requestContext" in event and "http" in event["requestContext"]:
        method = event["requestContext"]["http"]["method"]
    # REST API
    elif "httpMethod" in event:
        method = event["httpMethod"]
    # Local test
    else:
        method = event.get("method", "GET")

    if method == "POST":
        return handle_post(event)
    if method == "GET":
        return handle_get(event)

    return build_response(
        405,
        {"error": f"Method {method} not allowed"},
    )
