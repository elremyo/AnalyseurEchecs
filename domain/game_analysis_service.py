from dataclasses import dataclass
from typing import List, Optional, Tuple, Any, Callable
import pandas as pd
import streamlit as st
import chess
from engine.analysis import InvalidPgnError, analyze_game, find_key_moments, get_moves_from_pgn
from utils.pgn_parser import parse_pgn_meta
from domain.analyzed_move import AnalyzedMove


@dataclass
class AnalysisResult:
    """Résultat complet d'une analyse de partie."""
    analysis: List[AnalyzedMove]
    white_name: str
    black_name: str
    pgn_meta: Any
    key_moments: List[Any]
    winner: Optional[str] = None
    analysis_df: Optional[pd.DataFrame] = None
    quality_recap: Optional[pd.DataFrame] = None
    user_color: Optional[str] = None
    determinants_message: Optional[str] = None
    critiques_message: Optional[str] = None


@dataclass
class AnalysisError:
    """Erreurs d'analyse typées."""
    message: str
    error_type: str = "invalid_pgn"  # "invalid_pgn", "analysis_error", "validation_error"


class GameAnalysisService:
    """Service métier pur pour l'analyse de parties d'échecs."""
    
    def __init__(self, stockfish_path: str, book_path: str):
        self.stockfish_path = stockfish_path
        self.book_path = book_path
    
    @staticmethod
    @st.cache_data
    def _get_moves_from_pgn_cached(pgn_text: str) -> list[chess.Move]:
        """Version cachée de get_moves_from_pgn pour la couche UI."""
        return get_moves_from_pgn(pgn_text)
    
    def analyze_game(
        self,
        pgn: str,
        user_depth: int,
        compute_threats: bool = False,
        key_moments_threshold: int = 500,
        min_gap_between_moments: int = 2,
        username: str = "Vous",
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> Tuple[Optional[AnalysisResult], Optional[AnalysisError]]:
        """
        Analyse une partie et retourne le résultat ou une erreur.
        
        Returns:
            Tuple[Optional[AnalysisResult], Optional[AnalysisError]]: 
            (résultat, erreur) - exactement un des deux est non-None
        """
        # Validation input
        if not pgn or not pgn.strip():
            return None, AnalysisError("PGN vide", "validation_error")
        
        try:
            # Analyse du moteur
            analysis, white_name, black_name = analyze_game(
                pgn, user_depth, self.stockfish_path, self.book_path,
                compute_threats=compute_threats,
                progress_callback=progress_callback
            )
            
            # Traitement métier
            pgn_meta = parse_pgn_meta(pgn)
            key_moments = find_key_moments(
                analysis, 
                threshold=key_moments_threshold,
                min_gap_between_moments=min_gap_between_moments,
                winner=pgn_meta.winner
            )
            
            # Calcul de la couleur utilisateur et des messages précalculés
            username = getattr(st.session_state, 'username', 'Vous') if 'st' in globals() else 'Vous'
            user_color = "white" if username.lower() == white_name.lower() else "black"
            
            # Calcul des messages pour les key moments
            determinants_message = None
            critiques_message = None
            
            if pgn_meta.winner:
                if pgn_meta.winner == user_color:
                    determinants_message = "✅ **Tu gagnes la partie ici :**"
                    critiques_message = "⚠️ **Tu as failli tout perdre ici :**"
                else:
                    determinants_message = "❌ **Tu perds la partie ici :**"
                    critiques_message = "💥 **Tu aurais pu gagner ici :**"
            
            # Création du DataFrame et précalcul du GroupBy
            analysis_df = pd.DataFrame(analysis)
            analysis_df["_side"] = ["W" if i % 2 == 0 else "B" for i in range(len(analysis_df))]
            quality_recap = (
                analysis_df.groupby(["quality", "_side"])
                .size()
                .unstack(fill_value=0)
                .reindex(columns=["W", "B"], fill_value=0)
                .reindex(index=[
                    #"Brillant", 
                    #"Critique", 
                    "Meilleur", "Excellent", "Bon",
                    "Imprécision", "Erreur", "Gaffe", "Théorique"
                ], fill_value=0)
            )
            
            result = AnalysisResult(
                analysis=analysis,
                white_name=white_name,
                black_name=black_name,
                pgn_meta=pgn_meta,
                key_moments=key_moments,
                winner=pgn_meta.winner,
                analysis_df=analysis_df,
                quality_recap=quality_recap,
                user_color=user_color,
                determinants_message=determinants_message,
                critiques_message=critiques_message
            )
            
            return result, None
            
        except InvalidPgnError as err:
            return None, AnalysisError(str(err), "invalid_pgn")
        except Exception as err:
            return None, AnalysisError(f"Erreur : {err}", "analysis_error")
