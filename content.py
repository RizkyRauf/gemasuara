"""Content management for TikTok multi-account uploader.

A content item is a video + caption pair that belongs to exactly one account.
Each item lives in its own directory under ``content/<account>/<id>/``:

    content/
      <account_alias_or_open_id>/
        <short_id>/
          video.mp4
          meta.json

``meta.json`` stores the metadata defined in the shared design.
"""
from __future__ import annotations

import json
import logging
import secrets
import shutil
import string
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from auth import list_accounts

logger = logging.getLogger(__name__)

CONTENT_DIR = Path(__file__).parent / "content"
VIDEO_FILENAME = "video.mp4"
META_FILENAME = "meta.json"
VALID_STATUSES = {"draft", "ready", "posted", "failed"}
VALID_POST_MODES = {"draft", "direct"}
MAX_CAPTION_LENGTH = 2200
_CONTENT_ID_ALPHABET = string.ascii_lowercase + string.digits


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _generate_short_id(length: int = 8) -> str:
    return "".join(secrets.choice(_CONTENT_ID_ALPHABET) for _ in range(length))


def _account_id_from_alias(alias_or_id: str) -> str:
    """Resolve an account alias or open_id to the canonical open_id."""
    aliases = _load_aliases()
    if alias_or_id in aliases:
        return aliases[alias_or_id]

    # Accept open_ids that already have an alias mapped to them.
    if alias_or_id in aliases.values():
        return alias_or_id

    # Also accept raw open_ids that are already known from authentication.
    known = {acc["open_id"] for acc in list_accounts()}
    if alias_or_id in known:
        return alias_or_id

    raise ValueError(f"Akun '{alias_or_id}' tidak dikenali. "
                     "Daftarkan alias atau gunakan open_id yang valid.")


@dataclass
class Content:
    """A single piece of content ready to be managed and posted."""
    id: str
    account_id: str
    title: str
    caption: str
    status: str = "draft"
    post_mode: str = "draft"
    planned_at: str | None = None
    notes: str = ""
    created_at: str = field(default_factory=_utc_now)
    updated_at: str = field(default_factory=_utc_now)
    posted_at: str | None = None
    publish_id: str | None = None
    last_error: str | None = None
    failed_at: str | None = None

    def __post_init__(self):
        if self.status not in VALID_STATUSES:
            raise ValueError(f"Status tidak valid: {self.status}")
        if self.post_mode not in VALID_POST_MODES:
            raise ValueError(f"Post mode tidak valid: {self.post_mode}")

    @property
    def dir(self) -> Path:
        alias = get_alias(self.account_id) or self.account_id
        return CONTENT_DIR / alias / self.id

    @property
    def video_path(self) -> Path:
        return self.dir / VIDEO_FILENAME

    @property
    def meta_path(self) -> Path:
        return self.dir / META_FILENAME

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> Content:
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    def save(self) -> None:
        self.updated_at = _utc_now()
        self.dir.mkdir(parents=True, exist_ok=True)
        self.meta_path.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")
        logger.info("Content saved: %s (%s)", self.id, self.status)


def _load_aliases() -> dict[str, str]:
    aliases_file = Path(__file__).parent / "accounts.json"
    if aliases_file.exists():
        data = json.loads(aliases_file.read_text(encoding="utf-8"))
        return data.get("aliases", {})
    return {}


def _save_aliases(aliases: dict[str, str]) -> None:
    aliases_file = Path(__file__).parent / "accounts.json"
    data = {"aliases": aliases}
    aliases_file.write_text(json.dumps(data, indent=2), encoding="utf-8")


def set_alias(open_id: str, alias: str) -> None:
    """Assign a human-readable alias to an open_id."""
    if not alias:
        raise ValueError("Alias tidak boleh kosong")
    aliases = _load_aliases()
    # Remove any existing reverse mapping to keep 1-to-1.
    aliases = {k: v for k, v in aliases.items() if v != open_id}
    aliases[alias] = open_id
    _save_aliases(aliases)
    logger.info("Alias '%s' -> '%s' disimpan", alias, open_id)


def remove_alias(alias: str) -> None:
    """Remove an account alias."""
    aliases = _load_aliases()
    if alias in aliases:
        del aliases[alias]
        _save_aliases(aliases)
        logger.info("Alias '%s' dihapus", alias)


def get_alias(open_id: str) -> str | None:
    """Return the alias for an open_id, if any."""
    aliases = _load_aliases()
    for alias, oid in aliases.items():
        if oid == open_id:
            return alias
    return None


def list_aliases() -> dict[str, str]:
    """Return a mapping of alias -> open_id."""
    return _load_aliases()


def _resolve_account_dir(alias_or_id: str) -> Path:
    """Return the directory name (alias or open_id) used for an account."""
    aliases = _load_aliases()
    if alias_or_id in aliases:
        return Path(alias_or_id)
    return Path(alias_or_id)


