from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen


ROLLCALL_TWITTER_URL = "https://rollcall.com/wp-json/factbase/v1/twitter"


class RollCallError(RuntimeError):
    pass


@dataclass(frozen=True)
class RollCallCount:
    start: date
    end: date
    count: int


@dataclass(frozen=True)
class RollCallPost:
    id: str
    posted_at: datetime
    text: str
    post_url: str
    media_type: str | None
    word_count: int | None
    deleted: bool
    repost: bool
    quote: bool

    @classmethod
    def from_api(cls, item: dict) -> "RollCallPost":
        social = item.get("social") or {}
        return cls(
            id=str(item["id"]),
            posted_at=datetime.fromisoformat(item["date"]),
            text=str(item.get("text") or social.get("post_text") or ""),
            post_url=str(item.get("post_url") or ""),
            media_type=item.get("media_type"),
            word_count=parse_int(item.get("word_count")),
            deleted=bool(item.get("deleted_flag")),
            repost=bool(social.get("repost_flag")),
            quote=bool(social.get("quote_flag")),
        )

    def to_json(self) -> dict:
        return {
            "id": self.id,
            "posted_at": self.posted_at.isoformat(),
            "text": self.text,
            "post_url": self.post_url,
            "media_type": self.media_type,
            "word_count": self.word_count,
            "deleted": self.deleted,
            "repost": self.repost,
            "quote": self.quote,
        }

    @classmethod
    def from_json(cls, item: dict) -> "RollCallPost":
        return cls(
            id=str(item["id"]),
            posted_at=datetime.fromisoformat(item["posted_at"]),
            text=str(item.get("text") or ""),
            post_url=str(item.get("post_url") or ""),
            media_type=item.get("media_type"),
            word_count=parse_int(item.get("word_count")),
            deleted=bool(item.get("deleted")),
            repost=bool(item.get("repost")),
            quote=bool(item.get("quote")),
        )


def parse_int(value: object) -> int | None:
    if value in (None, ""):
        return None
    return int(value)


class JsonCountCache:
    def __init__(self, path: Path, ttl_hours: float) -> None:
        self.path = path
        self.ttl_hours = ttl_hours
        self.data = self._load()

    def get(self, start: date, end: date) -> int | None:
        item = self.data.get(self._key(start, end))
        if not item or not self._is_fresh(item):
            return None
        return int(item["count"])

    def set(self, start: date, end: date, count: int) -> None:
        self.data[self._key(start, end)] = {
            "count": count,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as file:
            json.dump(self.data, file, indent=2, sort_keys=True)
            file.write("\n")

    def _load(self) -> dict[str, dict]:
        if not self.path.exists():
            return {}
        try:
            with self.path.open("r", encoding="utf-8") as file:
                data = json.load(file)
        except (OSError, json.JSONDecodeError):
            return {}
        return data if isinstance(data, dict) else {}

    def _is_fresh(self, item: dict) -> bool:
        if self.ttl_hours <= 0:
            return False
        fetched_at = item.get("fetched_at")
        if not fetched_at:
            return False
        try:
            fetched = datetime.fromisoformat(fetched_at)
        except ValueError:
            return False
        if fetched.tzinfo is None:
            fetched = fetched.replace(tzinfo=timezone.utc)
        age = datetime.now(timezone.utc) - fetched.astimezone(timezone.utc)
        return age <= timedelta(hours=self.ttl_hours)

    @staticmethod
    def _key(start: date, end: date) -> str:
        return f"{start.isoformat()}:{end.isoformat()}"


class RollCallClient:
    def __init__(
        self,
        *,
        base_url: str = ROLLCALL_TWITTER_URL,
        timeout: int = 25,
        cache: JsonCountCache | None = None,
    ) -> None:
        self.base_url = base_url
        self.timeout = timeout
        self.cache = cache

    def count_truth_social_posts(self, start: date, end: date, *, use_cache: bool = True) -> int:
        cached = self.cache.get(start, end) if self.cache and use_cache else None
        if cached is not None:
            return cached

        data = self._get_json(
            {
                "platform": "truth social",
                "sort": "date",
                "sort_order": "desc",
                "page": 1,
                "format": "json",
                "dateFilter": "custom",
                "start_date": start.strftime("%m/%d/%Y"),
                "end_date": end.strftime("%m/%d/%Y"),
            }
        )
        try:
            count = int(data["meta"]["total_hits"])
        except (KeyError, TypeError, ValueError) as exc:
            raise RollCallError("Roll Call response did not include meta.total_hits") from exc

        if self.cache and use_cache:
            self.cache.set(start, end, count)
        return count

    def count_completed_weeks(self, week_start: date, lookback_weeks: int) -> list[RollCallCount]:
        counts: list[RollCallCount] = []
        for offset in range(1, lookback_weeks + 1):
            start = week_start - timedelta(days=7 * offset)
            end = start + timedelta(days=6)
            counts.append(
                RollCallCount(
                    start=start,
                    end=end,
                    count=self.count_truth_social_posts(start, end),
                )
            )
        return counts

    def truth_social_posts(self, start: date, end: date) -> list[RollCallPost]:
        posts: list[RollCallPost] = []
        page = 1
        page_count = 1
        while page <= page_count:
            data = self._get_json(
                {
                    "platform": "truth social",
                    "sort": "date",
                    "sort_order": "desc",
                    "page": page,
                    "format": "json",
                    "dateFilter": "custom",
                    "start_date": start.strftime("%m/%d/%Y"),
                    "end_date": end.strftime("%m/%d/%Y"),
                }
            )
            try:
                page_count = int(data["meta"]["page_count"])
                rows = data["data"]
            except (KeyError, TypeError, ValueError) as exc:
                raise RollCallError("Roll Call response did not include paginated post data") from exc

            posts.extend(RollCallPost.from_api(row) for row in rows)
            page += 1

        return sorted(posts, key=lambda post: post.posted_at)

    def _get_json(self, params: dict[str, object]) -> dict:
        request = Request(
            f"{self.base_url}?{urlencode(params)}",
            headers={"User-Agent": "Argus TruthSocialForecast/0.1"},
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                return json.load(response)
        except OSError as exc:
            raise RollCallError(f"Roll Call request failed: {exc}") from exc
