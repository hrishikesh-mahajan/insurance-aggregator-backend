import os

from dotenv import load_dotenv
from flask import Flask, make_response, request
from flask_cors import CORS
from pymongo import MongoClient

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
        document.pop("_id", None)
        document.pop("receiptImage", None)
        document.pop("claimDocuments", None)
        document.pop("beforeIncidentImages", None)
        document.pop("afterIncidentImages", None)
        print(document)
        claims.append(document)

    return make_response({"claims": claims}, 200)


if __name__ == "__main__":
    app.run(port=5000, debug=True)
    app.run(port=5000, debug=True)
