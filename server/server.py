import os, re, time
import rpyc
from rpyc.utils.server import ThreadedServer
import redis

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
TEXT_DIR   = os.getenv("TEXT_DIR", "/app/server/texts")
SERVER_HOST= os.getenv("SERVER_HOST", "0.0.0.1")
SERVER_PORT= int(os.getenv("SERVER_PORT", "18861"))

r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

def _load_text(path):
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()

class WordCountService(rpyc.Service):
    def exposed_list_texts(self):
        return sorted([f for f in os.listdir(TEXT_DIR) if f.endswith(".txt")])

    def exposed_count(self, keyword: str, filename: str):
        """
        Returns: dict {count:int, cached:bool, server_time_ms:float, host:str}
        """
        t0 = time.perf_counter()
        keyword_norm = keyword.strip().lower()
        cache_key = f"wc:{filename}:{keyword_norm}"

        cached_value = r.get(cache_key)
        if cached_value is not None:
            t1 = time.perf_counter()
            return {"count": int(cached_value), "cached": True,
                    "server_time_ms": (t1 - t0) * 1000.0, "host": SERVER_HOST}

        path = os.path.join(TEXT_DIR, filename)
        if not os.path.exists(path):
            raise FileNotFoundError(f"No such text: {filename}")

        text = _load_text(path).lower()
        # exact word count
        count = len(re.findall(rf"\b{re.escape(keyword_norm)}\b", text))

        r.set(cache_key, count)

        t1 = time.perf_counter()
        return {"count": count, "cached": False,
                "server_time_ms": (t1 - t0) * 1000.0, "host": SERVER_HOST}

if __name__ == "__main__":
    print(f"[server] starting on {SERVER_HOST}:{SERVER_PORT}, texts in {TEXT_DIR}")
    server = ThreadedServer(WordCountService, hostname=SERVER_HOST, port=SERVER_PORT)
    server.start()
