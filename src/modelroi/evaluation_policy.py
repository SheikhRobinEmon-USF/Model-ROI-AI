"""Provisional ranking of a single matched benchmark, using measured inputs."""
from pydantic import BaseModel, Field


class Gates(BaseModel):
    min_success: int = Field(default=80, ge=0, le=100)
    min_schema: int = Field(default=95, ge=0, le=100)
    max_p95_seconds: float | None = Field(default=None, gt=0, allow_inf_nan=False)


def rank_runs(runs, gates):
    weights = {"quality": 50, "latency": 20, "cost": 20, "reliability": 10}
    use_cost = all(r.get("metrics", {}).get("provider_cost_per_success") is not None for r in runs)
    if not use_cost:
        weights.pop("cost")
    entries = []
    eligible = []
    for run in runs:
        reasons = []
        metrics = run.get("metrics", {})
        if (run.get("success_rate") or 0) * 100 < gates.min_success:
            reasons.append("Task success below threshold")
        if metrics.get("schema_rate", -1) * 100 < gates.min_schema:
            reasons.append("Schema compliance below threshold or unavailable")
        latency = run.get("p95_ms")
        if latency is None or (gates.max_p95_seconds and latency > gates.max_p95_seconds * 1000):
            reasons.append("p95 latency above threshold or unavailable")
        if metrics.get("error_rate") is None:
            reasons.append("Error rate unavailable")
        entry = {"model": run["model_id"], "reasons": reasons, "score": None}
        entries.append(entry)
        if not reasons:
            eligible.append((entry, {"quality":run["success_rate"], "latency":latency,
                "cost":metrics.get("provider_cost_per_success"), "reliability":1-metrics["error_rate"]}))
    for key in ("latency", "cost"):
        if key not in weights or not eligible:
            continue
        values = [m[key] for _, m in eligible]
        lo, hi = min(values), max(values)
        for _, m in eligible:
            m[key] = (hi-m[key])/(hi-lo) if hi > lo else 1
    for entry, metrics in eligible:
        entry["score"] = round(100*sum(metrics[k]*w for k,w in weights.items())/sum(weights.values()), 1)
    entries.sort(key=lambda e: -(e["score"] if e["score"] is not None else -1))
    return {"gates":gates.model_dump(), "weights":weights, "entries":entries, "version":"matched-v1"}
