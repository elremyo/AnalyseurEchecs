import random

famous_games = [
    {
        "title": "Immortal Game (Anderssen vs. Kieseritzky, 1851)",
        "player_white": "Adolf Anderssen",
        "player_black": "Lionel Kieseritzky",
        "year": 1851,
        "pgn": """
[Event "Immortal Game"]
[Site "London"]
[Date "1851.06.21"]
[Round "?"]
[White "Adolf Anderssen"]
[Black "Lionel Kieseritzky"]
[Result "1-0"]

1.e4 e5 2.f4 exf4 3.Bc4 Qh4+ 4.Kf1 b5 5.Bxb5 Nf6 6.Nf3 Qh6 7.d3 Nh5 8.Nh4 Qg5
9.Nf5 c6 10.g4 Nf6 11.Rg1 cxb5 12.h4 Qg6 13.h5 Qg5 14.Qf3 Ng8 15.Bxf4 Qf6
16.Nc3 Bc5 17.Nd5 Qxb2 18.Bd6 Bxg1 19.e5 Qxa1+ 20.Ke2 Na6 21.Nxg7+ Kd8
22.Qf6+ Nxf6 23.Be7# 1-0
"""
    },
    {
        "title": "Opera Game (Morphy vs. Duke & Count, 1858)",
        "player_white": "Paul Morphy",
        "player_black": "Duke of Brunswick & Count Isouard",
        "year": 1858,
        "pgn": """
[Event "Opera Game"]
[Site "Paris"]
[Date "1858.??.??"]
[Round "?"]
[White "Paul Morphy"]
[Black "Duke of Brunswick & Count Isouard"]
[Result "1-0"]

1.e4 e5 2.Nf3 d6 3.d4 Bg4 4.dxe5 Bxf3 5.Qxf3 dxe5 6.Bc4 Nf6 7.Qb3 Qe7 8.Nc3 c6
9.Bg5 b5 10.Nxb5 cxb5 11.Bxb5+ Nbd7 12.O-O-O Rd8 13.Rxd7 Rxd7 14.Rd1 Qe6
15.Bxd7+ Nxd7 16.Qb8+ Nxb8 17.Rd8# 1-0
"""
    },
    {
        "title": "Fischer vs. Spassky - Game 6, 1972",
        "player_white": "Bobby Fischer",
        "player_black": "Boris Spassky",
        "year": 1972,
        "pgn": """
[Event "World Championship"]
[Site "Reykjavik"]
[Date "1972.07.23"]
[Round "6"]
[White "Robert James Fischer"]
[Black "Boris Spassky"]
[Result "1-0"]

1.c4 e6 2.Nc3 d5 3.d4 Nf6 4.Bg5 Be7 5.e3 O-O 6.Nf3 h6 7.Bh4 b6 8.cxd5 Nxd5
9.Bxe7 Qxe7 10.Nxd5 exd5 11.Rc1 Be6 12.Qa4 c5 13.Qa3 Rc8 14.Bb5 a6 15.dxc5
bxc5 16.O-O Ra7 17.Be2 Nd7 18.Nd4 Qf8 19.Nxe6 fxe6 20.e4 d4 21.f4 Qe7
22.e5 Rb8 23.Bc4 Kh8 24.Qh3 Nf8 25.b3 a5 26.a4 Rd7 27.Rf3 Rbd8 28.Rd1 Qf7
29.f5 Qe8 30.f6 Qg6 31.Bd3 Qg5 32.Re1 Qd2 33.Ref1 Qg5 34.Re1 Qd2 35.Ref1
Qg5 36.Rg3 Qxe5 37.fxg7+ Rxg7 38.Qxh6+ Nh7 39.Rxg7 Qxg7 40.Qxe6 Rg8
41.g3 Qg5 42.Rf4 Qh5 43.Be2 Qg5 44.Bd3 Qh5 45.Kg2 Re8 46.Qd7 Nf8 47.Qd6
Kg8 48.Bc4+ Kg7 49.Qf6+ Kh7 50.Rh4 Qxh4 51.Qxh4+ Kg7 52.Qf6+ Kh7
53.Bd3+ Kg8 54.Bc4+ 1-0
"""
    }
    ,
    {
        "title": "Deep Blue vs. Kasparov - Game 6, 1997",
        "player_white": "Deep Blue",
        "player_black": "Garry Kasparov",
        "year": 1997,
        "pgn": """
[Event "IBM Man-Machine"]
[Site "New York, NY USA"]
[Date "1997.05.11"]
[EventDate "?"]
[Round "6"]
[Result "1-0"]
[White "Deep Blue (Computer)"]
[Black "Garry Kasparov"]
[ECO "B17"]
[WhiteElo "?"]
[BlackElo "?"]
[PlyCount "37"]

1.e4 c6 2.d4 d5 3.Nc3 dxe4 4.Nxe4 Nd7 5.Ng5 Ngf6 6.Bd3 e6
7.N1f3 h6 8.Nxe6 Qe7 9.O-O fxe6 10.Bg6+ Kd8 11.Bf4 b5 12.a4
Bb7 13.Re1 Nd5 14.Bg3 Kc8 15.axb5 cxb5 16.Qd3 Bc6 17.Bf5 exf5
18.Rxe7 Bxe7 19.c4 1-0
        """
    }
]


def get_random_game():
    return random.choice(famous_games)