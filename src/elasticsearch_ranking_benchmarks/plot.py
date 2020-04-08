import json
import os

import numpy as np


def benchmark_fig(benchmark_name, title=None, out_dir="out"):
    """
    Get plotly figure data for a benchmark
    """
    timing_data = []
    dirname = f"{out_dir}/{benchmark_name}"
    for filename in sorted(os.listdir(dirname)):
        timing_data.append(json.loads(open(os.path.join(dirname, filename)).read()))

    data = []
    for timings in timing_data:
        for name, d in timings["timing"].items():
            xs = d["xs"]
            ys = np.array([y_i["mean"] for y_i in d["ys"]]) * 1000
            error_y = {
                "type": "data",
                "array": np.array([y_i["std"] for y_i in d["ys"]]) * 1000,
            }
            trace = {"x": xs, "y": ys, "name": name, "error_y": error_y}
            data.append(trace)

    y_max = max([y for trace in data for y in trace["y"]])
    title = timing_data[0].get("config", {}).get("title") or title or ""
    title = f"Benchmark: <b>{title}</b>"
    layout = {
        "title": title,
        "template": "plotly_white",
        "xaxis": {"title": "fetch size"},
        "yaxis": {
            "title": "search time (ms)",
            "domain": [0.1, 1],
            "range": [0, y_max * 1.1],
        },
        "width": 914,
        "height": 600,
        "legend_orientation": "h",
    }
    fig = {"data": data, "layout": layout}
    return fig
