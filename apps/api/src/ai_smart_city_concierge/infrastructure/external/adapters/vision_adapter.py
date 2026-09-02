"""
Vision AI Service Adapters
"""
from abc import ABC, abstractmethod
from typing import Any

from ....application.ports.external_services import VisionAIServicePort


@dataclass
class ImageAnalysisResult:
    """Image analysis result"""
    description: str
    objects: list[dict[str, Any]]
    tags: list[str]
    confidence: float


@dataclass
class ImageClassificationResult:
    """Image classification result"""
    categories: dict[str, float]


class BaseVisionAIAdapter(VisionAIServicePort, ABC):
    """Base vision AI adapter"""

    @abstractmethod
    async def _analyze_image_request(
        self,
        image_data: bytes,
        prompt: str | None,
    ) -> ImageAnalysisResult:
        """Analyze image request"""
        pass

    @abstractmethod
    async def _generate_embedding_request(self, image_data: bytes) -> list[float]:
        """Generate image embedding request"""
        pass

    @abstractmethod
    async def _classify_image_request(
        self,
        image_data: bytes,
        categories: list[str],
    ) -> ImageClassificationResult:
        """Classify image request"""
        pass

    async def analyze_image(
        self,
        image_data: bytes,
        prompt: str | None = None,
    ) -> dict[str, Any]:
        """Analyze image"""
        result = await self._analyze_image_request(image_data, prompt)
        return {
            "description": result.description,
            "objects": result.objects,
            "tags": result.tags,
            "confidence": result.confidence,
        }

    async def generate_embedding(self, image_data: bytes) -> list[float]:
        """Generate image embedding"""
        return await self._generate_embedding_request(image_data)

    async def classify_image(
        self,
        image_data: bytes,
        categories: list[str],
    ) -> dict[str, float]:
        """Classify image into categories"""
        result = await self._classify_image_request(image_data, categories)
        return result.categories


class CLIPAdapter(BaseVisionAIAdapter):
    """CLIP (Contrastive Language-Image Pre-training) adapter (local)"""

    def __init__(self, model_name: str = "openai/clip-vit-base-patch32", device: str = "cpu"):
        self.model_name = model_name
        self.device = device
        self._model = None
        self._processor = None

    async def _load_model(self):
        if self._model is None:
            from transformers import CLIPModel, CLIPProcessor

            self._model = CLIPModel.from_pretrained(self.model_name).to(self.device)
            self._processor = CLIPProcessor.from_pretrained(self.model_name)
            self._model.eval()

    async def _analyze_image_request(
        self,
        image_data: bytes,
        prompt: str | None,
    ) -> ImageAnalysisResult:
        await self._load_model()
        import io

        import torch
        from PIL import Image

        image = Image.open(io.BytesIO(image_data)).convert("RGB")

        if prompt:
            # Use text prompt for analysis
            inputs = self._processor(
                text=[prompt],
                images=image,
                return_tensors="pt",
                padding=True,
            ).to(self.device)

            with torch.no_grad():
                outputs = self._model(**inputs)
                logits_per_image = outputs.logits_per_image
                probs = logits_per_image.softmax(dim=1)

            return ImageAnalysisResult(
                description=prompt,
                objects=[],
                tags=[prompt],
                confidence=probs[0][0].item(),
            )
        else:
            # General image analysis - return basic info
            return ImageAnalysisResult(
                description="Image analyzed with CLIP",
                objects=[],
                tags=[],
                confidence=1.0,
            )

    async def _generate_embedding_request(self, image_data: bytes) -> list[float]:
        await self._load_model()
        import io

        import torch
        from PIL import Image

        image = Image.open(io.BytesIO(image_data)).convert("RGB")

        inputs = self._processor(images=image, return_tensors="pt").to(self.device)

        with torch.no_grad():
            image_features = self._model.get_image_features(**inputs)
            embedding = image_features.cpu().numpy()[0]

        return embedding.tolist()

    async def _classify_image_request(
        self,
        image_data: bytes,
        categories: list[str],
    ) -> ImageClassificationResult:
        await self._load_model()
        import io

        import torch
        from PIL import Image

        image = Image.open(io.BytesIO(image_data)).convert("RGB")

        inputs = self._processor(
            text=categories,
            images=image,
            return_tensors="pt",
            padding=True,
        ).to(self.device)

        with torch.no_grad():
            outputs = self._model(**inputs)
            logits_per_image = outputs.logits_per_image
            probs = logits_per_image.softmax(dim=1)

        categories_dict = {
            category: prob.item()
            for category, prob in zip(categories, probs[0], strict=False)
        }

        return ImageClassificationResult(categories=categories_dict)


class GPT4VisionAdapter(BaseVisionAIAdapter):
    """GPT-4 Vision adapter (OpenAI)"""

    def __init__(self, api_key: str, model: str = "gpt-4-vision-preview"):
        self.api_key = api_key
        self.model = model
        self._client = None

    async def _get_client(self):
        if self._client is None:
            from openai import AsyncOpenAI
            self._client = AsyncOpenAI(api_key=self.api_key)
        return self._client

    async def _analyze_image_request(
        self,
        image_data: bytes,
        prompt: str | None,
    ) -> ImageAnalysisResult:
        client = await self._get_client()

        import base64

        base64_image = base64.b64encode(image_data).decode('utf-8')

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt or "Describe this image in detail."},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}",
                            "detail": "high",
                        },
                    },
                ],
            },
        ]

        response = await client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=1000,
        )

        return ImageAnalysisResult(
            description=response.choices[0].message.content,
            objects=[],
            tags=[],
            confidence=1.0,
        )

    async def _generate_embedding_request(self, image_data: bytes) -> list[float]:
        # GPT-4V doesn't provide embeddings directly
        # Would need to use a separate embedding model
        return []

    async def _classify_image_request(
        self,
        image_data: bytes,
        categories: list[str],
    ) -> ImageClassificationResult:
        client = await self._get_client()

        import base64

        base64_image = base64.b64encode(image_data).decode('utf-8')

        prompt = f"Classify this image into one of these categories: {', '.join(categories)}. Return only the category name and confidence score as JSON."

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}",
                            "detail": "high",
                        },
                    },
                ],
            },
        ]

        response = await client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=500,
        )

        import json
        try:
            result = json.loads(response.choices[0].message.content)
            return ImageClassificationResult(categories=result)
        except:
            return ImageClassificationResult(categories={})


