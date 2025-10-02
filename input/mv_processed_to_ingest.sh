#!/bin/bash
curr_dir="/workspaces/L5-DE-Production-Environments-T1"
rm $curr_dir/output/*.csv.gz
mv $input_dir/input/processed/* $input_dir/input/ingestion/