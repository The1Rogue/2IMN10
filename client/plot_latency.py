import csv, pathlib, statistics
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np

CSV = pathlib.Path("/out/latency_phase2.csv")
PNG = pathlib.Path("/out/latency_phase2.png")

xs, ys, colors = [], [], []
cached_flags = []

with CSV.open("r", encoding="utf-8") as f:
    r = csv.DictReader(f)
    for row in r:
        xs.append(int(row["req_id"]))
        y = float(row["client_latency_ms"])
        ys.append(y)
        cached = str(row["cached"]).strip().lower() in ("true","1","yes")
        cached_flags.append(cached)
        colors.append("tab:green" if cached else "tab:blue")

avg = statistics.mean(ys)

p95 = float(np.percentile(np.array(ys), 95, interpolation="linear"))

plt.figure(figsize=(7.5, 4.8))
plt.title("Phase 2: Client-perceived execution latency per request")
plt.xlabel("Request #")
plt.ylabel("Latency (ms)")
plt.grid(True, alpha=0.3)

for x, y, c in zip(xs, ys, colors):
    plt.scatter([x], [y], s=60, c=[c])

plt.axhline(avg, color="gray", linestyle="--", linewidth=1, label=f"Avg = {avg:.2f} ms")
plt.axhline(p95, color="black", linestyle=":", linewidth=1, label=f"P95 = {p95:.2f} ms")

legend_elems = [
    Line2D([0],[0], marker='o', color='w', markerfacecolor='tab:blue',  markersize=8, label='Uncached'),
    Line2D([0],[0], marker='o', color='w', markerfacecolor='tab:green', markersize=8, label='Cached'),
]

handles = legend_elems + [
    Line2D([0],[0], color='gray', linestyle='--', label=f'Avg = {avg:.2f} ms'),
    Line2D([0],[0], color='black', linestyle=':', label=f'P95 = {p95:.2f} ms'),
]

plt.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=2, frameon=False)

plt.tight_layout()
plt.savefig(PNG, dpi=160, bbox_inches="tight")
print(f"Saved {PNG}")
