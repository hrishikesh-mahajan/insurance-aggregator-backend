import os

from dotenv import load_dotenv
from flask import Flask, jsonify, make_response, request
from flask_cors import CORS
from pymongo import MongoClient

from process_claim import process_claim

app = Flask(__name__)
CORS(app)

load_dotenv()


@app.route("/submit-form", methods=["POST"])
def submit_form():
    import uuid
    from datetime import datetime

    form_data = request.form.to_dict()
    files = request.files

    # Combine form data and files into a single dictionary
    data_to_insert = form_data.copy()

    # Handle single file fields
    single_file_fields = ["receiptImage", "claimDocuments"]

    for field in single_file_fields:
        if field in files:
            file = files[field]
            data_to_insert[field] = file.read()

    # Handle multiple file fields
    multiple_file_fields = ["beforeIncidentImages", "afterIncidentImages"]

    for field in multiple_file_fields:
        uploaded_files = request.files.getlist(field)
        if uploaded_files:
            data_to_insert[field] = [file.read() for file in uploaded_files]  # type: ignore

    # Add additional fields like claimNumber, createdAt, updatedAt
    data_to_insert["claimNumber"] = "CLAIM-" + str(uuid.uuid4())[:8]
    data_to_insert["createdAt"] = datetime.now().isoformat()
    data_to_insert["updatedAt"] = datetime.now().isoformat()

    print(data_to_insert)
    # Insert into MongoDB
    client = MongoClient(os.getenv("MONGO_DB_URI"))
    db = client[os.getenv("MONGO_DB_NAME", "")]
    collection = db[os.getenv("MONGO_DB_COLLECTION", "")]
    collection.insert_one(data_to_insert)
    for document in collection.find({}):
        document.pop("receiptImage", "")
        print(document)
    print(f"Database URI: {os.getenv('MONGO_DB_URI')}")
    print(f"Database Name: {os.getenv('MONGO_DB_NAME', '')}")
    print(f"Collection Name: {os.getenv('MONGO_DB_COLLECTION', '')}")

    return make_response("Form submitted successfully", 200)


@app.route("/get-claims", methods=["GET"])
def get_claims():
    client = MongoClient(os.getenv("MONGO_DB_URI"))
    db = client[os.getenv("MONGO_DB_NAME", "")]
    collection = db[os.getenv("MONGO_DB_COLLECTION", "")]

    claims = []
    for document in collection.find({}):
        document["_id"] = str(document["_id"])  # Convert ObjectId to string
        claim_number = document.get("claimNumber", "")
        # Generate URLs for file fields
        for field in [
            "receiptImage",
            "claimDocuments",
            "beforeIncidentImages",
            "afterIncidentImages",
        ]:
            server = r"http://localhost:5000"
            if field in document:
                if isinstance(document[field], list):
                    # For multiple files
                    document[field] = [
                        f"{server}/get-file/{claim_number}/{field}/{i}"
                        for i in range(len(document[field]))
                    ]
                else:
                    # For single file
                    document[field] = f"{server}/get-file/{claim_number}/{field}"
        claims.append(document)

    return jsonify(claims), 200


@app.route("/get-file/<string:claimNumber>/<string:fieldName>", methods=["GET"])
@app.route(
    "/get-file/<string:claimNumber>/<string:fieldName>/<int:index>", methods=["GET"]
)
def get_file(claimNumber, fieldName, index=None):
    client = MongoClient(os.getenv("MONGO_DB_URI"))
    db = client[os.getenv("MONGO_DB_NAME", "")]
    collection = db[os.getenv("MONGO_DB_COLLECTION", "")]

    document = collection.find_one({"claimNumber": claimNumber})
    if not document or fieldName not in document:
        return make_response("File not found", 404)

    file_data = document[fieldName]
    if isinstance(file_data, list):
        if index is not None and 0 <= index < len(file_data):
            file_data = file_data[index]
        else:
            return make_response("File index out of range", 404)

    response = make_response(file_data)
    # Set appropriate content type based on fieldName or file content
    response.headers.set("Content-Type", "application/octet-stream")
    return response


@app.route("/process-claim/<string:claimid>", methods=["POST"])
def process_claim_by_id(claimid: str):

    if request.json is None:
        return make_response("Request body must be a JSON object", 400)
    claim_id = request.json.get("claimNumber", "") or claimid
    result, status_code = process_claim(claim_id)

    return jsonify(result), status_code


if __name__ == "__main__":
    app.run(port=5000, debug=True)
