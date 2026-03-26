import base64
import streamlit as st

from display.constants import quality_images


@st.cache_data
def load_quality_images_b64() -> dict[str, str]:
    """Charge et encode en base64 toutes les images de qualité. Résultat mis en cache."""
    result = {}
    for quality, path in quality_images.items():
        with open(path, "rb") as f:
            result[quality] = base64.b64encode(f.read()).decode("utf-8")
    return result