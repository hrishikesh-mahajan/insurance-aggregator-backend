import json
import logging
import os
from datetime import datetime
from typing import Any, Dict

import markdown2
import requests
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


class AdvancedClaimVerificationService:
    def __init__(self, input_directory: str, output_directory: str):
        """
        Initialize Advanced Claim Verification Service

        :param input_directory: Directory containing input JSON files
        :param output_directory: Directory to store verification reports
        """
        self.input_directory = input_directory
        self.output_directory = output_directory

        # Gemini API Configuration
        self.GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
        self.GEMINI_ENDPOINT = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent'

        # Logging setup
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s: %(message)s',
            filename=os.path.join(output_directory, 'advanced_claim_verification.log')
        )

    def load_json_files(self) -> Dict[str, Any]:
        """
        Load all JSON files from input directory

        :return: Dictionary of JSON file contents
        """
        json_contents = {}
        for filename in os.listdir(self.input_directory):
            if filename.endswith('.json'):
                filepath = os.path.join(self.input_directory, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        json_contents[filename] = json.load(f)
                except json.JSONDecodeError as e:
                    logging.error(f"Error decoding {filename}: {e}")
                except Exception as e:
                    logging.error(f"Error reading {filename}: {e}")

        return json_contents

    def generate_comprehensive_report_with_gemini(self, json_contents: Dict[str, Any]) -> str:
        """
        Generate comprehensive report using Gemini API

        :param json_contents: Dictionary of JSON file contents
        :return: Markdown formatted report
        """
        try:
            # Prepare payload for Gemini API
            prompt = f"""
            You are an expert insurance claim verifier for a farming sector insurance company.
            Analyze the following semi-structured JSON data and generate a comprehensive,
            structured markdown report that includes:

            1. Detailed overview of the claim
            2. Comprehensive analysis of all submitted documents
            3. Key findings and insights
            4. Potential red flags or inconsistencies
            5. Recommendation for claim processing

            JSON Data Overview:
            {json.dumps({k: str(type(v)) for k, v in json_contents.items()})}

            Full JSON Content:
            {json.dumps(json_contents, indent=2)}
            """

            # Make API call to Gemini
            headers = {
                'Content-Type': 'application/json'
            }
            payload = {
                'contents': [{'parts': [{'text': prompt}]}]
            }

            response = requests.post(
                f"{self.GEMINI_ENDPOINT}?key={self.GEMINI_API_KEY}",
                headers=headers,
                json=payload
            )

            # Extract report from response
            if response.status_code == 200:
                report_content = response.json().get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '')
                return report_content
            else:
                logging.error(f"Gemini API Error: {response.text}")
                return self._fallback_report(json_contents)

        except Exception as e:
            logging.error(f"Report generation error: {e}")
            return self._fallback_report(json_contents)

    def _fallback_report(self, json_contents: Dict[str, Any]) -> str:
        """
        Fallback report generation method

        :param json_contents: Dictionary of JSON file contents
        :return: Basic markdown report
        """
        report = [
            "# Claim Verification Report",
            f"**Generated on:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Overview",
            "Unable to generate comprehensive report via Gemini API.",
            "",
            "## Submitted Documents"
        ]

        # Add basic information about submitted documents
        for filename, content in json_contents.items():
            report.append(f"### {filename}")
            report.append(f"- **Type:** {type(content)}")
            report.append(f"- **Size:** Approximately {len(str(content))} characters")

        return "\n".join(report)

    def convert_markdown_to_pdf(self, markdown_content: str, output_filename: str):
        """
        Convert markdown to PDF

        :param markdown_content: Markdown formatted report
        :param output_filename: Output PDF filename
        """
        try:
            # Convert markdown to HTML first
            html_content = markdown2.markdown(markdown_content)

            # Create PDF
            pdf_path = os.path.join(self.output_directory, output_filename)
            doc = SimpleDocTemplate(pdf_path, pagesize=letter)
            styles = getSampleStyleSheet()

            # Convert HTML to PDF-compatible paragraphs
            story = []
            for line in html_content.split('\n'):
                if line.strip():
                    story.append(Paragraph(line, styles['Normal']))
                story.append(Spacer(1, 6))

            # Build PDF
            doc.build(story)

            logging.info(f"PDF report generated: {pdf_path}")

        except Exception as e:
            logging.error(f"PDF conversion error: {e}")

    def run_verification(self):
        """
        Execute full claim verification process
        """
        try:
            # Load JSON files
            json_contents = self.load_json_files()

            # Generate comprehensive report
            markdown_report = self.generate_comprehensive_report_with_gemini(json_contents)

            # Generate PDF report
            output_filename = f'claim_verification_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
            self.convert_markdown_to_pdf(markdown_report, output_filename)

            # Optionally, save markdown as well
            markdown_path = os.path.join(
                self.output_directory,
                f'claim_verification_{datetime.now().strftime("%Y%m%d_%H%M%S")}.md'
            )
            with open(markdown_path, 'w', encoding='utf-8') as f:
                f.write(markdown_report)

            logging.info("Claim verification process completed successfully")

        except Exception as e:
            logging.error(f"Verification process failed: {e}")

def main():
    verification_service = AdvancedClaimVerificationService(
        input_directory='./output',
        output_directory='./reports'
    )
    verification_service.run_verification()

if __name__ == "__main__":
    main()
