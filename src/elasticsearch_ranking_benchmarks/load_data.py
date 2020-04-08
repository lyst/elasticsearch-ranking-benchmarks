import logging
import random
import sys
import uuid
from typing import Iterator

import numpy as np
from elasticsearch import Elasticsearch
from elasticsearch.helpers import streaming_bulk
from elasticsearch_ranking_benchmarks import configuration
from toolz import get_in

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

rng = random.Random(1)


def get_documents_random(n: int) -> Iterator[dict]:
    for i in range(int(n)):
        scores_uniform = {
            k: rng.random() for k in ["a", "b", "c", "d", "e", "f", "g", "h", "i"]
        }
        mu, sigma = 3.0, 1.0  # mean and standard deviation
        scores_lognormal = {
            k: np.random.lognormal(mu, sigma)
            for k in ["a", "b", "c", "d", "e", "f", "g", "h", "i"]
        }
        yield {
            "id": str(uuid.uuid4()),
            "scores": scores_uniform,
            "scores_rf": scores_lognormal,
        }


def documents_to_actions(index: str, documents: dict) -> Iterator[dict]:
    for document in documents:
        yield {
            "_index": index,
            "_type": "_doc",
            "_id": document["id"],
            "_source": document,
        }


def run(
    index: str,
    benchmark_name: str,
    document_count: int,
    shard_count: int,
    delete: bool = False,
):
    """
    """
    print(f"Index name: {index}")
    settings = configuration.SETTINGS_BASE.copy()
    settings["index"]["number_of_shards"] = shard_count
    try:
        benchmark_config = configuration.BENCHMARKS[benchmark_name]
    except KeyError:
        print(f"ERROR: No benchmark with name '{benchmark_name}'")
        print(
            "Available benchmarks: {}".format(
                ", ".join(sorted(configuration.BENCHMARKS.keys()))
            )
        )
        sys.exit(1)

    es_hosts = {
        get_in(["elasticsearch", "host"], sort_config)
        for sort_config in benchmark_config["sorting_orders"].values()
        if get_in(["elasticsearch", "host"], sort_config)
    }
    benchmark_es_host = get_in(["elasticsearch", "host"], benchmark_config)
    if benchmark_es_host:
        es_hosts.add(benchmark_es_host)

    for es_host in es_hosts:
        es_config = configuration.ES_HOSTS[es_host]
        es_config["host"] = es_host
        es = Elasticsearch(**es_config)
        es_version = es.info()["version"]["number"]
        if es_version < "7":
            print("mappings for ES6")
            mappings = configuration.MAPPINGS_ES6
        else:
            print("mappings for ES7")
            mappings = configuration.MAPPINGS_ES7
        if delete:
            print(f"Deleting index {index} on cluster {es_host}")
            es.indices.delete(index=index)
        if not es.indices.exists(index=index):
            es.indices.create(index, body=dict(settings=settings, mappings=mappings))
            print(f"Created index '{index}' on cluster {es_host}")
            documents = get_documents_random(document_count)
            actions = documents_to_actions(index, documents)
            indexed = 0
            for resp in streaming_bulk(es, actions):
                indexed += 1
                if indexed % 10000 == 0:
                    print(f"Indexed {indexed} documents")
            print(f"COMPLETE - Indexed {indexed} documents")
