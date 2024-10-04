from geopy.geocoders import Nominatim


def get_location_name(latitude, longitude):
    geolocator = Nominatim(user_agent="geoapiExercises")
    try:
        location = geolocator.reverse((latitude, longitude), exactly_one=True)
        return location.address if location else "Location not found"
    except Exception as e:
        return f"Error: {e}"


if __name__ == "__main__":
    latitude = 40.748817
    longitude = -73.985428
    location_name = get_location_name(latitude, longitude)
    print(
        f"The location name for coordinates ({latitude}, {longitude}) is: {location_name}"
    )
