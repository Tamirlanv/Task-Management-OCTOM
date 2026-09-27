from app.core.metrics import Metrics


def test_metrics_aggregate_and_bound_method_labels() -> None:
    metrics = Metrics()
    metrics.observe("GET", "/tasks/{task_id}", 200, 0.05)
    metrics.observe("GET", "/tasks/{task_id}", 200, 0.1)
    metrics.observe("ARBITRARY", "unmatched", 404, 0.01)
    output = metrics.render(2, 5)
    assert 'route="/tasks/{task_id}",status="200"} 2' in output
    assert 'method="OTHER"' in output
    assert "ARBITRARY" not in output
    assert "taskman_db_connections_checked_out 2" in output
