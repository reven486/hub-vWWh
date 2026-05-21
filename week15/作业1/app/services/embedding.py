import torch
import numpy as np
from PIL import Image
from functools import lru_cache
from transformers import AutoTokenizer, AutoModel, CLIPProcessor, CLIPModel
from app.core.config import get_settings


@lru_cache(maxsize=1)
def _load_bge():
    settings = get_settings()
    cfg = settings.models.bge
    tokenizer = AutoTokenizer.from_pretrained(cfg.model_name)
    model = AutoModel.from_pretrained(cfg.model_name).to(cfg.device)
    model.eval()
    return tokenizer, model, cfg.device


@lru_cache(maxsize=1)
def _load_clip():
    settings = get_settings()
    cfg = settings.models.clip
    processor = CLIPProcessor.from_pretrained(cfg.model_name)
    model = CLIPModel.from_pretrained(cfg.model_name).to(cfg.device)
    model.eval()
    return processor, model, cfg.device


def embed_text(texts: list[str]) -> list[list[float]]:
    tokenizer, model, device = _load_bge()
    encoded = tokenizer(texts, padding=True, truncation=True, max_length=512, return_tensors="pt")
    encoded = {k: v.to(device) for k, v in encoded.items()}
    with torch.no_grad():
        output = model(**encoded)
        embeddings = output.last_hidden_state[:, 0, :]  # CLS token
        embeddings = torch.nn.functional.normalize(embeddings, dim=-1)
    return embeddings.cpu().numpy().tolist()


def embed_single_text(text: str) -> list[float]:
    return embed_text([text])[0]


def embed_images(images: list[Image.Image]) -> list[list[float]]:
    processor, model, device = _load_clip()
    inputs = processor(images=images, return_tensors="pt", padding=True)
    inputs = {k: v.to(device) for k, v in inputs.items()}
    with torch.no_grad():
        features = model.get_image_features(**inputs)
        features = torch.nn.functional.normalize(features, dim=-1)
    return features.cpu().numpy().tolist()


def embed_text_clip(texts: list[str]) -> list[list[float]]:
    """Embed texts using CLIP for cross-modal image retrieval."""
    processor, model, device = _load_clip()
    inputs = processor(text=texts, return_tensors="pt", padding=True, truncation=True)
    inputs = {k: v.to(device) for k, v in inputs.items()}
    with torch.no_grad():
        features = model.get_text_features(**inputs)
        features = torch.nn.functional.normalize(features, dim=-1)
    return features.cpu().numpy().tolist()
