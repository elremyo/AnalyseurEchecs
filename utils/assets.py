import os
import base64


current_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.abspath(os.path.join(current_dir, '..'))
assets_path = os.path.join(base_dir, "assets")
engine_path = os.path.join(base_dir, 'engine')


stockfish_path = os.path.join(engine_path, 'stockfish', 'stockfish-windows-x86-64-avx2.exe')
book_path = os.path.join(assets_path, "performance.bin")

def img_to_base64(path):
    with open(path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode("utf-8")