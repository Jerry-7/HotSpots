from typing import List, Dict, Any, Optional
import time
import json

try:
    import redis
except ImportError:
    redis = None

class ShortTermMemory:
    """
    Chat history storage.
    Uses Redis if available, otherwise falls back to in-memory dict.
    """
    def __init__(self, redis_url: Optional[str] = None):
        self._fallback: Dict[str, List[Dict[str, Any]]] = {}
        self._client: Optional[redis.Redis] = None
        if redis_url and redis:
            try:
                self._client = redis.Redis.from_url(redis_url, decode_responses=True)
            except Exception:
                self._client = None

    def _key(self, session_id: str) -> str:
        return f"chat_history:{session_id}"

    def add(self, session_id: str, role: str, content: str) -> None:
        """Add a message to the session history."""
        item = {"role": role, "content": content, "ts": time.time()}
        if self._client:
            # 使用 json 而非 str/eval
            self._client.rpush(self._key(session_id), json.dumps(item))
        else:
            self._fallback.setdefault(session_id, []).append(item)

    def get(self, session_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get the last `limit` messages of a session."""
        if self._client:
            # lrange 的参数是 start, end
            data = self._client.lrange(self._key(session_id), -limit, -1)
            return [json.loads(x) for x in data]
        return self._fallback.get(session_id, [])[-limit:]

    def clear(self, session_id: str) -> None:
        """Clear all messages of a session."""
        if self._client:
            self._client.delete(self._key(session_id))
        else:
            self._fallback[session_id] = []
