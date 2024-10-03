from PIL import Image
import piexif


def get_exif_data(image_path):
    image = Image.open(image_path)
    exif_data = piexif.load(image.info["exif"])
    return exif_data


def get_gps_info(exif_data):
    gps_info = exif_data.get("GPS", {})
    if not gps_info:
        return None

    def get_if_exist(data, key):
        return data[key] if key in data else None

    def convert_to_degrees(value):
        d = float(value[0][0]) / float(value[0][1])
        m = float(value[1][0]) / float(value[1][1])
        s = float(value[2][0]) / float(value[2][1])
        return d + (m / 60.0) + (s / 3600.0)

    gps_latitude = get_if_exist(gps_info, piexif.GPSIFD.GPSLatitude)
    gps_latitude_ref = get_if_exist(gps_info, piexif.GPSIFD.GPSLatitudeRef)
    gps_longitude = get_if_exist(gps_info, piexif.GPSIFD.GPSLongitude)
    gps_longitude_ref = get_if_exist(gps_info, piexif.GPSIFD.GPSLongitudeRef)

    if gps_latitude and gps_latitude_ref and gps_longitude and gps_longitude_ref:
        lat = convert_to_degrees(gps_latitude)
        if gps_latitude_ref != b"N":
            lat = -lat

        lon = convert_to_degrees(gps_longitude)
        if gps_longitude_ref != b"E":
            lon = -lon

        return lat, lon
    return None


def get_timestamp(exif_data):
    timestamp = exif_data.get("0th", {}).get(piexif.ImageIFD.DateTime, None)
    if timestamp:
        return timestamp.decode("utf-8")
    return None


def extract_exif_data(image_path):
    exif_data = get_exif_data(image_path)
    gps_info = get_gps_info(exif_data)
    timestamp = get_timestamp(exif_data)
    return gps_info, timestamp


if __name__ == "__main__":
    image_path = "sample.jpg"
    gps_info, timestamp = extract_exif_data(image_path)
    print(f"GPS Info: {gps_info}")
    print(f"Timestamp: {timestamp}")
