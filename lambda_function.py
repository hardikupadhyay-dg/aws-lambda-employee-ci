import json
import os
import base64

import boto3

DYNAMODB_TABLE_NAME = "Emp_Master"
AWS_REGION = os.environ.get("AWS_REGION", "ap-south-1")

dynamodb_resource = boto3.resource("dynamodb", region_name=AWS_REGION)
table = dynamodb_resource.Table(DYNAMODB_TABLE_NAME)


def _parse_body(event):
    """Parse JSON body from API Gateway proxy event, handling base64 if needed."""
    body = event.get("body", "")
    if not body:
        return {}

    if event.get("isBase64Encoded"):
        body = base64.b64decode(body).decode("utf-8")

    try:
        return json.loads(body)
    except json.JSONDecodeError:
        return {}


def _response(status_code, body_dict):
    """Helper to build API Gateway-compatible response."""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps(body_dict),
    }


def handle_post_employee(event):
    """
    Handle POST /employee - insert an employee into Emp_Master.

    Expected JSON:
    {
        "Emp_Id": "E001",
        "First_Name": "Alice",
        "Last_Name": "Brown",
        "Date_Of_Joining": "2024-07-01"
    }
    """
    data = _parse_body(event)

    required_fields = [
        "Emp_Id",
        "First_Name",
        "Last_Name",
        "Date_Of_Joining",
    ]

    missing = [field for field in required_fields if field not in data]
    if missing:
        return _response(
            400,
            {"error": f"Missing required fields: {', '.join(missing)}"},
        )

    item = {
        "Emp_Id": str(data["Emp_Id"]),
        "First_Name": str(data["First_Name"]),
        "Last_Name": str(data["Last_Name"]),
        "Date_Of_Joining": str(data["Date_Of_Joining"]),
    }

    print(f"Inserting item into DynamoDB: {item}")

    table.put_item(Item=item)

    # Return 201 Created per requirement
    return _response(201, {"message": "Employee created", "employee": item})


def handle_get_employee(event):
    """
    Handle GET /employee?emp_id=<id> - retrieve employee by Emp_Id.
    """
    query_params = event.get("queryStringParameters") or {}
    emp_id = query_params.get("emp_id")

    if not emp_id:
        return _response(
            400,
            {"error": "Query parameter 'emp_id' is required."},
        )

    print(f"Retrieving employee with Emp_Id={emp_id}")

    result = table.get_item(Key={"Emp_Id": emp_id})
    item = result.get("Item")

    print(f"DynamoDB get_item result: {result}")

    if not item:
        return _response(404, {"error": "Employee not found"})

    return _response(200, {"employee": item})


def lambda_handler(event, context):
    """
    Main Lambda handler compatible with API Gateway (HTTP API / REST proxy).
    Also suitable for local testing by calling directly.
    """
    print("Lambda handler invoked")
    print("Received event:")
    print(json.dumps(event))

    http_method = event.get("requestContext", {}).get("http", {}).get("method") \
        or event.get("httpMethod", "")
    raw_path = event.get("requestContext", {}).get("http", {}).get("path") \
        or event.get("path", "")

    # We expect /employee path
    if raw_path.endswith("/employee"):
        if http_method == "POST":
            return handle_post_employee(event)
        if http_method == "GET":
            return handle_get_employee(event)

    return _response(
        400,
        {
            "error": "Unsupported route or method",
            "httpMethod": http_method,
            "path": raw_path,
        },
    )


if __name__ == "__main__":
    # Simple local tests
    test_event_post = {
        "httpMethod": "POST",
        "path": "/employee",
        "isBase64Encoded": False,
        "body": json.dumps(
            {
                "Emp_Id": "E001",
                "First_Name": "Alice",
                "Last_Name": "Brown",
                "Date_Of_Joining": "2024-07-01",
            }
        ),
    }
    print("Local POST test response:")
    print(lambda_handler(test_event_post, None))

    test_event_get = {
        "httpMethod": "GET",
        "path": "/employee",
        "isBase64Encoded": False,
        "queryStringParameters": {"emp_id": "E001"},
    }
    print("Local GET test response:")
    print(lambda_handler(test_event_get, None))

