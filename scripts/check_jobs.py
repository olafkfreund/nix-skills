#!/usr/bin/env python3
"""Fail the aggregate status unless every required Check job succeeded."""

import json
import os


def validate(results):
    if set(results) != {"check", "collection", "distribution"} or any(
            job.get("result") != "success" for job in results.values()):
        raise ValueError(f"Required checks did not all succeed: {results}")


if __name__ == "__main__":
    validate(json.loads(os.environ["CHECK_RESULTS"]))
    print("All required collection, distribution and provider jobs passed")
