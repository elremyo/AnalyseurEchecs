import base64
import streamlit as st

from constants import QUALITY_IMAGES


@st.cache_resource
def load_quality_images_b64() -> dict[str, str]:
    """Charge et encode en base64 toutes les images de qualité. Résultat mis en cache."""
    result = {}
    for quality, path in QUALITY_IMAGES.items():
        with open(path, "rb") as f:
            result[quality] = base64.b64encode(f.read()).decode("utf-8")
    return result