def create_content(
    account: str,
    video_path: str | Path,
    title: str,
    caption: str,
    post_mode: str = "draft",
    planned_at: str | None = None,
    notes: str = "",
) -> Content:
    """Create a new content item, copying the video into the content tree."""
    account_id = _account_id_from_alias(account)
    alias = get_alias(account_id) or account_id
    source = Path(video_path)

    if not source.exists():
        raise FileNotFoundError(f"File video tidak ditemukan: {source}")

    _validate_caption(caption)

    content_id = _generate_short_id()
    while (CONTENT_DIR / alias / content_id).exists():
        content_id = _generate_short_id()

    content = Content(
        id=content_id,
        account_id=account_id,
        title=title,
        caption=caption,
        status="draft",
        post_mode=post_mode,
        planned_at=planned_at,
        notes=notes,
    )

    content.dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, content.video_path)
    content.save()
    logger.info("Content created: %s for account %s", content.id, account_id)
    return content


def load_content(content_id: str) -> Content:
    """Load a content item by its short id."""
    for account_dir in CONTENT_DIR.glob("*"):
        if not account_dir.is_dir():
            continue
        meta_path = account_dir / content_id / META_FILENAME
        if meta_path.exists():
            data = json.loads(meta_path.read_text(encoding="utf-8"))
            return Content.from_dict(data)
    raise ValueError(f"Konten dengan id '{content_id}' tidak ditemukan")


def load_all_content(
    account: str | None = None,
    status: str | None = None,
) -> list[Content]:
    """Load all content items with optional filters.

    The ``account`` argument may be an alias or an open_id. Filtering is done
    against the canonical ``account_id`` stored in each ``meta.json`` so that
    renaming aliases does not hide existing content.
    """
    items: list[Content] = []
    target_account_id = _account_id_from_alias(account) if account else None

    for account_dir in CONTENT_DIR.glob("*"):
        if not account_dir.is_dir():
            continue
        for meta_path in account_dir.rglob(META_FILENAME):
            data = json.loads(meta_path.read_text(encoding="utf-8"))
            content = Content.from_dict(data)
            if target_account_id and content.account_id != target_account_id:
                continue
            if status and content.status != status:
                continue
            items.append(content)

    items.sort(key=lambda c: c.created_at, reverse=True)
    return items


def update_content(
    content_id: str,
    title: str | None = None,
    caption: str | None = None,
    status: str | None = None,
    post_mode: str | None = None,
    planned_at: str | None = None,
    notes: str | None = None,
) -> Content:
    """Update metadata of an existing content item."""
    content = load_content(content_id)

    if title is not None:
        content.title = title
    if caption is not None:
        _validate_caption(caption)
        content.caption = caption
    if status is not None:
        if status not in VALID_STATUSES:
            raise ValueError(f"Status tidak valid: {status}")
        content.status = status
    if post_mode is not None:
        if post_mode not in VALID_POST_MODES:
            raise ValueError(f"Post mode tidak valid: {post_mode}")
        content.post_mode = post_mode
    if planned_at is not None:
        content.planned_at = planned_at
    if notes is not None:
        content.notes = notes

    content.save()
    return content


def delete_content(content_id: str) -> None:
    """Permanently delete a content item and its folder."""
    content = load_content(content_id)
    shutil.rmtree(content.dir)
    logger.info("Content deleted: %s", content.id)


def _validate_caption(caption: str) -> None:
    if not caption or not caption.strip():
        raise ValueError("Caption tidak boleh kosong")
    if len(caption) > MAX_CAPTION_LENGTH:
        raise ValueError(f"Caption terlalu panjang (maksimal {MAX_CAPTION_LENGTH} karakter)")


def mark_posted(content_id: str, publish_id: str) -> Content:
    """Mark content as successfully posted."""
    content = load_content(content_id)
    content.status = "posted"
    content.publish_id = publish_id
    content.posted_at = _utc_now()
    content.last_error = None
    content.failed_at = None
    content.save()
    return content


def mark_failed(content_id: str, error_message: str) -> Content:
    """Mark content as failed with an error message."""
    content = load_content(content_id)
    content.status = "failed"
    content.last_error = error_message
    content.failed_at = _utc_now()
    content.save()
    return content


def summary() -> dict[str, dict[str, int]]:
    """Return a summary of content counts per account and status."""
    result: dict[str, dict[str, int]] = {}
    for content in load_all_content():
        display = get_alias(content.account_id) or content.account_id
        if display not in result:
            result[display] = {status: 0 for status in VALID_STATUSES}
            result[display]["total"] = 0
        result[display][content.status] += 1
        result[display]["total"] += 1
    return result
