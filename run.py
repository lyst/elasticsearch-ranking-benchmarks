import argparse
from elasticsearch_ranking_benchmarks import benchmark, load_data


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--benchmark-name",
        help="""The path to the body file""",
        type=str,
        required=True,
    )
    parser.add_argument(
        "--out-dir",
        help="""The output directory""",
        type=str,
        required=False,
        default="out",
    )
    parser.add_argument(
        "--sample-size",
        help="""The size of samples to take at each query size""",
        type=int,
        required=False,
        default=20,
    )
    parser.add_argument(
        "--shard-count",
        help="""The number of shards to use""",
        type=int,
        required=False,
        default=2,
    )
    parser.add_argument(
        "--delete",
        help="""Recreate the index""",
        action="store_true",
        required=False,
        default=False,
    )
    args, _ = parser.parse_known_args()
    out_dir = args.out_dir
    benchmark_name = args.benchmark_name
    shard_count = args.shard_count
    sample_size = args.sample_size
    delete = args.delete
    document_count = int(1e6)
    index = f"docs_{document_count}_{shard_count}"
    load_data.run(index, benchmark_name, document_count, shard_count, delete=delete)
    benchmark.run(index, benchmark_name, out_dir, sample_size=sample_size)


if __name__ == "__main__":
    main()
