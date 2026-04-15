import json
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Any, Callable
import pandas as pd
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
    accuracy_white: Optional[float] = None
    accuracy_black: Optional[float] = None
    game_id: Optional[str] = None


@dataclass
class AnalysisError:
    message: str
    error_type: str = "invalid_pgn"


# ---------------------------------------------------------------------------
# Helpers internes
# ---------------------------------------------------------------------------

_QUALITY_ORDER = ["Meilleur", "Excellent", "Bon", "Imprécision", "Erreur", "Gaffe", "Théorique"]


def _build_quality_recap(analysis: List[AnalyzedMove]) -> pd.DataFrame:
    rows = [{"quality": m.quality, "_side": "W" if i % 2 == 0 else "B"}
            for i, m in enumerate(analysis)]
    df = pd.DataFrame(rows) if rows else pd.DataFrame(columns=["quality", "_side"])
    return (
        df.groupby(["quality", "_side"])
        .size()
        .unstack(fill_value=0)
        .reindex(columns=["W", "B"], fill_value=0)
        .reindex(index=_QUALITY_ORDER, fill_value=0)
    )


def _build_analysis_df(analysis: List[AnalyzedMove]) -> pd.DataFrame:
    df = pd.DataFrame(analysis)
    if not df.empty:
        df["_side"] = ["W" if i % 2 == 0 else "B" for i in range(len(df))]
    return df


def _compute_accuracy(analysis: List[AnalyzedMove]) -> Tuple[Optional[float], Optional[float]]:
    white_accs = [m.accuracy for i, m in enumerate(analysis) if i % 2 == 0]
    black_accs = [m.accuracy for i, m in enumerate(analysis) if i % 2 == 1]
    acc_w = round(sum(white_accs) / len(white_accs), 1) if white_accs else None
    acc_b = round(sum(black_accs) / len(black_accs), 1) if black_accs else None
    return acc_w, acc_b


def _build_messages(pgn_meta, user_color: str) -> Tuple[Optional[str], Optional[str]]:
    if not pgn_meta.winner or pgn_meta.winner == "draw":
        return None, None
    if pgn_meta.winner == user_color:
        return "✅ **Tu gagnes la partie ici :**", "⚠️ **Tu as failli tout perdre ici :**"
    return "❌ **Tu perds la partie ici :**", "💥 **Tu aurais pu gagner ici :**"


def _extract_game_id(pgn_meta) -> Optional[str]:
    if not pgn_meta.link:
        return None
    segment = pgn_meta.link.rstrip("/").split("/")[-1]
    return segment or None


def _save_to_cache(game_id: str, depth: int, result: "AnalysisResult") -> None:
    """Persiste silencieusement le résultat en SQLite."""
    from utils.chesscom_cache import save_analysis
    move_rows = [
        {
            "game_id":        game_id,
            "move_index":     i,
            "coup":           m.coup,
            "quality":        m.quality,
            "eval_cp":        m.eval,
            "eval_type":      m.raw_eval.get("type", "cp"),
            "eval_value":     m.raw_eval.get("value", 0),
            "best_move_san":  m.best_move,
            "best_move_uci":  m.best_move_uci,
            "is_best":        int(m.is_best),
            "is_theoretical": int(m.is_theoretical),
            "accuracy_cp":    m.accuracy,
        }
        for i, m in enumerate(result.analysis)
    ]
    save_analysis(
        game_id=game_id,
        depth=depth,
        accuracy_white=result.accuracy_white,
        accuracy_black=result.accuracy_black,
        total_moves=len(result.analysis),
        quality_recap=result.quality_recap,
        key_moments_determinants=result.key_moments.get("moments_determinants", []),
        key_moments_critiques=result.key_moments.get("moments_critiques", []),
        winner=result.winner,
        move_rows=move_rows,
    )


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------

