import os
import logging
from typing import Dict, Any

import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

HF_MODEL_REPO = "Emeka-JR/FYP_Model"
HF_API_URL = f"https://api-inference.huggingface.co/models/{HF_MODEL_REPO}"


class ModelService:
    def __init__(self):
        self.api_token = os.getenv("HF_API_TOKEN")
        if not self.api_token:
            logger.warning("HF_API_TOKEN is not set. Model predictions will fail.")
        else:
            logger.info("ModelService configured to use Hugging Face Inference API.")

    async def predict(self, text: str) -> Dict[str, Any]:
        if not text or not text.strip():
            raise ValueError("Input text cannot be empty")

        if not self.api_token:
            raise RuntimeError("HF_API_TOKEN is not configured on the server")

        headers = {
            "Authorization": f"Bearer {self.api_token}"
        }
        payload = {
            "inputs": text
        }

        try:
            logger.info("Sending request to Hugging Face Inference API...")
            response = requests.post(HF_API_URL, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()

            # Expected format: [[{"label": "...", "score": 0.95}, ...]]
            if isinstance(data, list) and len(data) > 0 and isinstance(data[0], list):
                best = sorted(data[0], key=lambda x: x["score"], reverse=True)[0]
                category = best["label"]
                confidence = float(best["score"])
            else:
                raise RuntimeError(f"Unexpected response format from HF API: {data}")

            return {
                "category": category,
                "confidence": confidence
            }

        except Exception as e:
            logger.error(f"Error calling Hugging Face Inference API: {e}")
            raise RuntimeError("Failed to get prediction from model service")


model_service = ModelService()
