from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from app.core.logging import setup_logging


logger = setup_logging("prediction_log")


DB_PATH = Path(__file__).resolve().parent.parent / "auth.db"


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_prediction_tables() -> None:
    """
    初始化预测相关表结构（单条/批量共用）。
    与用户表复用同一个 auth.db。
    """
    conn = _get_conn()
    cur = conn.cursor()

    # 批量预测批次表
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS prediction_batches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            user_id INTEGER,
            model_version TEXT,
            total_count INTEGER,
            churn_count INTEGER,
            non_churn_count INTEGER
        )
        """
    )

    # 单条/批量统一的明细表；单条预测时 batch_id 为空
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS prediction_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            user_id INTEGER,
            batch_id INTEGER,
            is_single INTEGER DEFAULT 0,
            model_version TEXT,
            features_json TEXT,
            prediction_label TEXT,
            prediction_probability REAL,
            has_feedback INTEGER DEFAULT 0,
            true_label TEXT
        )
        """
    )

    conn.commit()
    conn.close()
    logger.info("预测日志相关数据表初始化完成")


@dataclass
class LoggedPredictionItem:
    id: int
    batch_id: Optional[int]
    user_id: Optional[int]
    model_version: Optional[str]
    prediction_label: str
    prediction_probability: float
    has_feedback: bool
    true_label: Optional[str]
    created_at: datetime


def log_single_prediction(
    *,
    user_id: Optional[int],
    model_version: Optional[str],
    features: Dict[str, Any],
    prediction_label: str,
    prediction_probability: float,
) -> int:
    """
    记录单条预测日志，返回插入的明细 ID。
    如果未显式提供模型版本，则默认记为 v2。
    """
    init_prediction_tables()
    conn = _get_conn()
    cur = conn.cursor()

    effective_version = model_version or "v2"

    cur.execute(
        """
        INSERT INTO prediction_items (
            user_id,
            batch_id,
            is_single,
            effective_version,
            features_json,
            prediction_label,
            prediction_probability
        )
        VALUES (?, NULL, 1, ?, ?, ?, ?)
        """,
        (
            user_id,
            model_version,
            json.dumps(features, ensure_ascii=False),
            prediction_label,
            float(prediction_probability),
        ),
    )

    item_id = cur.lastrowid
    conn.commit()
    conn.close()
    logger.info(f"已记录单条预测日志，ID={item_id}")
    return item_id


def log_batch_prediction(
    *,
    user_id: Optional[int],
    model_version: Optional[str],
    items: Iterable[Dict[str, Any]],
    churn_count: int,
    non_churn_count: int,
) -> int:
    """
    记录一次批量预测：
    - 在 prediction_batches 中插入一条批次记录
    - 在 prediction_items 中插入多条明细记录
    items: 迭代器，每个元素需包含 keys: features, prediction_label, prediction_probability

    如果未显式提供模型版本，则默认记为 v2。
    """
    init_prediction_tables()
    conn = _get_conn()
    cur = conn.cursor()

    effective_version = model_version or "v2"

    items_list: List[Dict[str, Any]] = list(items)
    total_count = len(items_list)

    # 插入批次
    cur.execute(
        """
        INSERT INTO prediction_batches (
            user_id,
            model_version,
            total_count,
            churn_count,
            non_churn_count
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (user_id, effective_version, total_count, churn_count, non_churn_count),
    )
    batch_id = cur.lastrowid

    # 插入明细
    for item in items_list:
        features = item.get("features") or {}
        label = item.get("prediction_label")
        prob = float(item.get("prediction_probability", 0.0))

        cur.execute(
            """
            INSERT INTO prediction_items (
                user_id,
                batch_id,
                is_single,
                effective_version,
                features_json,
                prediction_label,
                prediction_probability
            )
            VALUES (?, ?, 0, ?, ?, ?, ?)
            """,
            (
                user_id,
                batch_id,
                model_version,
                json.dumps(features, ensure_ascii=False),
                label,
                prob,
            ),
        )

    conn.commit()
    conn.close()
    logger.info(f"已记录批量预测日志，batch_id={batch_id}, 条数={total_count}")
    return batch_id


def add_feedback(item_id: int, true_label: str) -> None:
    """
    为一条预测结果补充真实标签反馈。
    """
    init_prediction_tables()
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE prediction_items
        SET has_feedback = 1,
            true_label = ?
        WHERE id = ?
        """,
        (true_label, item_id),
    )
    conn.commit()
    conn.close()
    logger.info(f"已为预测明细 {item_id} 记录反馈标签: {true_label}")

