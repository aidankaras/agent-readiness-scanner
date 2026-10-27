"""Polite HTTP fetching (stdlib only). Respects robots.txt for our own UA, rate-limits, caches per run."""
import time, urllib.request, urllib.error, urllib.robotparser, urllib.parse
from dataclasses import dataclass

UA = "agent-readiness-scanner/0.3 (+https://github.com/aidankaras/agent-readiness-scanner)"


@dataclass
class Resp:
    url: str
    status: int
    ctype: str = ""
    text: str = ""

    @property
    def ok(self):
        return 200 <= self.status < 300


class Fetcher:
    def __init__(self, delay=1.0, timeout=15, max_bytes=3_000_000):
        self.delay, self.timeout, self.max_bytes = delay, timeout, max_bytes
        self._last = 0.0
        self._cache = {}
        self._robots = {}

    def allowed(self, url):
        p = urllib.parse.urlsplit(url)
        origin = f"{p.scheme}://{p.netloc}"
        if p.path == "/robots.txt":
            return True
        if origin not in self._robots:
            rp = urllib.robotparser.RobotFileParser()
            r = self._raw(origin + "/robots.txt")
            rp.parse(r.text.splitlines() if r.ok else [])
            self._robots[origin] = rp
        return self._robots[origin].can_fetch(UA, url)

    def get(self, url):
        if url in self._cache:
            return self._cache[url]
        if not self.allowed(url):
            r = Resp(url, -2, text="blocked by robots.txt for scanner UA")
        else:
            r = self._raw(url)
        self._cache[url] = r
        return r

    def _raw(self, url):
        if url in self._cache:
            return self._cache[url]
        wait = self.delay - (time.monotonic() - self._last)
        if wait > 0:
            time.sleep(wait)
        self._last = time.monotonic()
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as f:
                body = f.read(self.max_bytes)
                r = Resp(f.geturl(), f.status, f.headers.get("Content-Type", ""), body.decode("utf-8", "replace"))
        except urllib.error.HTTPError as e:
            body = e.read(200_000).decode("utf-8", "replace") if e.fp else ""
            r = Resp(url, e.code, e.headers.get("Content-Type", "") if e.headers else "", body)
        except Exception as e:  # network error, timeout, TLS
            r = Resp(url, -1, text=f"{type(e).__name__}: {e}")
        self._cache[url] = r
        return r


class FixtureFetcher:
    """Serves files from a fixture dir: path '/a/b.json' -> dir/'a__b.json'. Missing -> 404."""

    def __init__(self, base, root):
        import pathlib
        self.base, self.root = base.rstrip("/"), pathlib.Path(root)

    def allowed(self, url):
        return True

    def get(self, url):
        p = urllib.parse.urlsplit(url)
        if url.startswith(self.base):
            key = (p.path.strip("/") or "index").replace("/", "__")
            if p.query:
                key += "__" + p.query.replace("=", "-").replace("&", "_")
            f = self.root / key
            if f.exists():
                ct = "application/json" if key.endswith(".json") or "well-known" in key else "text/html"
                return Resp(url, 200, ct, f.read_text())
        return Resp(url, 404, "text/html", "not found")
