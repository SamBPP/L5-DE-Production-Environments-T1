#!/bin/bash
repo_root="$(git rev-parse --show-toplevel)"
rm $repo_root/output/*
mv $repo_root/input/processed/* $repo_root/input/ingestion/