class GameAnalysisService:

    def __init__(self, stockfish_path: str, book_path: str):
        self.stockfish_path = stockfish_path
        self.book_path = book_path

    def analyze_game(
        self,
        pgn: str,
        user_depth: int,
        username: str = "Vous",
        compute_threats: bool = False,
        key_moments_threshold: int = 500,
        min_gap_between_moments: int = 2,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
    ) -> Tuple[Optional[AnalysisResult], Optional[AnalysisError]]:

        if not pgn or not pgn.strip():
            return None, AnalysisError("PGN vide", "validation_error")

        try:
            analysis, white_name, black_name = analyze_game(
                pgn, user_depth, self.stockfish_path, self.book_path,
                compute_threats=compute_threats,
                progress_callback=progress_callback,
            )
            pgn_meta       = parse_pgn_meta(pgn)
            key_moments    = find_key_moments(
                analysis,
                threshold=key_moments_threshold,
                min_gap_between_moments=min_gap_between_moments,
                winner=pgn_meta.winner,
            )
            user_color     = "white" if username.lower() == white_name.lower() else "black"
            det_msg, crit_msg = _build_messages(pgn_meta, user_color)
            analysis_df    = _build_analysis_df(analysis)
            quality_recap  = _build_quality_recap(analysis)
            acc_w, acc_b   = _compute_accuracy(analysis)
            game_id        = _extract_game_id(pgn_meta)

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
                determinants_message=det_msg,
                critiques_message=crit_msg,
                accuracy_white=acc_w,
                accuracy_black=acc_b,
                game_id=game_id,
            )

            # Persistence silencieuse
            if game_id:
                try:
                    _save_to_cache(game_id, user_depth, result)
                except Exception:
                    pass

            return result, None

        except InvalidPgnError as err:
            return None, AnalysisError(str(err), "invalid_pgn")
        except Exception as err:
            return None, AnalysisError(f"Erreur : {err}", "analysis_error")

    def load_from_cache(
        self,
        game_id: str,
        pgn: str,
        username: str,
    ) -> Tuple[Optional[AnalysisResult], Optional[AnalysisError]]:
        """Reconstruit un AnalysisResult depuis SQLite sans appeler Stockfish."""
        from utils.chesscom_cache import load_analysis_full, load_analysis_moves

        meta = load_analysis_full(game_id)
        if not meta:
            return None, AnalysisError("Cache manquant.", "cache_miss")

        rows = load_analysis_moves(game_id)
        if not rows:
            return None, AnalysisError("Coups absents du cache.", "cache_miss")

        analysis = [
            AnalyzedMove(
                coup=r["coup"],
                quality=r["quality"],
                eval=r["eval_cp"],
                raw_eval={"type": r["eval_type"], "value": r["eval_value"]},
                best_move=r["best_move_san"] or "",
                best_move_uci=r["best_move_uci"] or "",
                is_best=bool(r["is_best"]),
                is_theoretical=bool(r["is_theoretical"]),
                accuracy=r["accuracy_cp"] if r["accuracy_cp"] is not None else 100.0,
            )
            for r in rows
        ]

        pgn_meta   = parse_pgn_meta(pgn)
        user_color = "white" if username.lower() == pgn_meta.white.lower() else "black"
        det_msg, crit_msg = _build_messages(pgn_meta, user_color)

        key_moments = {
            "moments_determinants": json.loads(meta.get("key_moments_determinants") or "[]"),
            "moments_critiques":    json.loads(meta.get("key_moments_critiques")    or "[]"),
        }

        return AnalysisResult(
            analysis=analysis,
            white_name=pgn_meta.white,
            black_name=pgn_meta.black,
            pgn_meta=pgn_meta,
            key_moments=key_moments,
            winner=meta.get("winner"),
            analysis_df=_build_analysis_df(analysis),
            quality_recap=_build_quality_recap(analysis),
            user_color=user_color,
            determinants_message=det_msg,
            critiques_message=crit_msg,
            accuracy_white=meta.get("accuracy_white"),
            accuracy_black=meta.get("accuracy_black"),
            game_id=game_id,
        ), None

    def analyze_batch(
        self,
        username: str,
        limit: int,
        user_depth: int,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
    ) -> Tuple[int, int, List[str]]:
        """
        Analyse batch des N dernières parties non analysées.
        
        Args:
            username: Nom d'utilisateur Chess.com
            limit: Nombre maximum de parties à analyser
            user_depth: Profondeur d'analyse Stockfish
            progress_callback: Callback pour la progression (current, total, message)
            
        Returns:
            Tuple: (succès, échecs, liste des game_id analysés)
        """
        from utils.chesscom_cache import get_unanalyzed_games
        
        # Récupérer les parties non analysées
        unanalyzed_games = get_unanalyzed_games(username, limit)
        
        if not unanalyzed_games:
            return 0, 0, []
        
        success_count = 0
        error_count = 0
        analyzed_game_ids = []
        total_games = len(unanalyzed_games)
        
        for i, game in enumerate(unanalyzed_games, 1):
            game_id = game["game_id"]
            pgn = game.get("pgn", "")
            
            if progress_callback:
                progress_callback(i, total_games, f"Analyse de la partie {i}/{total_games}...")
            
            try:
                result, error = self.analyze_game(
                    pgn=pgn,
                    user_depth=user_depth,
                    username=username,
                    compute_threats=False,
                    key_moments_threshold=500,
                    min_gap_between_moments=2,
                )
                
                if result:
                    success_count += 1
                    analyzed_game_ids.append(game_id)
                else:
                    error_count += 1
                    if progress_callback:
                        progress_callback(i, total_games, f"Erreur : {error.message if error else 'Erreur inconnue'}")
                        
            except Exception as e:
                error_count += 1
                if progress_callback:
                    progress_callback(i, total_games, f"Exception : {str(e)}")
        
        return success_count, error_count, analyzed_game_ids