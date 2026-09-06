"""
LUMYD Gemini Quota Guard & Rate Limiter
Enforces safety constraints for Gemini API Free Tier:
- Max 15 requests per minute (enforces minimum 4-second delay between calls)
- Max 1,000 requests per day (staying well under the 1,500 daily free tier limit)
- Query-level response caching to avoid repeated calls for identical questions
- Automatic daily counter reset at UTC midnight
"""

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
TRACKER_FILE = DATA_DIR / "gemini_quota_tracker.json"
CACHE_FILE = DATA_DIR / "gemini_query_cache.json"

# Free tier safety thresholds
DEFAULT_DAILY_LIMIT = 1000       # Free tier limit is 1,500; 1,000 provides a 33% safety margin
MIN_REQUEST_INTERVAL = 4.1       # 15 RPM = 1 request every 4 seconds; 4.1s guarantees compliance


class GeminiQuotaGuard:
    def __init__(
        self,
        daily_limit: int = DEFAULT_DAILY_LIMIT,
        min_interval: float = MIN_REQUEST_INTERVAL
    ):
        self.daily_limit = daily_limit
        self.min_interval = min_interval
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self._last_call_time: float = 0.0

    def _get_today_date_str(self) -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")

    def _load_tracker(self) -> Dict[str, Any]:
        if not TRACKER_FILE.exists():
            return {"date": self._get_today_date_str(), "requests_today": 0, "total_all_time": 0}
        try:
            with open(TRACKER_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Reset if new day (UTC)
                if data.get("date") != self._get_today_date_str():
                    data["date"] = self._get_today_date_str()
                    data["requests_today"] = 0
                return data
        except Exception:
            return {"date": self._get_today_date_str(), "requests_today": 0, "total_all_time": 0}

    def _save_tracker(self, data: Dict[str, Any]) -> None:
        try:
            with open(TRACKER_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[!] Warning: Failed to save quota tracker: {e}")

    def get_status(self) -> Dict[str, Any]:
        """Returns the current daily quota usage and safety limit."""
        tracker = self._load_tracker()
        used = tracker.get("requests_today", 0)
        remaining = max(0, self.daily_limit - used)
        return {
            "date_utc": tracker.get("date"),
            "requests_used_today": used,
            "daily_safety_limit": self.daily_limit,
            "requests_remaining": remaining,
            "total_all_time": tracker.get("total_all_time", 0),
            "percentage_used": round((used / self.daily_limit) * 100, 2)
        }

    def can_request(self) -> Tuple[bool, str]:
        """Checks if a new request is allowed under daily limits."""
        status = self.get_status()
        if status["requests_remaining"] <= 0:
            return False, f"Daily Gemini Free Tier safety quota reached ({status['requests_used_today']}/{self.daily_limit})."
        return True, "OK"

    def throttle_and_record(self) -> None:
        """Enforces minimum interval (15 RPM) and records the request."""
        now = time.time()
        elapsed = now - self._last_call_time
        if elapsed < self.min_interval:
            sleep_duration = self.min_interval - elapsed
            time.sleep(sleep_duration)

        # Update counter
        tracker = self._load_tracker()
        tracker["requests_today"] = tracker.get("requests_today", 0) + 1
        tracker["total_all_time"] = tracker.get("total_all_time", 0) + 1
        self._save_tracker(tracker)
        self._last_call_time = time.time()

    # Response Caching
    def get_cached_response(self, query: str) -> Optional[Dict[str, Any]]:
        """Retrieves cached structured response if previously processed."""
        if not CACHE_FILE.exists():
            return None
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                cache = json.load(f)
            key = query.strip().lower()
            return cache.get(key)
        except Exception:
            return None

    def cache_response(self, query: str, response_data: Dict[str, Any]) -> None:
        """Caches structured response to prevent repeat API calls."""
        cache = {}
        if CACHE_FILE.exists():
            try:
                with open(CACHE_FILE, "r", encoding="utf-8") as f:
                    cache = json.load(f)
            except Exception:
                cache = {}
        key = query.strip().lower()
        cache[key] = response_data
        try:
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(cache, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[!] Warning: Failed to save query cache: {e}")


# Singleton instance
quota_guard = GeminiQuotaGuard()
