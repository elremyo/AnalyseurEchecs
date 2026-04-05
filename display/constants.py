from utils.assets import assets_path
import os

board_size = 800  # in pixels

# Constants for board rendering
SQUARE_SIZE_PX = 45.7
BOARD_MARGIN_PX = 10
QUALITY_ICON_SIZE = 20

quality_images = {
    "Théorique": os.path.join(assets_path, "theorique.png"),
    "Gaffe": os.path.join(assets_path, "gaffe.png"),
    "Erreur": os.path.join(assets_path, "erreur.png"),
    "Imprécision": os.path.join(assets_path, "imprecision.png"),
    "Bon": os.path.join(assets_path, "bon.png"),
    "Excellent": os.path.join(assets_path, "excellent.png"),
    "Meilleur": os.path.join(assets_path, "meilleur.png"),
    "Critique": os.path.join(assets_path, "tres_bon.png"),
    "Brillant": os.path.join(assets_path, "brillant.png")
}

quality_colors = {
    "Théorique": "#a88764",
    "Gaffe": "#c93233",
    "Erreur": "#dc8c2a",
    "Imprécision": "#e8b443",
    "Bon": "#78af8b",
    "Excellent": "#67ac49",
    "Meilleur": "#98bc49",
    "Critique": "#4c8caf",
    "Brillant": "#1baa9b"
}

quality_board_colors = {
    "Théorique": ("#ccb08c", "#ae8763"),
    "Gaffe": ("#df8973", "#c0604a"),
    "Erreur": ("#e9b373", "#cc8a49"),
    "Imprécision": ("#f2cd7f", "#d4a456"),
    "Bon": ("#c4c49f", "#a79c77"),
    "Excellent": ("#c5ca80", "#a8a257"),
    "Meilleur": ("#c5ca80", "#a8a257"),
    "Critique": ("#a7b2b2", "#8a8a8a"),
    "Brillant": ("#1baa9b", "#1baa9b")
}

# Board colors
BOARD_COLORS = {
    "square_light": "#ebecd0",
    "square_dark": "#739552",
    "arrow": "#ff0000",
    "margin": "#181818", # Same as background in config.toml
    "best_arrow": "#98bc499e",
    "threat_arrow": "#c02424b9",
    "default_light": "#ffffff",
    "default_dark": "#000000"
}