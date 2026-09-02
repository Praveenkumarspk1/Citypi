"""
CLIP Vision AI Client
"""
import io
import os
from typing import Any

import torch
from PIL import Image
from transformers import CLIPModel, CLIPProcessor

from ...application.ports.external_services import VisionAIServicePort


class CLIPClient(VisionAIServicePort):
    """CLIP ViT-B/32 vision model client (local)"""

    def __init__(
        self,
        model_name: str = "openai/clip-vit-base-patch32",
        device: str | None = None,
        cache_dir: str | None = None,
    ):
        self.model_name = model_name
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.cache_dir = cache_dir or os.getenv("HF_HOME", os.path.expanduser("~/.cache/huggingface"))
        self._model: CLIPModel | None = None
        self._processor: CLIPProcessor | None = None
        self._embedding_dim = 512  # CLIP ViT-B/32 dimension

    def _get_model(self) -> CLIPModel:
        """Lazy load model"""
        if self._model is None:
            self._model = CLIPModel.from_pretrained(
                self.model_name,
                cache_dir=self.cache_dir,
            ).to(self.device)
            self._model.eval()
        return self._model

    def _get_processor(self) -> CLIPProcessor:
        """Lazy load processor"""
        if self._processor is None:
            self._processor = CLIPProcessor.from_pretrained(
                self.model_name,
                cache_dir=self.cache_dir,
            )
        return self._processor

    async def analyze_image(
        self,
        image_data: bytes,
        prompt: str | None = None,
    ) -> dict[str, Any]:
        """Analyze image with optional text prompt"""
        model = self._get_model()
        processor = self._get_processor()

        # Load image
        image = Image.open(io.BytesIO(image_data)).convert("RGB")

        if prompt:
            # Text-guided analysis
            inputs = processor(
                text=[prompt],
                images=image,
                return_tensors="pt",
                padding=True,
            ).to(self.device)

            with torch.no_grad():
                outputs = model(**inputs)
                logits_per_image = outputs.logits_per_image
                probs = logits_per_image.softmax(dim=1)

            return {
                "prompt": prompt,
                "probability": probs[0][0].item(),
                "description": f"Image matches '{prompt}' with {probs[0][0].item():.2%} confidence",
            }
        else:
            # General image analysis - return embeddings and basic info
            inputs = processor(images=image, return_tensors="pt").to(self.device)

            with torch.no_grad():
                image_features = model.get_image_features(**inputs)
                image_embedding = image_features / image_features.norm(dim=-1, keepdim=True)

            return {
                "embedding": image_embedding[0].cpu().tolist(),
                "dimension": self._embedding_dim,
                "image_size": image.size,
                "mode": image.mode,
            }

    async def generate_embedding(self, image_data: bytes) -> list[float]:
        """Generate image embedding"""
        model = self._get_model()
        processor = self._get_processor()

        image = Image.open(io.BytesIO(image_data)).convert("RGB")
        inputs = processor(images=image, return_tensors="pt").to(self.device)

        with torch.no_grad():
            image_features = model.get_image_features(**inputs)
            image_embedding = image_features / image_features.norm(dim=-1, keepdim=True)

        return image_embedding[0].cpu().tolist()

    async def classify_image(
        self,
        image_data: bytes,
        categories: list[str],
    ) -> dict[str, float]:
        """Classify image into provided categories"""
        model = self._get_model()
        processor = self._get_processor()

        image = Image.open(io.BytesIO(image_data)).convert("RGB")

        # Prepare text inputs for all categories
        text_inputs = processor(
            text=categories,
            return_tensors="pt",
            padding=True,
        ).to(self.device)

        image_inputs = processor(images=image, return_tensors="pt").to(self.device)

        with torch.no_grad():
            # Get text and image features
            text_features = model.get_text_features(**text_inputs)
            image_features = model.get_image_features(**image_inputs)

            # Normalize
            text_features = text_features / text_features.norm(dim=-1, keepdim=True)
            image_features = image_features / image_features.norm(dim=-1, keepdim=True)

            # Compute similarity
            similarity = (image_features @ text_features.T).softmax(dim=-1)

        results = {}
        for i, category in enumerate(categories):
            results[category] = similarity[0][i].item()

        return results

    async def text_embedding(self, text: str) -> list[float]:
        """Generate text embedding using CLIP text encoder"""
        model = self._get_model()
        processor = self._get_processor()

        inputs = processor(text=[text], return_tensors="pt", padding=True).to(self.device)

        with torch.no_grad():
            text_features = model.get_text_features(**inputs)
            text_embedding = text_features / text_features.norm(dim=-1, keepdim=True)

        return text_embedding[0].cpu().tolist()

    async def image_text_similarity(
        self,
        image_data: bytes,
        text: str,
    ) -> float:
        """Compute similarity between image and text"""
        model = self._get_model()
        processor = self._get_processor()

        image = Image.open(io.BytesIO(image_data)).convert("RGB")

        inputs = processor(
            text=[text],
            images=image,
            return_tensors="pt",
            padding=True,
        ).to(self.device)

        with torch.no_grad():
            outputs = model(**inputs)
            logits_per_image = outputs.logits_per_image
            probs = logits_per_image.softmax(dim=1)

        return probs[0][0].item()

    def get_model_info(self) -> dict[str, Any]:
        """Get model information"""
        return {
            "model_name": self.model_name,
            "device": self.device,
            "embedding_dimension": self._embedding_dim,
            "cache_dir": self.cache_dir,
        }
