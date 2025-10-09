#!/bin/bash
curr_dir="/workspaces/L5-DE-Production-Environments-T1"
rm $curr_dir/output/*
mv $curr_dir/input/processed/* $curr_dir/input/ingestion/