class GoogleVisionAdapter(BaseVisionAIAdapter):
    """Google Cloud Vision API adapter"""

    def __init__(self, credentials_path: str | None = None):
        self.credentials_path = credentials_path
        self._client = None

    async def _get_client(self):
        if self._client is None:
            from google.cloud import vision
            if self.credentials_path:
                self._client = vision.ImageAnnotatorClient.from_service_account_file(self.credentials_path)
            else:
                self._client = vision.ImageAnnotatorClient()
        return self._client

    async def _analyze_image_request(
        self,
        image_data: bytes,
        prompt: str | None,
    ) -> ImageAnalysisResult:
        client = await self._get_client()

        from google.cloud import vision

        image = vision.Image(content=image_data)

        # Label detection
        label_response = client.label_detection(image=image)
        labels = [label.description for label in label_response.label_annotations]

        # Object detection
        object_response = client.object_localization(image=image)
        objects = [
            {
                "name": obj.name,
                "confidence": obj.score,
                "bounding_box": {
                    "x": obj.bounding_poly.normalized_vertices[0].x,
                    "y": obj.bounding_poly.normalized_vertices[0].y,
                    "width": obj.bounding_poly.normalized_vertices[1].x - obj.bounding_poly.normalized_vertices[0].x,
                    "height": obj.bounding_poly.normalized_vertices[2].y - obj.bounding_poly.normalized_vertices[0].y,
                },
            }
            for obj in object_response.localized_object_annotations
        ]

        # Text detection
        text_response = client.text_detection(image=image)
        texts = [text.description for text in text_response.text_annotations]

        description = f"Labels: {', '.join(labels[:10])}. Objects: {', '.join([o['name'] for o in objects[:5]])}."
        if texts:
            description += f" Text: {texts[0][:200]}"

        return ImageAnalysisResult(
            description=description,
            objects=objects,
            tags=labels,
            confidence=sum(l.score for l in label_response.label_annotations[:5]) / 5 if label_response.label_annotations else 0,
        )

    async def _generate_embedding_request(self, image_data: bytes) -> list[float]:
        # Google Vision doesn't provide embeddings directly
        return []

    async def _classify_image_request(
        self,
        image_data: bytes,
        categories: list[str],
    ) -> ImageClassificationResult:
        # Use label detection for classification
        client = await self._get_client()

        from google.cloud import vision

        image = vision.Image(content=image_data)
        client.label_detection(image=image)

        categories_dict = {}
        for label in label_response.label_annotations:
            if label.description in categories:
                categories_dict[label.description] = label.score

        return ImageClassificationResult(categories=categories_dict)


class AzureVisionAdapter(BaseVisionAIAdapter):
    """Azure Computer Vision adapter"""

    def __init__(self, subscription_key: str, endpoint: str):
        self.subscription_key = subscription_key
        self.endpoint = endpoint
        self._client = None

    async def _get_client(self):
        if self._client is None:
            from azure.cognitiveservices.vision.computervision import ComputerVisionClient
            from msrest.authentication import CognitiveServicesCredentials
            self._client = ComputerVisionClient(
                self.endpoint,
                CognitiveServicesCredentials(self.subscription_key),
            )
        return self._client

    async def _analyze_image_request(
        self,
        image_data: bytes,
        prompt: str | None,
    ) -> ImageAnalysisResult:
        client = await self._get_client()

        import io

        image_stream = io.BytesIO(image_data)

        # Analyze image
        analysis = client.analyze_image_in_stream(
            image_stream,
            visual_features=[
                "Categories", "Tags", "Description", "Objects", "Faces",
            ],
        )

        tags = [tag.name for tag in analysis.tags]
        objects = [
            {
                "name": obj.object_property,
                "confidence": obj.confidence,
                "bounding_box": {
                    "x": obj.rectangle.x,
                    "y": obj.rectangle.y,
                    "width": obj.rectangle.w,
                    "height": obj.rectangle.h,
                },
            }
            for obj in analysis.objects
        ]

        description = analysis.description.captions[0].text if analysis.description.captions else ""

        return ImageAnalysisResult(
            description=description,
            objects=objects,
            tags=tags,
            confidence=analysis.description.captions[0].confidence if analysis.description.captions else 0,
        )

    async def _generate_embedding_request(self, image_data: bytes) -> list[float]:
        # Azure Computer Vision doesn't provide embeddings directly
        return []

    async def _classify_image_request(
        self,
        image_data: bytes,
        categories: list[str],
    ) -> ImageClassificationResult:
        client = await self._get_client()

        import io

        image_stream = io.BytesIO(image_data)

        analysis = client.analyze_image_in_stream(
            image_stream,
            visual_features=["Categories"],
        )

        categories_dict = {}
        for category in analysis.categories:
            if category.name in categories:
                categories_dict[category.name] = category.score

        return ImageClassificationResult(categories=categories_dict)
