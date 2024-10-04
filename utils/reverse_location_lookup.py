import requests


def get_location_name(latitude, longitude, complete=False):
    response = requests.get(
        f"https://api.bigdatacloud.net/data/reverse-geocode-client?latitude={latitude}&longitude={longitude}&localityLanguage=en"
    )
    if response.status_code == 200:
        data = response.json()

        ordered_address = []
        for key in data.get("localityInfo", {}).get("administrative", []):
            ordered_address.append(key)
        for key in data.get("localityInfo", {}).get("informative", []):
            ordered_address.append(key)
        ordered_address.sort(key=lambda x: x.get("order", 0), reverse=True)
        complete_address = [data.get("plusCode", "")] + [
            key.get("name", "") for key in ordered_address
        ]

        if complete:
            return ", ".join([key for key in complete_address])

        address_components = [
            data.get("plusCode", ""),
            data.get("locality", ""),
            data.get("city", ""),
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
    latitude = 25.78
    longitude = 76.62
    location_name = get_location_name(latitude, longitude)
    print(
        f"The location name for coordinates ({latitude}, {longitude}) is: {location_name}"
    )
    print(
        f"Complete location name: {get_location_name(latitude, longitude, complete=True)}"
    )
    print(
        f"Google Maps link for coordinates ({latitude}, {longitude}): {get_google_maps_link(latitude, longitude)}"
    )
