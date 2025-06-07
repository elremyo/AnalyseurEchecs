import os
import platform

current_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.abspath(os.path.join(current_dir, '..'))
assets_path = os.path.join(base_dir, "assets")
engine_path = os.path.join(base_dir, 'engine')




if platform.system() == "Windows":
    stockfish_path = os.path.join(engine_path, 'stockfish', 'stockfish-windows-x86-64-avx2.exe')
else:
    stockfish_path = "/usr/games/stockfish"


book_path = os.path.join(assets_path, "performance.bin")


def can_use_clipboard():
    try:
        import pyperclip
        test = pyperclip.paste()
        return True
    except:
        return False
