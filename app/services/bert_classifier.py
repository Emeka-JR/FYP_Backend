from transformers import BertTokenizerFast, BertForSequenceClassification
import torch
from typing import Tuple
import os
from app.core.config import get_settings

settings = get_settings()

class BertNewsClassifier:
    def __init__(self):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model_path = os.path.join('ml', 'models', 'bert_model')
        self.tokenizer_path = os.path.join('ml', 'models', 'bert_tokenizer')
        
        # Load tokenizer and model
        self.tokenizer = BertTokenizerFast.from_pretrained(self.tokenizer_path)
        self.model = BertForSequenceClassification.from_pretrained(self.model_path)
        self.model.to(self.device)
        self.model.eval()
        
        # Categories from settings
        self.categories = settings.NEWS_CATEGORIES

    async def classify_text(self, text: str) -> Tuple[str, float]:
        # Tokenize text
        inputs = self.tokenizer(
            text,
            truncation=True,
            max_length=512,
            padding='max_length',
            return_tensors='pt'
        )
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        # Get prediction
        with torch.no_grad():
            outputs = self.model(**inputs)
            probabilities = torch.softmax(outputs.logits, dim=1)
            prediction = torch.argmax(probabilities, dim=1)
            confidence_score = torch.max(probabilities).item()
        
        predicted_category = self.categories[prediction.item()]
        return predicted_category, confidence_score

# Create a singleton instance
classifier = BertNewsClassifier() 