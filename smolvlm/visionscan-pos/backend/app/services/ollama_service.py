import base64
import json
import logging
from typing import List, Optional
import requests
from config import config

logger = logging.getLogger(__name__)


class OllamaDetectionResult:
    """Result from Ollama detection."""
    def __init__(self, product_name: str, confidence: float, quantity: int = 1):
        self.product_name = product_name.strip()
        self.confidence = min(max(confidence, 0.0), 1.0)  # Clamp 0-1
        self.quantity = max(quantity, 1)


class OllamaService:
    """Service for interacting with Ollama LLava-Phi3 model."""

    def __init__(self, endpoint: str = None, model: str = None):
        self.endpoint = endpoint or config.OLLAMA_ENDPOINT
        self.model = model or config.OLLAMA_MODEL
        self.api_url = f"{self.endpoint}/api/generate"

    def build_inventory_prompt(self, inventory_names: List[str]) -> str:
        """Build prompt with inventory context."""
        inventory_str = ", ".join(inventory_names)
        prompt = f"""Analyze this image and identify products from our inventory.

Available products: {inventory_str}

Please respond with a JSON object containing detected products. Format:
{{
  "products": [
    {{"name": "product_name_from_list", "confidence": 0.95, "quantity": 1}},
    ...
  ]
}}

Only include products that you see in the image from the available list.
Set confidence as a decimal 0-1.
Be strict - only report products you're confident about.
If no products detected, return {{"products": []}}"""
        return prompt

    def detect_products(
        self,
        image_base64: str,
        inventory_names: List[str]
    ) -> tuple[List[OllamaDetectionResult], int]:
        """
        Detect products in image using Ollama Llava-Phi3.

        Returns: (results, processing_time_ms)
        Raises: ValueError for invalid input, requests.RequestException for API errors
        """
        if not image_base64:
            raise ValueError("Image base64 cannot be empty")

        if not inventory_names:
            raise ValueError("Inventory list cannot be empty")

        prompt = self.build_inventory_prompt(inventory_names)

        try:
            response = requests.post(
                self.api_url,
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "images": [image_base64],
                    "stream": False,
                },
                timeout=config.OLLAMA_TIMEOUT,
            )
            response.raise_for_status()

            data = response.json()

            # Parse response to extract products
            response_text = data.get("response", "")
            results = self._parse_response(response_text)

            # Get processing time in milliseconds
            eval_duration = data.get("eval_duration", 0)
            processing_time_ms = eval_duration // 1_000_000  # Convert nanoseconds to ms

            return results, processing_time_ms

        except requests.exceptions.Timeout:
            logger.error("Ollama request timed out")
            raise
        except requests.exceptions.ConnectionError:
            logger.error(f"Failed to connect to Ollama at {self.endpoint}")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama API error: {e}")
            raise

    def _parse_response(self, response_text: str) -> List[OllamaDetectionResult]:
        """Parse Ollama response and extract products."""
        try:
            # Try to extract JSON from response
            # Look for { and } markers
            start = response_text.find("{")
            end = response_text.rfind("}") + 1

            if start == -1 or end == 0:
                logger.warning(f"No JSON found in response: {response_text[:200]}")
                return []

            json_str = response_text[start:end]
            data = json.loads(json_str)

            results = []
            for product in data.get("products", []):
                try:
                    result = OllamaDetectionResult(
                        product_name=product.get("name", ""),
                        confidence=float(product.get("confidence", 0.0)),
                        quantity=int(product.get("quantity", 1))
                    )
                    if result.product_name:  # Only add non-empty names
                        results.append(result)
                except (ValueError, TypeError, KeyError) as e:
                    logger.warning(f"Failed to parse product entry: {product}, error: {e}")
                    continue

            return results

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse Ollama response as JSON: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error parsing Ollama response: {e}")
            return []


# Singleton instance
ollama_service = OllamaService()
