import os
from stockfish import Stockfish

# S'assurer que le moteur est exécutable
os.system("chmod +x ./bin/stockfish")

# Initialiser Stockfish
stockfish = Stockfish(path="./bin/stockfish", depth=15)

# Tester
print("Best move from start position:", stockfish.get_best_move())
