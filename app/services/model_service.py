import torch
from transformers import BertTokenizerFast, BertForSequenceClassification
import pickle
from typing import Dict, Any
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ModelService:
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.label_encoder = None
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        try:
            self.load_model()
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            raise

    def load_model(self):
        """Load the trained model, tokenizer, and label encoder"""
        try:
            # Get the absolute path to the models directory
            current_dir = os.path.dirname(os.path.abspath(__file__))
            backend_dir = os.path.dirname(os.path.dirname(current_dir))
            project_root = os.path.dirname(backend_dir)
            model_path = os.path.join(project_root, 'models')
            
            logger.info(f"Loading model from: {model_path}")
            
            # Load label encoder first to get number of classes
            label_encoder_path = os.path.join(model_path, 'label_encoder.pkl')
            if not os.path.exists(label_encoder_path):
                raise FileNotFoundError(f"Label encoder file not found: {label_encoder_path}")
            
            with open(label_encoder_path, 'rb') as f:
                self.label_encoder = pickle.load(f)
            
            num_labels = len(self.label_encoder.classes_)
            logger.info(f"Number of labels: {num_labels}")
            
            # Load model
            model_dir = os.path.join(model_path, 'bert_model')
            if not os.path.exists(model_dir):
                raise FileNotFoundError(f"Model directory not found: {model_dir}")
            
            # Load the model configuration
            config_path = os.path.join(model_dir, 'config.json')
            if not os.path.exists(config_path):
                raise FileNotFoundError(f"Model config not found: {config_path}")
            
            # Load the model weights
            weights_path = os.path.join(model_dir, 'model.safetensors')
            if not os.path.exists(weights_path):
                raise FileNotFoundError(f"Model weights not found: {weights_path}")
            
            self.model = BertForSequenceClassification.from_pretrained(
                model_dir,
                local_files_only=True,
                num_labels=num_labels
            )
            self.model.to(self.device)
            self.model.eval()

            # Load tokenizer
            tokenizer_dir = os.path.join(model_path, 'bert_tokenizer')
            if not os.path.exists(tokenizer_dir):
                raise FileNotFoundError(f"Tokenizer directory not found: {tokenizer_dir}")
            
            self.tokenizer = BertTokenizerFast.from_pretrained(tokenizer_dir, local_files_only=True)
                
            logger.info("Model, tokenizer, and label encoder loaded successfully")
            
        except Exception as e:
            logger.error(f"Error in load_model: {str(e)}")
            raise

    async def predict(self, text: str) -> Dict[str, Any]:
        """Make prediction for a given text"""
        if not text:
            raise ValueError("Input text cannot be empty")
            
        if not self.model or not self.tokenizer or not self.label_encoder:
            raise RuntimeError("Model components not properly initialized")
            
        try:
            logger.info(f"Processing text: {text[:100]}...")  # Log first 100 chars
            
            # Prepare input
            inputs = self.tokenizer(
                text,
                truncation=True,
                padding=True,
                max_length=512,
                return_tensors="pt"
            ).to(self.device)
            
            logger.info("Input prepared successfully")

            # Make prediction
            with torch.no_grad():
                outputs = self.model(**inputs)
                predictions = torch.softmax(outputs.logits, dim=-1)
                predicted_class = torch.argmax(predictions, dim=-1).item()
                confidence = predictions[0][predicted_class].item()
                
            logger.info(f"Raw prediction - class: {predicted_class}, confidence: {confidence}")

            # Get category name
            category = self.label_encoder.inverse_transform([predicted_class])[0]
            logger.info(f"Predicted category: {category}")

            return {
                "category": category,
                "confidence": confidence,
                "all_probabilities": {
                    cat: float(prob) for cat, prob in zip(
                        self.label_encoder.classes_,
                        predictions[0].cpu().numpy()
                    )
                }
            }
        except Exception as e:
            logger.error(f"Error in predict: {str(e)}")
            raise

# Create singleton instance
model_service = ModelService() 