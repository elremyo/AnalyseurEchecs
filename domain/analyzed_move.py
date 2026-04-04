from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class AnalyzedMove:
    """Dataclass représentant l'analyse d'un coup d'échecs.
    
    Remplace les dicts non-typés utilisés précédemment pour l'analyse,
    en fournissant un schéma strict et des accès typés.
    """
    coup: str
    quality: str
    eval: int
    raw_eval: Dict[str, Any]
    best_move: str
    best_move_uci: str
    is_best: bool
    is_theoretical: bool
    threats: List[str] = field(default_factory=list)
