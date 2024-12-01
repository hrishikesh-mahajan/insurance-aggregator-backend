import requests
from datetime import datetime, timedelta
import json

class NaturalDisasterTracker:
    def __init__(self):
        # GDACS API base URL
        self.base_url = "https://www.gdacs.org/gdacsapi/api/events/geoRSS"

    def fetch_disasters(self, latitude, longitude, 
                        start_date=None, 
                        end_date=None, 
                        radius_km=100, 
                        disaster_types=None):
        """
        Fetch natural disaster data for a specific location.
        
        :param latitude: GPS Latitude
        :param longitude: GPS Longitude
        :param start_date: Start date for disaster search (default: 30 days ago)
        :param end_date: End date for disaster search (default: current date)
        :param radius_km: Search radius in kilometers
        :param disaster_types: List of disaster types to filter (optional)
        :return: List of disaster events
        """
        # Set default date range if not provided
        if start_date is None:
            start_date = datetime.now() - timedelta(days=30)
        if end_date is None:
            end_date = datetime.now()
        
        # Prepare query parameters
        params = {
            'lat': latitude,
            'lon': longitude,
            'radius': radius_km,
            'startdate': start_date.strftime('%Y-%m-%d'),
            'enddate': end_date.strftime('%Y-%m-%d')
        }
        
        try:
            # Make API request
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()  # Raise an exception for bad responses
            
            # Parse the XML response
            disasters = self._parse_gdacs_response(response.text)
            
            # Filter by disaster types if specified
            if disaster_types:
                disasters = [
                    disaster for disaster in disasters 
                    if disaster['type'] in disaster_types
                ]
            
            return disasters
        
        except requests.RequestException as e:
            print(f"Error fetching disaster data: {e}")
            return []

    def _parse_gdacs_response(self, xml_response):
        """
        Parse the GDACS XML response and extract relevant disaster information.
        
        :param xml_response: Raw XML response from GDACS
        :return: List of disaster dictionaries
        """
        # Note: This is a placeholder. In a real implementation, 
        # you'd use an XML parsing library like ElementTree or BeautifulSoup
        disasters = []
        
        # Example parsing logic (pseudo-code)
        # This would need to be replaced with actual XML parsing
        try:
            # Parse XML and extract disaster details
            # Each disaster would include:
            disasters.append({
                'type': 'earthquake',  # or hurricane, flood, etc.
                'severity': 'high',
                'location': 'Example Location',
                'date': datetime.now(),
                'coordinates': {
                    'latitude': 0.0,
                    'longitude': 0.0
                },
                'additional_info': {}
            })
        except Exception as e:
            print(f"Error parsing XML: {e}")
        
        return disasters

    def get_nearby_disasters(self, latitude, longitude, radius_km=100):
        """
        Convenient method to get nearby disasters within a specified radius.
        
        :param latitude: GPS Latitude
        :param longitude: GPS Longitude
        :param radius_km: Search radius in kilometers
        :return: List of nearby disaster events
        """
        return self.fetch_disasters(
            latitude, 
            longitude, 
            radius_km=radius_km
        )

# Example usage
if __name__ == "__main__":
    # Initialize the disaster tracker
    tracker = NaturalDisasterTracker()
    
    # Example coordinates (New York City)
    latitude = 40.7128
    longitude = -74.0060
    
    # Fetch disasters near New York City in the last 30 days
    nearby_disasters = tracker.get_nearby_disasters(latitude, longitude)
    
    # Print out the disasters
    print("Nearby Disasters:")
    print(json.dumps(nearby_disasters, indent=2))
