import json
import os
import boto3

TABLE_NAME = os.environ.get("EMP_TABLE_NAME", "Emp_Master")
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)


def lambda_handler(event, context):
    # Log the full event for debugging
    print(f"Received event: {json.dumps(event)}")

    # ---- Normalize HTTP method, path, body, query params ----
    http_method = None
    path = ""
    body = event.get("body")
    query_params = {}

    # HTTP API v2 (version == "2.0")
    if event.get("version") == "2.0":
        http_info = event.get("requestContext", {}).get("http", {})
        http_method = http_info.get("method")
        path = event.get("rawPath", "")
        query_params = event.get("queryStringParameters") or {}

    # REST API (no version or version == "1.0")
    else:
        http_method = event.get("httpMethod")
        path = event.get("path", "")
        query_params = event.get("queryStringParameters") or {}

    # If body is a JSON string, parse it
    if isinstance(body, str) and body.strip():
        body = json.loads(body)
    elif body is None:
        body = {}

    print(f"Normalized method={http_method}, path={path}, query={query_params}")

    # -----------------------------------
    # POST /employee  -> create employee
    # -----------------------------------
    if http_method == "POST" and path.endswith("/employee"):
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
            "body": json.dumps({"message": "Employee created", "item": item}),
        }

    # -----------------------------------
    # GET /employee?emp_id=E001 -> fetch
    # -----------------------------------
    if http_method == "GET" and path.endswith("/employee"):
        emp_id = query_params.get("emp_id")
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
        "body": json.dumps({"message": "Method is not at all allowed"}),
    }

#dummy 1