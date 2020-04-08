import copy

ES_HOSTS = {
    "opendistro-1.4": {"port": 9504},
    "opendistro-1.1": {"port": 9505},
    "opendistro-0.10": {"port": 9506},
}

BENCHMARKS = {
    "opendistro-versions": {
        "title": "Comparing sorting float across Open Distro versions",
        "elasticsearch": {},
        "sorting_orders": {
            "1.4": {
                "sort": [{"scores.a": {"order": "desc"}}],
                "elasticsearch": {"host": "opendistro-1.4"},
            },
            "1.1": {
                "sort": [{"scores.a": {"order": "desc"}}],
                "elasticsearch": {"host": "opendistro-1.1"},
            },
            "0.10": {
                "sort": [{"scores.a": {"order": "desc"}}],
                "elasticsearch": {"host": "opendistro-0.10"},
            },
        },
        "body": {
            "from": 0,
            "query": {"bool": {"filter": {"match_all": {}}}},
            "_source": "false",
            "docvalue_fields": [{"field": "scores.a", "format": "use_field_mapping"}],
        },
    },
    "rank-features": {
        "title": "Rank features (with saturation, lognormal features)",
        "elasticsearch": {"host": "opendistro-1.1"},
        "sorting_orders": {
            "_doc": {"sort": ["_doc"]},
            "score_1": {"sort": ["_score", {"scores.a": {"order": "desc"}}]},
            "rf_5": {
                "sort": ["_score"],
                "should": [
                    {"rank_feature": {"field": "scores_rf.a"}},
                    {"rank_feature": {"field": "scores_rf.b"}},
                    {"rank_feature": {"field": "scores_rf.c"}},
                    {"rank_feature": {"field": "scores_rf.d"}},
                    {"rank_feature": {"field": "scores_rf.e"}},
                ],
            },
            "rf_4": {
                "sort": ["_score"],
                "should": [
                    {"rank_feature": {"field": "scores_rf.a"}},
                    {"rank_feature": {"field": "scores_rf.b"}},
                    {"rank_feature": {"field": "scores_rf.c"}},
                    {"rank_feature": {"field": "scores_rf.d"}},
                ],
            },
            "rf_3": {
                "sort": ["_score"],
                "should": [
                    {"rank_feature": {"field": "scores_rf.a"}},
                    {"rank_feature": {"field": "scores_rf.b"}},
                    {"rank_feature": {"field": "scores_rf.c"}},
                ],
            },
            "rf_2": {
                "sort": ["_score"],
                "should": [
                    {"rank_feature": {"field": "scores_rf.a"}},
                    {"rank_feature": {"field": "scores_rf.b"}},
                ],
            },
            "rf_1": {
                "sort": ["_score"],
                "should": [{"rank_feature": {"field": "scores_rf.a"}}],
            },
        },
        "body": {
            "from": 0,
            "query": {"bool": {"filter": {"match_all": {}}}},
            "_source": "false",
        },
    },
}


SETTINGS_BASE = {
    "index": {
        "refresh_interval": "1s",
        "number_of_replicas": "0",
        "requests.cache.enable": "false",
        "queries.cache.enabled": "false",
        "translog": {"durability": "async", "sync_interval": "1m"},
        "mapping": {"total_fields": {"limit": "2000"}},
    },
    "analysis": {},
}

MAPPINGS_BASE = {
    "dynamic": "false",
    "dynamic_templates": [
        {
            "scores": {
                "path_match": "scores.*",
                "mapping": {"type": "float", "store": "false"},
            }
        }
    ],
    "properties": {
        "id": {"fields": {"hashed": {"type": "murmur3"}}, "type": "keyword"},
        "scores": {"dynamic": "true", "type": "object"},
    },
}

# Elasticsearch v6 API needs to be nested by doc type
MAPPINGS_ES6 = {"_doc": MAPPINGS_BASE}

MAPPINGS_ES7 = copy.deepcopy(MAPPINGS_BASE)
MAPPINGS_ES7["properties"]["scores_rf"] = {"dynamic": "true", "type": "object"}
MAPPINGS_ES7["dynamic_templates"].append(
    {
        "scores_rf": {
            "path_match": "scores_rf.*",
            "mapping": {"type": "rank_feature", "store": "false"},
        }
    }
)
