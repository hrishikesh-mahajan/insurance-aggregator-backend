from flask import Flask, make_response, request
from flask_cors import CORS
from pymongo import MongoClient

app = Flask(__name__)
CORS(app)


@app.route("/submit-form", methods=["POST"])
def submit_form():
    form_data = request.form

    images = request.files.getlist("images")
    pdfs = request.files.getlist("pdfs")

    # Convert files to binary data
    image_blobs = [image.read() for image in images]
    pdf_blobs = [pdf.read() for pdf in pdfs]

    # Assuming you have a MongoDB collection called 'form_data'
    client = MongoClient("mongodb://localhost:27017/")
    db = client["insurance_aggregator"]
    collection = db["form_data"]

    # Insert form data and files into MongoDB
    form_data_dict = form_data.to_dict()
    form_data_dict["images"] = image_blobs  # type: ignore
    form_data_dict["pdfs"] = pdf_blobs  # type: ignore

    collection.insert_one(form_data_dict)

    return make_response("Form submitted successfully", 200)


if __name__ == "__main__":
    app.run()
