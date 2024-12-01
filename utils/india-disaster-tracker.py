import requests
import logging
from datetime import datetime, timedelta
import json
import os
from dotenv import load_dotenv


class IndianDisasterVerificationService:
    def __init__(self):
        # Load environment variables
        load_dotenv()

        # Set up logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        # API Sources for Indian Disaster Data
        self.apis = {
            "ndma": {
                "url": "https://nidm.gov.in/api/disaster-reports",
                "api_key": os.getenv("NDMA_API_KEY"),
            },
            "imd": {
                "url": "https://mausam.imd.gov.in/api/disaster-alerts",
                "api_key": os.getenv("IMD_API_KEY"),
            },
            "state_disaster_management": {
                "base_url": "https://api.state-disaster-management.in/reports"
            },
        }

        # Predefined disaster categories relevant to agriculture
        self.agricultural_disaster_types = [
            "drought",
            "flood",
            "heavy_rainfall",
            "hailstorm",
            "cyclone",
            "extreme_temperature",
            "landslide",
        ]

    def verify_location_disaster(self, latitude, longitude, date, precision_km=10):
        """
        Comprehensive disaster verification for agricultural insurance

        :param latitude: GPS Latitude of the location
        :param longitude: GPS Longitude of the location
        :param date: Date of incident
        :param precision_km: Search radius for location
        :return: Detailed disaster verification report
        """
        verification_report = {
            "location": {"latitude": latitude, "longitude": longitude},
            "date": date,
            "disaster_occurred": False,
            "disaster_details": [],
            "verification_sources": [],
        }

        # Sources to check
        sources_to_check = [
            self._check_ndma_reports,
            self._check_imd_alerts,
            self._check_state_disaster_reports,
            self._check_satellite_data,
        ]

        for source_check in sources_to_check:
            try:
                source_result = source_check(latitude, longitude, date, precision_km)

                if source_result["disaster_occurred"]:
                    verification_report["disaster_occurred"] = True
                    verification_report["disaster_details"].extend(
                        source_result["disaster_details"]
                    )
                    verification_report["verification_sources"].append(
                        source_result["source"]
                    )

            except Exception as e:
                self.logger.error(f"Error checking source {source_check.__name__}: {e}")

        return verification_report

    def _check_ndma_reports(self, latitude, longitude, date, precision_km):
        """
        Check National Disaster Management Authority reports
        """
        try:
            response = requests.get(
                self.apis["ndma"]["url"],
                params={
                    "latitude": latitude,
                    "longitude": longitude,
                    "date": date,
                    "radius": precision_km,
                },
                headers={"Authorization": f"Bearer {self.apis['ndma']['api_key']}"},
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("disasters"):
                    return {
                        "disaster_occurred": True,
                        "disaster_details": data["disasters"],
                        "source": "NDMA",
                    }
        except Exception as e:
            self.logger.warning(f"NDMA API error: {e}")

        return {"disaster_occurred": False, "disaster_details": []}

    def _check_imd_alerts(self, latitude, longitude, date, precision_km):
        """
        Check India Meteorological Department alerts
        """
        try:
            response = requests.get(
                self.apis["imd"]["url"],
                params={
                    "lat": latitude,
                    "lon": longitude,
                    "date": date,
                    "radius": precision_km,
                },
                headers={"Authorization": f"Bearer {self.apis['imd']['api_key']}"},
            )

            if response.status_code == 200:
                data = response.json()
                weather_alerts = [
                    alert
                    for alert in data.get("alerts", [])
                    if alert["type"] in self.agricultural_disaster_types
                ]

                if weather_alerts:
                    return {
                        "disaster_occurred": True,
                        "disaster_details": weather_alerts,
                        "source": "IMD",
                    }
        except Exception as e:
            self.logger.warning(f"IMD API error: {e}")

        return {"disaster_occurred": False, "disaster_details": []}

    def _check_state_disaster_reports(self, latitude, longitude, date, precision_km):
        """
        Cross-reference with state-level disaster management systems
        """
        # Placeholder for state-level API calls
        # Would involve making calls to individual state disaster management APIs
        return {"disaster_occurred": False, "disaster_details": []}

    def _check_satellite_data(self, latitude, longitude, date, precision_km):
        """
        Use satellite imagery to detect potential agricultural disasters

        Requires integration with satellite imagery APIs like:
        - NASA Earth Data
        - ISRO Bhuvan
        - Copernicus Open Access Hub
        """
        # Placeholder for satellite data analysis
        return {"disaster_occurred": False, "disaster_details": []}

    def generate_insurance_report(self, verification_result):
        """
        Generate a standardized insurance claim verification report
        """
        return {
            "claim_verifiable": verification_result["disaster_occurred"],
            "disaster_type": (
                [detail["type"] for detail in verification_result["disaster_details"]]
                if verification_result["disaster_occurred"]
                else []
            ),
            "verification_sources": verification_result["verification_sources"],
            "additional_notes": f"Verified across {len(verification_result['verification_sources'])} sources",
        }


# Example Usage
if __name__ == "__main__":
    # Initialize the verification service
    disaster_service = IndianDisasterVerificationService()

    # Example verification for a farm location in Maharashtra
    farm_location = {
        "latitude": 19.0760,  # Example coordinates near Pune
        "longitude": 72.8777,
        "date": datetime.now().strftime("%Y-%m-%d"),
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
