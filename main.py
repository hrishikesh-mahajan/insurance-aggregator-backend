import json

from utils.image_exif_parser import extract_exif_data
from utils.indian_disaster_verification import IndianDisasterVerificationService
from utils.reverse_location_lookup import get_google_maps_link, get_location_name

if __name__ == "__main__":
    image_path = "sample.jpg"

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

    else:
        print("No GPS info found in the image.")
