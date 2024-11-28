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
    form_data = request.form.to_dict()
    files = request.files

    # Combine form data and files into a single dictionary
    data_to_insert = form_data.copy()

    for key in files:
        uploaded_files = request.files.getlist(key)
        # Store files as binary data (blobs)
        data_to_insert[key] = [file.read() for file in uploaded_files]  # type: ignore

    # Insert into MongoDB
    client = MongoClient(os.getenv("MONGO_URI"))
    db = client[os.getenv("MONGO_DB_NAME")]
    collection = db[os.getenv("MONGO_COLLECTION_NAME")]
    collection.insert_one(data_to_insert)

    return make_response("Form submitted successfully", 200)


if __name__ == "__main__":
    app.run(port=5000, debug=True)
