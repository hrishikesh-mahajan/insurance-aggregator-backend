import json
import logging
from datetime import datetime, timedelta
from pprint import pprint

import requests


class IndianDisasterVerificationService:
    def __init__(self):
        # Set up logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        # Public APIs for disaster-related information
        self.apis = {
            "nasa_eonet": {
                "url": "https://eonet.gsfc.nasa.gov/api/v3/events",
                "params": {
                    "status": "open",
                    "bbox": "68.1766451,6.4546608,97.4025614,37.6173922",  # India's bounding box
                },
            },
            "reliefweb": {
                "url": "https://api.reliefweb.int/v1/disasters",
                "params": {
                    "query[value]": "country.id:119",
                    "limit": 3,
                    "preset": "latest",
                },  # India
            },
        }

        # Predefined disaster categories relevant to agriculture
        self.agricultural_disaster_types = [
            "drought",
            "flood",
            "heavy_rainfall",
            "cyclone",
            "extreme_heat",
            "landslide",
            "wildfires",
        ]

    def verify_location_disaster(self, latitude, longitude, date, radius_km=50):
        """
        Verify if a disaster occurred at a specific location

        :param latitude: Location latitude
        :param longitude: Location longitude
        :param date: Date of incident
        :param radius_km: Search radius
        :return: Disaster verification report
        """
        verification_report = {
            "location": {"latitude": latitude, "longitude": longitude},
            "date": date,
            "disaster_occurred": False,
            "disasters": [],
        }

        # Check NASA Earth Observatory Natural Event Tracker (EONET)
        eonet_disasters = self._check_nasa_eonet(latitude, longitude, date, radius_km)

        # Check ReliefWeb disasters
        reliefweb_disasters = self._check_reliefweb(
            latitude, longitude, date, radius_km
        )

        # Combine and deduplicate results
        all_disasters = eonet_disasters + reliefweb_disasters

        if all_disasters:
            verification_report["disaster_occurred"] = True
            verification_report["disasters"] = all_disasters

        return verification_report

    def _check_nasa_eonet(self, latitude, longitude, date, radius_km):
        """
        Check NASA's Earth Observatory Natural Event Tracker
        """
        disasters = []
        try:
            response = requests.get(
                self.apis["nasa_eonet"]["url"], params=self.apis["nasa_eonet"]["params"]
            )
            if response.status_code == 200:
                events = response.json().get("events", [])

                nasa_eonet_disasters = []

                for event in events:
                    nasa_eonet_disasters.append(event)
                    # Check if event is close to location and date
                    if self._is_event_relevant(
                        event, latitude, longitude, date, radius_km
                    ):
                        disasters.append(
                            {
                                "source": "NASA EONET",
                                "type": event.get("categories", [{}])[0].get(
                                    "title", "Unknown"
                                ),
                                "title": event.get("title", "Unnamed Event"),
                                "date": event.get("geometry", [{}])[0].get("date"),
                                "coordinates": event.get("geometry", [{}])[0].get(
                                    "coordinates"
                                ),
                                "link": event.get("sources", [{}])[0]
                                .get("url")
                                .replace("amp;", ""),
                            }
                        )

                with open("nasa_eonet_disasters.json", "w") as f:
                    json.dump(nasa_eonet_disasters, f, indent=2)
        except Exception as e:
            self.logger.error(f"NASA EONET API error: {e}")

        return disasters

    def _check_reliefweb(self, latitude, longitude, date, radius_km):
        """
        Check ReliefWeb disaster reports for India
        """
        disasters = []
        try:
            response = requests.get(
                self.apis["reliefweb"]["url"], params=self.apis["reliefweb"]["params"]
            )

            if response.status_code == 200:
                disaster_data = response.json().get("data", [])
                relief_disasters = []

                for disaster in disaster_data:
                    disaster_response = requests.get(disaster.get("href"))
                    disaster = disaster_response.json().get("data", [])[0]

                    relief_disasters.append(disaster)

                    # Check if disaster is close to location and date
                    if self._is_reliefweb_event_relevant(
                        disaster, latitude, longitude, date, radius_km
                    ):
                        disasters.append(
                            {
                                "source": "ReliefWeb",
                                "type": disaster.get("fields", {})
                                .get("type", [{}])[0]
                                .get("name", "Unknown"),
                                "title": disaster.get("fields", {}).get(
                                    "name", "Unnamed Event"
                                ),
                                "date": disaster.get("fields", {})
                                .get("date", {})
                                .get("created"),
                                "location": disaster.get("fields", {})
                                .get("country", {})[0]
                                .get("location"),
                                "link": disaster.get("fields", {}).get("url_alias", ""),
                            }
                        )

                with open("reliefweb_disasters.json", "w") as f:
                    json.dump(relief_disasters, f, indent=2)

        except Exception as e:
            self.logger.error(f"ReliefWeb API error: {e}")
        return disasters

    def _is_event_relevant(self, event, latitude, longitude, target_date, radius_km):
        """
        Check if an event is relevant to the specified location and date
        """
        # Implement haversine formula for distance calculation
        from math import atan2, cos, radians, sin, sqrt

        # print("Event: ", json.dumps(event, indent=2))
        # print("Latitude: ", latitude)
        # print("Longitude: ", longitude)
        # print("Target Date: ", target_date)
        # print("Radius: ", radius_km)

        def haversine_distance(lat1, lon1, lat2, lon2):
            R = 6371  # Earth radius in kilometers

            # Convert degrees to radians
            lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

            # Haversine formula
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
            c = 2 * atan2(sqrt(a), sqrt(1 - a))
            distance = R * c

            return distance

        # Check event geometry (coordinates)
        if event.get("geometry"):
            event_coords = event["geometry"][0]
            event_lat = event_coords.get("coordinates", [0, 0])[1]
            event_lon = event_coords.get("coordinates", [0, 0])[0]

            # Calculate distance
            distance = haversine_distance(latitude, longitude, event_lat, event_lon)

            # Check if within radius and date is close
            event_date = event_coords.get("date")

            if distance <= radius_km and self._is_date_close(event_date, target_date):
                return True

        return False

    def _is_reliefweb_event_relevant(
        self, disaster, latitude, longitude, target_date, radius_km
    ):
        """
        Check relevance for ReliefWeb events
        """
        from math import atan2, cos, radians, sin, sqrt

        def haversine_distance(lat1, lon1, lat2, lon2):
            R = 6371  # Earth radius in kilometers
            lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
            c = 2 * atan2(sqrt(a), sqrt(1 - a))
            distance = R * c
            return distance

        # Check disaster location (coordinates)
        if disaster.get("fields", {}).get("country", [{}])[0].get("location"):
            disaster_coords = disaster["fields"]["country"][0]["location"]
            disaster_lat = disaster_coords.get("lat")
            disaster_lon = disaster_coords.get("lon")

            # Calculate distance
            distance = haversine_distance(
                latitude, longitude, disaster_lat, disaster_lon
            )

            # Check if within radius and date is close
            disaster_date = disaster.get("fields", {}).get("date", {}).get("created")
            # print("Disaster Date: ", disaster_date)
            if distance <= radius_km and self._is_date_close(
                disaster_date, target_date
            ):
                return True

        return False

    def _is_date_close(self, event_date, target_date, days_threshold=30):
        """
        Check if dates are within a reasonable proximity
        """
        try:
            event_datetime = datetime.fromisoformat(event_date.replace("Z", "+00:00"))
            target_datetime = datetime.fromisoformat(target_date)

            aware_target_datetime = target_datetime.replace(
                tzinfo=event_datetime.tzinfo
            )  # Ensure same timezone
            target_datetime = aware_target_datetime

            # Check if within specified number of days
            date_difference = abs((event_datetime - target_datetime).days)
            return date_difference <= days_threshold
        except Exception as e:
            print("Error in date comparison: ", e)
            return False

    def generate_insurance_report(self, verification_result):
        """
        Generate insurance claim verification report
        """
        return {
            "claim_verifiable": verification_result["disaster_occurred"],
            "disaster_types": [
                disaster["type"]
                for disaster in verification_result.get("disasters", [])
            ],
            "disaster_sources": list(
                set(
                    disaster["source"]
                    for disaster in verification_result.get("disasters", [])
                )
            ),
        }


# Example Usage
if __name__ == "__main__":
    # Initialize the verification service
    disaster_service = IndianDisasterVerificationService()

    # Example farm location (Maharashtra)
    farm_location = {
        "latitude": 19.0760,  # Coordinates near Pune
        "longitude": 72.8777,
        "date": datetime.now().strftime("%Y-%m-%d"),
    }

    farm_location = {
        "latitude": 25.78,  # Coordinates near Madhya Pradesh
        "longitude": 76.62,
        "date": "2024-11-07",
    }

    # Verify disaster for the location
    verification_result = disaster_service.verify_location_disaster(
        farm_location["latitude"], farm_location["longitude"], farm_location["date"]
    )

    # Generate insurance report
    insurance_report = disaster_service.generate_insurance_report(verification_result)

    print("Disaster Verification Report:")
    print(json.dumps(verification_result, indent=2))
    print("\nInsurance Claim Report:")
    print(json.dumps(insurance_report, indent=2))

    with open("disaster_verification.json", "w") as f:
        json.dump(verification_result, f, indent=2)

    with open("insurance_report.json", "w") as f:
        json.dump(insurance_report, f, indent=2)
