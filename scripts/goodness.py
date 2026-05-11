from enum import Enum
from typing import TYPE_CHECKING
import numpy as np
from numpy._typing import NDArray
import logging

if TYPE_CHECKING:
    from hiclas_holder import HiclasHolder

logger = logging.getLogger(__name__)


class GoodnessType(Enum):
    JACCARD = 1
    RUZICKA = 2
    CZEKANOWSKI = 3


class Goodness:
    __slots__ = ("__type", "__rows", "__columns", "__total")
    __type: GoodnessType
    __rows: NDArray[np.float32]
    __columns: NDArray[np.float32]
    __total: float

    def __init__(
        self,
        rows: NDArray[np.float32],
        columns: NDArray[np.float32],
        total: float,
        type: GoodnessType,
    ):
        self.__rows = rows
        self.__columns = columns
        self.__total = total
        self.__type = type

    @property
    def rows(self) -> NDArray[np.float32]:
        return self.__rows

    @property
    def columns(self) -> NDArray[np.float32]:
        return self.__columns

    @property
    def total(self) -> float:
        return self.__total

    @property
    def type(self) -> GoodnessType:
        return self.__type


def compare_matrices(
    a: np.ndarray,
    b: np.ndarray,
    t: GoodnessType,
) -> Goodness:
    logger.info(f"[compare_matrices] Starting comparison with type={t}, shapes: a={a.shape}, b={b.shape}")
    if a.shape != b.shape:
        raise ValueError("Shape of matrices do not match")
    if t == GoodnessType.JACCARD:
        logger.debug(f"[compare_matrices] Computing Jaccard similarity...")
        result = __calc_jaccard(a, b)
        logger.info(f"[compare_matrices] Jaccard computed, total={result.total}")
        return result
    elif t == GoodnessType.RUZICKA:
        logger.debug(f"[compare_matrices] Computing Ruzicka similarity...")
        result = __calc_ruzicka(a, b)
        logger.info(f"[compare_matrices] Ruzicka computed, total={result.total}")
        return result
    elif t == GoodnessType.CZEKANOWSKI:
        logger.debug(f"[compare_matrices] Computing Czekanowski similarity...")
        result = __calc_czekanowski(a, b)
        logger.info(f"[compare_matrices] Czekanowski computed, total={result.total}")
        return result
    else:
        raise ValueError(f"Unknown goodness type {type}")


def compare_hmcs(a: "HiclasHolder", b: "HiclasHolder", t: GoodnessType) -> Goodness:
    return compare_matrices(a.incidences, b.incidences, t)


def __calc_jaccard(
    a: np.ndarray,
    b: np.ndarray,
) -> Goodness:
    logger.debug(f"[__calc_jaccard] Computing row-wise intersections and unions...")
    
    # Row-wise Jaccard
    intersection_row = np.logical_and(a, b).sum(axis=1)
    union_row = np.logical_or(a, b).sum(axis=1)
    rows = np.divide(
        intersection_row,
        union_row,
        out=np.zeros_like(intersection_row, dtype=float),
        where=union_row != 0,
    )
    logger.debug(f"[__calc_jaccard] Row-wise done. Computing column-wise...")

    intersection_col = np.logical_and(a, b).sum(axis=0)
    union_col = np.logical_or(a, b).sum(axis=0)
    columns = np.divide(
        intersection_col,
        union_col,
        out=np.zeros_like(intersection_col, dtype=float),
        where=union_col != 0,
    )
    logger.debug(f"[__calc_jaccard] Column-wise done. Computing total...")

    intersection_total = intersection_row.sum()
    union_total = union_row.sum()
    total = intersection_total / union_total if union_total != 0 else 0.0

    logger.debug(f"[__calc_jaccard] Jaccard calculation complete: total={total:.4f}")
    return Goodness(rows, columns, total, GoodnessType.JACCARD)


def __calc_ruzicka(
    a: np.ndarray,
    b: np.ndarray,
) -> Goodness:
    """
    Calculate Ruzicka similarity index (weighted Jaccard).
    Works with both binary and continuous valued matrices.
    Ruzicka = Σ min(a_i, b_i) / Σ max(a_i, b_i)
    """
    logger.debug(f"[__calc_ruzicka] Computing row-wise min and max...")

    # Row-wise Ruzicka
    min_row = np.minimum(a, b).sum(axis=1)
    max_row = np.maximum(a, b).sum(axis=1)
    rows = np.divide(
        min_row,
        max_row,
        out=np.zeros_like(min_row, dtype=np.float32),
        where=max_row != 0,
    )
    logger.debug(f"[__calc_ruzicka] Row-wise done. Computing column-wise...")

    # Column-wise Ruzicka
    min_col = np.minimum(a, b).sum(axis=0)
    max_col = np.maximum(a, b).sum(axis=0)
    columns = np.divide(
        min_col,
        max_col,
        out=np.zeros_like(min_col, dtype=np.float32),
        where=max_col != 0,
    )
    logger.debug(f"[__calc_ruzicka] Column-wise done. Computing total...")

    # Total Ruzicka
    min_total = min_row.sum()
    max_total = max_row.sum()
    total = min_total / max_total if max_total != 0 else 0.0

    logger.debug(f"[__calc_ruzicka] Ruzicka calculation complete: total={total:.4f}")
    return Goodness(rows.astype(np.float32), columns.astype(np.float32), total, GoodnessType.RUZICKA)


def __calc_czekanowski(
    a: np.ndarray,
    b: np.ndarray,
) -> Goodness:
    """
    Calculate Czekanowski similarity coefficient (Czekanowski-Dice-Sørensen).
    Works with both binary and continuous valued matrices.
    Czekanowski = 2 × Σ min(a_i, b_i) / Σ (a_i + b_i)
    """
    logger.debug(f"[__calc_czekanowski] Computing row-wise min and sum...")

    # Row-wise Czekanowski
    min_row = np.minimum(a, b).sum(axis=1)
    sum_row = (a + b).sum(axis=1)
    rows = np.divide(
        2 * min_row,
        sum_row,
        out=np.zeros_like(min_row, dtype=np.float32),
        where=sum_row != 0,
    )
    logger.debug(f"[__calc_czekanowski] Row-wise done. Computing column-wise...")

    # Column-wise Czekanowski
    min_col = np.minimum(a, b).sum(axis=0)
    sum_col = (a + b).sum(axis=0)
    columns = np.divide(
        2 * min_col,
        sum_col,
        out=np.zeros_like(min_col, dtype=np.float32),
        where=sum_col != 0,
    )
    logger.debug(f"[__calc_czekanowski] Column-wise done. Computing total...")

    # Total Czekanowski
    min_total = min_row.sum()
    sum_total = sum_row.sum()
    total = 2 * min_total / sum_total if sum_total != 0 else 0.0

    logger.debug(f"[__calc_czekanowski] Czekanowski calculation complete: total={total:.4f}")
    return Goodness(rows.astype(np.float32), columns.astype(np.float32), total, GoodnessType.CZEKANOWSKI)
