import requests


def get_location_name(latitude, longitude):
    response = requests.get(
        f"https://api.bigdatacloud.net/data/reverse-geocode-client?latitude={latitude}&longitude={longitude}&localityLanguage=en"
    )
    if response.status_code == 200:
        data = response.json()
        address_components = [
            data.get("locality", ""),
            data.get("principalSubdivision", ""),
            data.get("countryName", ""),
            data.get("street", ""),
            data.get("streetNumber", ""),
        ]
        return ", ".join(filter(None, address_components))
    else:
        return "Error retrieving location"


def get_google_maps_link(latitude, longitude):
    return f"https://www.google.com/maps/search/?api=1&query={latitude},{longitude}"


if __name__ == "__main__":
    latitude = 18.5204
    longitude = 73.8567
    location_name = get_location_name(latitude, longitude)
    print(
        f"The location name for coordinates ({latitude}, {longitude}) is: {location_name}"
    )
    print(
        f"Google Maps link for coordinates ({latitude}, {longitude}): {get_google_maps_link(latitude, longitude)}"
    )
