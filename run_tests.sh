python3 biolog_proc.py --input_path Xavier_lab_data --which_lab Joao_Xavier_MSKCC --output_file_prefix Xavier_lab_data_test
python3 biolog_proc.py \
    --growth_model Gompertz \
    --min_r2 0.95 \
    --max_trials 100 \
    --fc_cutoff 1.5 \
    --reference_strain WT \
    --which_lab Richard_Bennett_Brown \
    --input_path Bennett_lab_data \
    --output_file_prefix Bennett_lab_data_test
