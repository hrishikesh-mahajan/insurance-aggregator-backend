import json
import os

from pymongo import MongoClient

from utils.image_exif_parser import extract_exif_data
from utils.indian_disaster_verification import IndianDisasterVerificationService
from utils.plant_identification_module import PlantIdentificationService
from utils.reverse_location_lookup import get_google_maps_link, get_location_name


def process_claim(claim_id: str):
    client = MongoClient(os.getenv("MONGO_DB_URI"))
    db = client[os.getenv("MONGO_DB_NAME", "")]
    collection = db[os.getenv("MONGO_DB_COLLECTION", "")]
    claim_data = collection.find_one({"claimNumber": claim_id})

    if not claim_data:
        return "Claim not found", 404

    # Extract image path from claim data
    image_blob = claim_data.get("receiptImage")
    if not image_blob:
        return "Image not found in the claim data", 400

    image_path = ".\\inputs\\" + f"temp_image_{claim_id}.jpg"
    with open(image_path, "wb") as f:
        f.write(image_blob)

    # Extract GPS info and timestamp from the image
    gps_info, timestamp = extract_exif_data(image_path)
    print(f"GPS Info: {gps_info}")
    print(f"Timestamp: {timestamp}")
    if gps_info:
        lat, lon = gps_info

        # Get location name and Google Maps link
        location_name = get_location_name(lat, lon, complete=True)
        print(f"Location: {location_name}")
        print(f"Google Maps link: {get_google_maps_link(lat, lon)}")

        # Verify if the location is affected by any disaster
        indian_disaster_verification_service = IndianDisasterVerificationService()
        verification_result = (
            indian_disaster_verification_service.verify_location_disaster(
                lat, lon, timestamp
            )
        )
        insurance_report = (
            indian_disaster_verification_service.generate_insurance_report(
                verification_result
            )
        )
        print(f"Disaster Info: {json.dumps(verification_result, indent = 2)}")
        print(f"Insurance Info: {json.dumps(insurance_report, indent = 2)}")
        with open("disaster_verification.json", "w") as f:
            json.dump(verification_result, f, indent=2)

        with open("insurance_report.json", "w") as f:
            json.dump(insurance_report, f, indent=2)

        # Verify crop plantation
        plant_service = PlantIdentificationService()
        crop_result = plant_service.identify_crop(image_path)
        print(f"Crop Identification: {crop_result}")
        verification_result = plant_service.verify_crop_match(
            image_path, expected_crop="Grapes"
        )
        print(f"Verification Result: {verification_result}")
        with open("crop_result.md", "w") as f:
            f.write(crop_result.get("raw_response", {}).text)

    else:
        print("No GPS info found in the image.")
    return "Claim processed successfully", 200
