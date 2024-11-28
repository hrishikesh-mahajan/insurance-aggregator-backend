from utils.image_exif_parser import extract_exif_data
from utils.reverse_location_lookup import get_google_maps_link, get_location_name

if __name__ == "__main__":
    image_path = "sample.jpg"
    gps_info, timestamp = extract_exif_data(image_path)
    print(f"GPS Info: {gps_info}")
    print(f"Timestamp: {timestamp}")
    if gps_info:
        lat, lon = gps_info
        location_name = get_location_name(lat, lon, complete=True)
        print(f"Location: {location_name}")
        print(f"Google Maps link: {get_google_maps_link(lat, lon)}")
    else:
        print("No GPS info found in the image.")
