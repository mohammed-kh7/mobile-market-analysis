"""محرك السوق: البحث، سحب المراجعات، التنظيف، تصنيف المشاعر، SQLite، وتقرير CSV."""
from __future__ import annotations

import re
import sqlite3
import time
import unicodedata
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterator, Optional

import pandas as pd
from google_play_scraper import Sort
from google_play_scraper import reviews as gp_reviews
from google_play_scraper import search as gp_search

DB_PATH = str(Path(__file__).with_name("competitor_intelligence.db"))
BATCH_SIZE = 500
MIN_REVIEWS, MAX_REVIEWS = 500, 10000

_URL_RE = re.compile(r"https?://\S+|www\.\S+")
_CTRL_RE = re.compile(r"[\u0000-\u0008\u000b\u000c\u000e-\u001f\u200b-\u200f\u202a-\u202e]")


# ----------------------------------------------------------------------------
# البحث
# ----------------------------------------------------------------------------
def _summary(r: dict) -> dict:
    return {
        "title": r.get("title") or "",
        "developer": r.get("developer") or "",
        "score": float(r.get("score") or 0.0),
        "icon": r.get("icon") or "",
        "appId": r.get("appId") or "",
    }


def search_apps(query: str, lang: str = "en", country: str = "us", limit: int = 10) -> list[dict]:
    """بحث ديناميكي بالاسم أو الكلمة المفتاحية أو الفئة."""
    query = (query or "").strip()
    if not query:
        return []
    try:
        raw = gp_search(query, lang=lang, country=country, n_hits=limit)
    except Exception as exc:
        raise RuntimeError(f"فشل البحث: {exc}") from exc
    return [_summary(r) for r in raw if r.get("appId")]


# ----------------------------------------------------------------------------
# سحب المراجعات (دفعات صغيرة + إعادة محاولة)
# ----------------------------------------------------------------------------
def iter_review_batches(
    app_id: str,
    count: int = 500,
    lang: str = "en",
    country: str = "us",
    progress_cb: Optional[Callable[[float], None]] = None,
) -> Iterator[list[dict]]:
    """Stream pages of at most 500 unique reviews; always request 500 upstream.

    The final page can be smaller when the store is exhausted. An upstream
    failure is raised even after earlier pages were saved, never hidden.
    """
    count = max(MIN_REVIEWS, min(int(count), MAX_REVIEWS))
    collected = 0
    seen: set[str] = set()
    token = None
    last_error: Optional[Exception] = None

    while collected < count:
        result = None
        for attempt in range(3):
            try:
                result, token = gp_reviews(
                    app_id, lang=lang, country=country, sort=Sort.NEWEST,
                    count=BATCH_SIZE, continuation_token=token,
                )
                last_error = None
                break
            except Exception as exc:  # شبكة أو حجب مؤقت
                last_error = exc
                if attempt < 2:
                    time.sleep(0.5 * (2 ** attempt))
        if last_error:
            raise RuntimeError(f"Review download failed for {app_id}: {last_error}") from last_error
        if not result:
            break
        page = []
        for review in result:
            review_id = review.get("reviewId")
            if review_id and review_id not in seen:
                seen.add(review_id)
                page.append(review)
        if not page:
            break
        page = page[:count - collected]
        # Defensive slicing also bounds parsing if an upstream client overfills.
        for start in range(0, len(page), BATCH_SIZE):
            chunk = page[start:start + BATCH_SIZE]
            collected += len(chunk)
            yield chunk
        if progress_cb:
            progress_cb(min(collected / count, 1.0))
        if token is None:
            break


def fetch_reviews(app_id: str, count: int = 500, lang: str = "en", country: str = "us",
                  progress_cb: Optional[Callable[[float], None]] = None) -> list[dict]:
    """Compatibility API; interactive analysis consumes the streaming API."""
    return [review for batch in iter_review_batches(app_id, count, lang, country, progress_cb)
            for review in batch]


# ----------------------------------------------------------------------------
# التنظيف وتصنيف المشاعر
# ----------------------------------------------------------------------------
def clean_text(text: object) -> str:
    text = unicodedata.normalize("NFKC", str(text or ""))
    text = _URL_RE.sub(" ", text)
    text = _CTRL_RE.sub("", text)
    return re.sub(r"\s+", " ", text).strip()


def classify_sentiment(score: int) -> str:
    if score >= 4:
        return "Positive"
    if score <= 2:
        return "Negative"
    return "Neutral"


