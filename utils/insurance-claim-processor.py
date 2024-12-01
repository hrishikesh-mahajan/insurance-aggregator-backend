import json
import logging
import os
import re
import uuid
from typing import Any, Dict, List

import google.generativeai as genai
import numpy as np
from dotenv import load_dotenv

# Third-party libraries
import pandas as pd
import PyPDF2
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class InsuranceClaimProcessor:
    def __init__(self, gemini_api_key: str = ""):
        """
        Initialize the Insurance Claim Processor with Gemini API integration

        Args:
            gemini_api_key (str): Google Gemini API Key for advanced AI processing
        """
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        self.logger = logging.getLogger(__name__)

        # Set your Gemini API Key
        load_dotenv()

        # Configure Gemini API
        genai.configure(api_key=os.getenv("GOOGLE_GEMINI_API_KEY"))
        self.gemini_pro_model = genai.GenerativeModel("gemini-pro")
        self.gemini_vision_model = genai.GenerativeModel("gemini-1.5-flash")

        # Configuration for processing
        self.config = {
            "max_document_size_mb": 10,
            "accepted_file_types": [".pdf", ".jpg", ".jpeg", ".png", ".txt"],
        }

    def preprocess_text(self, text: str) -> str:
        """
        Preprocess and clean text input

        Args:
            text (str): Raw input text

        Returns:
            str: Cleaned and normalized text
        """
        # Remove special characters and extra whitespaces
        text = re.sub(r"[^a-zA-Z0-9\s]", "", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text.lower()

    def detect_and_translate_text(self, text: str) -> str:
        """
        Detect language and translate to English using Gemini

        Args:
            text (str): Input text

        Returns:
            str: English translated text
        """
        try:
            # Use Gemini for language detection and translation
            translation_prompt = f"""
            Detect the language of the following text and translate it to English.
            If the text is already in English, just return the original text.

            Original Text: {text}

            Provide only the translated text in English.
            """

            response = self.gemini_pro_model.generate_content(translation_prompt)
            translated_text = response.text.strip()

            return self.preprocess_text(translated_text)

        except Exception as e:
            self.logger.error(f"Translation error: {e}")
            return self.preprocess_text(text)

    def extract_text_from_document(self, file_path: str) -> str:
        """
        Extract text from various document types using Gemini Vision

        Args:
            file_path (str): Path to the document

        Returns:
            str: Extracted text content
        """
        file_ext = os.path.splitext(file_path)[1].lower()

        try:
            if file_ext == ".pdf":
                with open(file_path, "rb") as file:
                    reader = PyPDF2.PdfReader(file)
                    # Extract text from the first page for initial processing
                    # More complex PDF handling can be added if needed
                    text = reader.pages[0].extract_text()

            elif file_ext in [".jpg", ".jpeg", ".png"]:
                # Use Gemini Vision for OCR
                with open(file_path, "rb") as image_file:
                    image_parts = [
                        {"mime_type": "image/jpeg", "data": image_file.read()}
                    ]

                    ocr_prompt = "Extract all readable text from this image. Ensure you capture every detail."
                    response = self.gemini_vision_model.generate_content(
                        contents=[image_parts[0], ocr_prompt]  # type: ignore
                    )
                    text = response.text

            elif file_ext == ".txt":
                with open(file_path, "r", encoding="utf-8") as file:
                    text = file.read()

            else:
                raise ValueError(f"Unsupported file type: {file_ext}")

            # Translate and preprocess the extracted text
            return self.detect_and_translate_text(text)

        except Exception as e:
            self.logger.error(f"Document extraction error: {e}")
            return ""

    def analyze_text_coherence(self, documents: List[str]) -> Dict[str, float | str]:
        """
        Analyze text coherence using TF-IDF and cosine similarity

        Args:
            documents (List[str]): List of document texts

        Returns:
            Dict[str, float]: Coherence metrics
        """
        if len(documents) < 2:
            return {
                "coherence_score": 1.0,
                "consistency_level": "High",
                "confidence": 0.9,
            }

        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform(documents)
        cosine_scores = cosine_similarity(tfidf_matrix)

        avg_similarity = np.mean(cosine_scores[np.triu_indices(len(documents), k=1)])

        coherence_levels = {
            (0, 0.2): ("Very Low", 0.1),
            (0.2, 0.4): ("Low", 0.3),
            (0.4, 0.6): ("Medium", 0.5),
            (0.6, 0.8): ("High", 0.7),
            (0.8, 1.0): ("Very High", 0.9),
        }

        for (lower, upper), (level, score) in coherence_levels.items():
            if lower <= avg_similarity < upper:
                return {
                    "coherence_score": float(avg_similarity),
                    "consistency_level": level,
                    "confidence": score,
                }
        return {}

    def detect_potential_fraud(self, documents: List[str]) -> Dict[str, Any]:
        """
        Use Gemini AI to detect potential fraudulent patterns

        Args:
            documents (List[str]): List of document texts

        Returns:
            Dict[str, Any]: Fraud detection results
        """
        combined_text = " ".join(documents)

        try:
            prompt = f"""
            Perform a comprehensive fraud analysis on the following insurance claim documents:

            Documents: {combined_text}

            Provide a detailed analysis covering:
            1. Detailed examination of document consistency
            2. Identification of potential inconsistencies or red flags
            3. Suspicious patterns or anomalies
            4. Credibility assessment of the claim
            5. Recommended areas for further investigation

            Classify the overall fraud risk and provide a confidence level for your assessment.
            """

            response = self.gemini_pro_model.generate_content(prompt)
            fraud_analysis = response.text

            # Integrated risk scoring based on Gemini's analysis
            risk_prompt = f"""
            Based on the following fraud analysis, provide a numerical risk score from 0 to 1:

            {fraud_analysis}

            Consider document inconsistencies, suspicious patterns, and overall claim credibility.
            Respond ONLY with a single numerical value representing the risk score.
            """

            risk_response = self.gemini_pro_model.generate_content(risk_prompt)

            try:
                risk_score = float(risk_response.text.strip())
            except ValueError:
                risk_score = 0.5  # Default to medium risk if parsing fails

            risk_levels = {
                "Low Risk": (0, 0.3),
                "Medium Risk": (0.3, 0.7),
                "High Risk": (0.7, 1.0),
            }

            for level, (lower, upper) in risk_levels.items():
                if lower <= risk_score < upper:
                    return {
                        "fraud_analysis": fraud_analysis,
                        "risk_level": level,
                        "risk_score": min(risk_score, 1.0),
                    }

        except Exception as e:
            self.logger.error(f"Fraud detection error: {e}")
        return {
            "fraud_analysis": "Unable to complete comprehensive analysis",
            "risk_level": "Unknown",
            "risk_score": 0.5,
        }

    def generate_claim_report(self, document_paths: List[str]) -> Dict[str, Any]:
        """
        Generate a comprehensive claim report

        Args:
            document_paths (List[str]): Paths to claim documents

        Returns:
            Dict[str, Any]: Comprehensive claim report
        """
        report_id = str(uuid.uuid4())

        # Extract text from documents
        extracted_texts = [
            self.extract_text_from_document(path) for path in document_paths
        ]

        # Remove any empty texts
        extracted_texts = [text for text in extracted_texts if text]

        # Analyze coherence and fraud
        coherence_result = self.analyze_text_coherence(extracted_texts)
        fraud_detection = self.detect_potential_fraud(extracted_texts)

        report = {
            "report_id": report_id,
            "documents_analyzed": document_paths,
            "total_documents": len(document_paths),
            "extracted_text_length": [len(text) for text in extracted_texts],
            "coherence": coherence_result,
            "fraud_detection": fraud_detection,
            "timestamp": pd.Timestamp.now().isoformat(),
        }

        # Save report to JSON
        with open(f"claim_report_{report_id}.json", "w") as f:
            json.dump(report, f, indent=4)

        with open(f"claim_report_{report_id}.md", "w") as f:
            f.write(f"# Insurance Claim Report ({report_id})\n\n")
            f.write("## Documents Analyzed\n\n")
            for i, doc in enumerate(document_paths):
                f.write(f"{i + 1}. {doc}\n")
            f.write("\n")
            f.write("## Coherence Analysis\n\n")
            f.write(f"Coherence Score: {coherence_result['coherence_score']}\n")
            f.write(f"Consistency Level: {coherence_result['consistency_level']}\n")
            f.write(f"Confidence Level: {coherence_result['confidence']}\n\n")
            f.write("## Fraud Detection\n\n")
            f.write(f"Fraud Analysis:\n\n{fraud_detection['fraud_analysis']}\n\n")
            f.write(f"Risk Level: {fraud_detection['risk_level']}\n")
            f.write(f"Risk Score: {fraud_detection['risk_score']}\n\n")
            f.write("## Timestamp\n\n")
            f.write(f"{report['timestamp']}\n")

        return report


# Example Usage
def main():
    processor = InsuranceClaimProcessor()

    # Example document paths
    document_paths = ["sample.jpg"]

    # Process claim
    claim_report = processor.generate_claim_report(document_paths)
    print(json.dumps(claim_report, indent=2))


if __name__ == "__main__":
    main()
