import json
from collections import Counter, defaultdict
from threading import Lock

BUCKETS = (0.01, 0.025, 0.05, 0.1, 0.3, 0.5, 1.0, 2.5, 5.0)


class Metrics:
    """Bounded-label Prometheus counters for one application process."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._counts: Counter[tuple[str, str, int]] = Counter()
        self._durations: defaultdict[tuple[str, str, int], float] = defaultdict(float)
        self._buckets: Counter[tuple[str, str, int, float]] = Counter()

    def observe(self, method: str, route: str, status: int, duration: float) -> None:
        # Arbitrary methods and unknown paths must not create unlimited label values.
        method = (
            method
            if method in {"GET", "POST", "PATCH", "DELETE", "OPTIONS", "HEAD", "PUT"}
            else "OTHER"
        )
        key = (method, route, status)
        with self._lock:
            self._counts[key] += 1
            self._durations[key] += duration
            for bucket in BUCKETS:
                if duration <= bucket:
                    self._buckets[(*key, bucket)] += 1

    def render(self, pool_checked_out: int, pool_size: int) -> str:
        lines = [
            "# TYPE taskman_http_requests_total counter",
            "# TYPE taskman_http_duration_seconds histogram",
            "# TYPE taskman_db_connections_checked_out gauge",
            f"taskman_db_connections_checked_out {pool_checked_out}",
            "# TYPE taskman_db_pool_size gauge",
            f"taskman_db_pool_size {pool_size}",
        ]
        with self._lock:
            for (method, route, status), count in sorted(self._counts.items()):
                labels = f'method={json.dumps(method)},route={json.dumps(route)},status="{status}"'
                key = (method, route, status)
                lines.append(f"taskman_http_requests_total{{{labels}}} {count}")
                for bucket in BUCKETS:
                    lines.append(
                        f'taskman_http_duration_seconds_bucket{{{labels},le="{bucket}"}} {self._buckets[(*key, bucket)]}'
                    )
                lines.append(
                    f'taskman_http_duration_seconds_bucket{{{labels},le="+Inf"}} {count}'
                )
                lines.append(f"taskman_http_duration_seconds_count{{{labels}}} {count}")
                lines.append(
                    f"taskman_http_duration_seconds_sum{{{labels}}} {self._durations[key]}"
                )
        return "\n".join(lines) + "\n"