def reviews_to_frame(raw: list[dict], app_id: str) -> pd.DataFrame:
    if len(raw) > BATCH_SIZE:
        return pd.concat([reviews_to_frame(raw[start:start + BATCH_SIZE], app_id)
                          for start in range(0, len(raw), BATCH_SIZE)], ignore_index=True)
    fetched_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    rows = []
    for r in raw:
        score = int(r.get("score") or 0)
        if not 1 <= score <= 5 or not r.get("reviewId"):
            continue
        rows.append({
            "review_id": r["reviewId"],
            "app_id": app_id,
            "user_name": r.get("userName") or "",
            "score": score,
            "content": r.get("content") or "",
            "clean_content": clean_text(r.get("content")),
            "review_at": pd.Timestamp(r["at"]).isoformat() if r.get("at") else None,
            "thumbs_up": int(r.get("thumbsUpCount") or 0),
            "app_version": r.get("reviewCreatedVersion") or "",
            "sentiment": classify_sentiment(score),
            "fetched_at": fetched_at,
        })
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------------
# SQLite
# ----------------------------------------------------------------------------
@contextmanager
def _connect(db_path: str = DB_PATH):
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        _init_schema(conn)
        yield conn
        conn.commit()
    finally:
        conn.close()


def _init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS apps (
            app_id     TEXT PRIMARY KEY,
            title      TEXT NOT NULL,
            developer  TEXT,
            score      REAL,
            icon       TEXT,
            updated_at TEXT
        );
        CREATE TABLE IF NOT EXISTS reviews (
            review_id     TEXT PRIMARY KEY,
            app_id        TEXT NOT NULL REFERENCES apps(app_id),
            user_name     TEXT,
            score         INTEGER NOT NULL CHECK (score BETWEEN 1 AND 5),
            content       TEXT,
            clean_content TEXT,
            review_at     TEXT,
            thumbs_up     INTEGER DEFAULT 0,
            app_version   TEXT,
            sentiment     TEXT NOT NULL CHECK (sentiment IN ('Positive','Neutral','Negative')),
            fetched_at    TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_reviews_app  ON reviews(app_id);
        CREATE INDEX IF NOT EXISTS idx_reviews_date ON reviews(review_at);
        """
    )


def save_app(info: dict, db_path: str = DB_PATH) -> None:
    with _connect(db_path) as conn:
        conn.execute(
            "INSERT INTO apps (app_id, title, developer, score, icon, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?) ON CONFLICT(app_id) DO UPDATE SET "
            "title=excluded.title, developer=excluded.developer, score=excluded.score, "
            "icon=excluded.icon, updated_at=excluded.updated_at",
            (info["appId"], info["title"], info["developer"], info["score"], info["icon"],
             datetime.now(timezone.utc).isoformat(timespec="seconds")),
        )


def save_reviews(df: pd.DataFrame, db_path: str = DB_PATH) -> int:
    if df.empty:
        return 0
    cols = ["review_id", "app_id", "user_name", "score", "content", "clean_content",
            "review_at", "thumbs_up", "app_version", "sentiment", "fetched_at"]
    with _connect(db_path) as conn:
        conn.executemany(
            f"INSERT OR REPLACE INTO reviews ({', '.join(cols)}) VALUES ({', '.join('?' * len(cols))})",
            df[cols].itertuples(index=False, name=None),
        )
    return len(df)


def load_reviews(app_ids: list[str], db_path: str = DB_PATH) -> pd.DataFrame:
    if not app_ids:
        return pd.DataFrame()
    marks = ", ".join("?" * len(app_ids))
    with _connect(db_path) as conn:
        chunks = pd.read_sql_query(
            f"""SELECT r.review_id, r.app_id, a.title AS app_title, r.user_name, r.score,
                       r.clean_content AS content, r.review_at, r.thumbs_up,
                       r.app_version, r.sentiment
                FROM reviews r JOIN apps a ON a.app_id = r.app_id
                WHERE r.app_id IN ({marks})""",
            conn, params=app_ids, chunksize=BATCH_SIZE,
        )
        frames = []
        for frame in chunks:
            frame["review_at"] = pd.to_datetime(frame["review_at"], errors="coerce")
            frames.append(frame)
        df = pd.concat(frames, ignore_index=True)
    return df


# ----------------------------------------------------------------------------
# تقرير CSV
# ----------------------------------------------------------------------------
CSV_COLUMNS = ("app_title", "user_name", "score", "sentiment", "review_at",
               "thumbs_up", "app_version", "content")


def _safe_csv_value(value: object) -> object:
    """Keep untrusted store text from becoming a formula in spreadsheet apps."""
    if isinstance(value, str) and (value.lstrip().startswith(("=", "+", "-", "@"))
                                   or value.startswith(("\t", "\r", "\n"))):
        return "'" + value
    return value


def build_csv_report(df: pd.DataFrame) -> bytes:
    report = df.reindex(columns=CSV_COLUMNS).sort_values(
        ["app_title", "review_at"], ascending=[True, False]
    ).copy()
    for column in ("app_title", "user_name", "app_version", "content"):
        report[column] = report[column].map(_safe_csv_value)
    return report.to_csv(index=False, lineterminator="\n").encode("utf-8-sig")
