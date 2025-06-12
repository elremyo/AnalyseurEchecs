import random
import requests
import os

assets_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")


chess_gifs = [
    "https://gifdb.com/images/high/cute-cats-fighting-over-chess-game-zpyt9q36qznawkc1.webp",
    "https://gifdb.com/images/high/chess-checkmate-natasha-lyonne-yhuv4j4bowlr0e0k.webp",
    "https://gifdb.com/images/high/geri-patiently-waiting-for-chess-move-ndg4p71mvtzws11v.webp",
    "https://gifdb.com/images/high/adorable-naughty-white-cat-playing-chess-nq389mt672i78q5g.webp",
    "https://gifdb.com/images/high/irritated-gaston-flipping-chess-board-gz33tqpfln3ngc98.webp",
    "https://gifdb.com/images/high/chess-game-serious-shaun-the-sheep-grtxymygnde3puwc.webp",
    "https://gifdb.com/images/high/hot-lady-capturing-chess-piece-yag0u744l3uxum4q.webp",
    "https://gifdb.com/images/high/chubby-cat-claiming-chess-piece-nng3pl7e4kp7b8kb.webp",
    "https://media3.giphy.com/media/v1.Y2lkPTc5MGI3NjExaHpydjY5cW9iMXpmeDlidG41NTR3eDF6YnM2MHRxYW5uc2EwdzNhcCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/JuUWDI13JB0XK/giphy.gif",
    "https://media2.giphy.com/media/v1.Y2lkPTc5MGI3NjExMmY4bXk5dnhvODFocmdxNzltd29oN2RtdGJmcjk2cDA3ZHllMGVtdSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/6XlOzOgC5FTsk/giphy.gif"
]


def get_random_gif():
    for _ in range(3):  # on tente 3 fois
        gif = random.choice(chess_gifs)
        try:
            if requests.head(gif, timeout=3).status_code == 200:
                return gif
        except:
            continue
    return os.path.join(assets_path, 'checkmate_gif.gif')
