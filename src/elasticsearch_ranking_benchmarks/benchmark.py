import copy
import json
import logging
import os
import time
from typing import Tuple

import numpy as np
from elasticsearch import Elasticsearch
from elasticsearch_ranking_benchmarks import configuration

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


def search_time_at_fetch_size(
    client: Elasticsearch, fetch_size: int, index: str, body: dict
) -> Tuple[float, int]:
    """
    Run search and measure how long it took.
    Returns tuple of system time in seconds and Elasticsearch `took` time in milliseconds.
    """
    start_t = time.time()
    body["size"] = fetch_size
    resp = client.search(
        index=index, body=body, filter_path=["took", "hits.hits.fields"]
    )
    took_ms = resp["took"]
    end_t = time.time()
    return (end_t - start_t), took_ms


def benchmark(index: str, benchmarks: dict, n: int = 10) -> dict:
    """
    Run benchmark of search BODIES on INDEX over N at each fetch size
    """
    timing = {benchmark["name"]: {"xs": [], "ys": []} for benchmark in benchmarks}
    for fetch_size in [int(x) for x in np.linspace(45, 4500, num=15)][::-1]:
        log.info(f"Benchmarking Fetch Size: {fetch_size}")
        times = {benchmark["name"]: [] for benchmark in benchmarks}
        for i in range(n):
            for benchmark in benchmarks:
                name = benchmark["name"]
                body = benchmark["body"]
                client = Elasticsearch(**benchmark["es_config"])
                t, _ = search_time_at_fetch_size(client, fetch_size, index, body)
                times[name].append(t)
        for benchmark in benchmarks:
            name = benchmark["name"]
            timing[name]["xs"].append(fetch_size)
            ts = np.array(times[name])
            timing[name]["ys"].append({"mean": np.mean(ts), "std": np.std(ts)})
    return timing


def run(index: str, benchmark_name: str, out_dir: str, sample_size: int = 20) -> None:
    """
    Run benckmark
    """
    output_dir = f"{out_dir}/{benchmark_name}"
    if not os.path.exists(output_dir):
        log.info(f"Creating directory {output_dir}")
        os.makedirs(output_dir)

    benchmark_config = configuration.BENCHMARKS[benchmark_name]
    sorting_orders = benchmark_config["sorting_orders"]
    base_body = benchmark_config["body"]

    es_benchmark_config = benchmark_config.get("elasticsearch", {})
    output_file = os.path.join(output_dir, f"timing.{benchmark_name}.{index}.json")

    benchmarks = []
    for sort_name, sort_data in sorting_orders.items():
        log.info(f"Running benchmark '{benchmark_name}'. Sort: '{sort_name}'")
        body = copy.deepcopy(base_body)
        if sort_data.get("sort"):
            body["sort"] = sort_data.get("sort")
        if sort_data.get("should"):
            body["query"]["bool"]["should"] = sort_data.get("should")
        if sort_data.get("script"):
            script = sort_data.get("script")
            body["query"] = {
                "script_score": {"query": body["query"], "script": {"source": script}}
            }
        if sort_data.get("track_total_hits"):
            body["track_total_hits"] = sort_data.get("track_total_hits")
        es_sort_config = sort_data.get("elasticsearch", {})
        es_host = es_benchmark_config.get("host") or es_sort_config.get("host")
        es_default_host_config = configuration.ES_HOSTS[es_host]
        es_config = {**es_default_host_config, **es_benchmark_config, **es_sort_config}
        benchmark_data = {"name": f"{sort_name}", "body": body, "es_config": es_config}
        benchmarks.append(benchmark_data)
    timings = benchmark(index, benchmarks, n=sample_size)
    with open(output_file, "w") as f:
        f.write(
            json.dumps(
                {"config": benchmark_config, "timing": timings, "index": index},
                indent=4,
            )
        )
    log.info(f"Wrote timing data to {output_file}")
