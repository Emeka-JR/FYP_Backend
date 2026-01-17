import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import pickle
from typing import Dict, Any
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 👉 Your Hugging Face model repository
HF_MODEL_REPO = "Emeka-JR/FYP_Model"

class ModelService:
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = None
        self.tokenizer = None
        self.label_encoder = None
        self.load_model()

    def load_model(self):
        try:
            logger.info("Loading model from Hugging Face Hub...")

            # Load tokenizer & model from Hugging Face
            self.tokenizer = AutoTokenizer.from_pretrained(HF_MODEL_REPO)
            self.model = AutoModelForSequenceClassification.from_pretrained(
                HF_MODEL_REPO
            )

            # Move model to device (CPU/GPU)
            self.model.to(self.device)
            self.model.eval()

            # Load local label encoder (small file, kept in backend)
            base_dir = os.path.dirname(os.path.abspath(__file__))
            label_encoder_path = os.path.join(base_dir, "label_encoder.pkl")


            if not os.path.exists(label_encoder_path):
                raise FileNotFoundError("label_encoder.pkl not found")

            with open(label_encoder_path, "rb") as f:
                self.label_encoder = pickle.load(f)

            logger.info("Model and label encoder loaded successfully")

        except Exception as e:
            logger.error(f"Model loading failed: {e}")
            raise RuntimeError("Model service initialization failed")

    async def predict(self, text: str) -> Dict[str, Any]:
        if not text.strip():
            raise ValueError("Input text cannot be empty")

        inputs = self.tokenizer(
            text,
            truncation=True,
            padding=True,
            max_length=512,
            return_tensors="pt"
        ).to(self.device)

        with torch.no_grad():
            outputs = self.model(**inputs)
            probs = torch.softmax(outputs.logits, dim=-1)
            pred_idx = torch.argmax(probs, dim=-1).item()
            confidence = probs[0][pred_idx].item()

        category = self.label_encoder.inverse_transform([pred_idx])[0]

        return {
            "category": category,
            "confidence": confidence
        }

# Singleton model service
model_service = ModelService()
