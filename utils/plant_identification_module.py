import base64
import io
import os
from typing import Any, Dict

import google.generativeai as genai
from dotenv import load_dotenv
from PIL import Image


class PlantIdentificationService:
    def __init__(self, api_key: str = None):
        """
        Initialize the Plant Identification Service

        :param api_key: Google Gemini API key (optional if set in environment)
        """
        # Load environment variables
        load_dotenv()

        # Use provided API key or get from environment
        self.api_key = api_key or os.getenv('GOOGLE_GEMINI_API_KEY')

        if not self.api_key:
            raise ValueError("No API key provided. Set GOOGLE_GEMINI_API_KEY in .env or pass directly.")

        # Configure Gemini API
        genai.configure(api_key=self.api_key)

        # Initialize the model
        self.model = genai.GenerativeModel('gemini-pro-vision')

    def _preprocess_image(self, image_path: str) -> bytes:
        """
        Preprocess and convert image to base64

        :param image_path: Path to the image file
        :return: Base64 encoded image bytes
        """
        try:
            with Image.open(image_path) as img:
                # Resize large images to reduce API call size
                img.thumbnail((800, 800))

                # Convert image to bytes
                byte_arr = io.BytesIO()
                img.save(byte_arr, format='JPEG')
                return base64.b64encode(byte_arr.getvalue()).decode('utf-8')
        except Exception as e:
            raise ValueError(f"Image preprocessing error: {str(e)}")

    def identify_crop(self, image_path: str) -> Dict[str, Any]:
        """
        Identify crop type from an image

        :param image_path: Path to the farm/crop image
        :return: Dictionary with crop identification details
        """
        try:
            # Preprocess image
            image_base64 = self._preprocess_image(image_path)

            # Prepare prompt
            prompt = """
            Analyze this agricultural image and provide:
            1. Crop/Plant Type: Specific botanical/agricultural name
            2. Confidence Level: Percentage of confidence in identification
            3. Growth Stage: Current growth/maturity stage
            4. Additional Observations: Any notable characteristics or potential health issues

            If the image is unclear or doesn't show a clear agricultural scene,
            state that conclusive identification is not possible.
            """

            # Generate response
            response = self.model.generate_content([prompt, image_base64])

            # Process and return results
            return {
                "success": True,
                "identification": response.text,
                "raw_response": response
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "details": "Crop identification failed"
            }

    def verify_crop_match(self, image_path: str, expected_crop: str) -> Dict[str, Any]:
        """
        Verify if the crop in the image matches the expected crop

        :param image_path: Path to the farm/crop image
        :param expected_crop: Crop type expected according to insurance policy
        :return: Verification results
        """
        try:
            # Identify crop
            identification_result = self.identify_crop(image_path)

            if not identification_result['success']:
                return {
                    "match": False,
                    "reason": "Unable to identify crop",
                    "details": identification_result.get('error', 'Unknown error')
                }

            # Compare identified crop with expected crop
            identified_crop = identification_result['identification']

            # Perform similarity check (can be enhanced with NLP matching)
            match = expected_crop.lower() in identified_crop.lower()

            return {
                "match": match,
                "identified_crop": identified_crop,
                "expected_crop": expected_crop,
                "full_analysis": identification_result
            }

        except Exception as e:
            return {
                "match": False,
                "error": str(e),
                "details": "Verification process failed"
            }

# Example Usage
def main():
    # Initialize the service
    plant_service = PlantIdentificationService()

    # Example image paths (replace with actual paths)
    corn_image = '/path/to/corn/image.jpg'
    wheat_image = '/path/to/wheat/image.jpg'

    # Identify crop
    corn_result = plant_service.identify_crop(corn_image)
    print("Corn Identification:", corn_result)

    # Verify crop match
    verification_result = plant_service.verify_crop_match(
        corn_image,
        expected_crop='Corn'
    )
    print("Verification Result:", verification_result)

if __name__ == "__main__":
    main()
