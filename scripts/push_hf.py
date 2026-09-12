#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Mirror data/ and the dataset card to Hugging Face.

    HF_TOKEN=hf_... uv run --with huggingface_hub scripts/push_hf.py [--repo forzagreen/ar-verbs]

GitHub is canonical; this copies data/jsonl, data/csv, data/json and README.md
into the dataset repo, creating it (public) if it does not exist. Run after
scripts/build_dataset.py and scripts/validate.py.
"""
import argparse
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--repo", default="forzagreen/ar-verbs")
    ap.add_argument("--message", default="Update dataset")
    args = ap.parse_args()
    token = os.environ.get("HF_TOKEN")
    if not token:
        sys.exit("set HF_TOKEN (a write token from https://huggingface.co/settings/tokens)")
    from huggingface_hub import HfApi
    api = HfApi(token=token)
    api.create_repo(args.repo, repo_type="dataset", exist_ok=True)
    api.upload_folder(
        repo_id=args.repo, repo_type="dataset", folder_path=ROOT, path_in_repo=".",
        allow_patterns=["README.md", "data/json/*", "data/jsonl/*", "data/csv/*", "docs/*"],
        commit_message=args.message,
    )
    print("pushed to https://huggingface.co/datasets/" + args.repo)


if __name__ == "__main__":
    main()
