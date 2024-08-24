# Overview
The script, biolog_proc.py, processes raw BIOLOG data files to identify the metabolites that support the growth of specfic strains. I implemented three quantitative metrics for this assessment: (1) endpoint OD; (2) area under the growth curve; and (3) specific growth rate. The specific growth rate is calculated by fitting a Logistic or Gompertz growth model to the observed OD values (see Zwietering, M.H., Jongenburger, I., Rombouts, F.M. and Van't Riet, K.J.A.E.M., 1990. Modeling of the bacterial growth curve. Applied and environmental microbiology, 56(6), pp.1875-1881, for details on these models). Each metric is evaluated based on two criteria: the average fold change of the metric (compared to negative control) must be >= `fc_cutoff`, and the p-value (based on a paried-sample t-test) must be < `pvalue_cutoff`.

# Installation
No local installation is requierd, but you will need Python3 (https://www.python.org/downloads/) to run the script in the command line. The script has been tested on Python3.9 but should work with other Python versions. The command-line parsing library `argparse` is also required. It can be easily installed by running `pip3.x install argparse` where `3.x` corresponds to the Python version you use to run the script. For example, run `pip3.9 install argparse` if you use Python3.9.

# Basic Usage
Download the Github repository and place your raw BIOLOG Excel files in the folder `input_data_folder`. You can include as many files as you like; the script will automatically detect and parse each one. The Excel file names can be arbibutary, but the sheet names must follow the format: PMX_Y_Z (where X is the PM plate number, Y is the plate replicate number, and Z is the strain name). Ensure that each sheet name is unique and appears only once across all Excel files.

To run the script, use the following command:
python3 your_script_name.py input_folder_path [optional arguments]

## Positional Argument
input_folder_path (required): Specifies the path to the folder containing the input Biolog data.

## Optional Arguments
--growth_model (optional): Specifies the growth curve model to be used for data fitting. The default model is 'Logistic'.
To use the Gompertz model, run the following command:
python3 biolog_proc.py /path/to/input_data_folder --growth_model Gompertz

--min_r2 (optional): Specifies the minimum R² required for the growth curve model fitting. The default value is 0.9.
To use a more stringent R² cutoff, run the following command:
python3 biolog_proc.py /path/to/input_data_folder --min_r2 0.95

--max_trials (optional): Sets the maximum number of trial attempts for initial guesses during the growth curve model fitting process. The default value is 50.
To use more trial attempts, run the following command:
python3 biolog_proc.py /path/to/input_data_folder --max_trials 100

--fc_cutoff (optional): Specifies the minimum mean fold change cutoff for growth determination. The default value is 1.2.
To use a more stringent cutoff for fold change, run the following command:
python3 biolog_proc.py /path/to/input_data_folder --fc_cutoff 1.5

--pvalue_cutoff (optional): Specifies the maximum p-value cutoff for growth determination. The default value is 0.05.
To use a more stringent pvalue cutoff, run the following command:
python3 biolog_proc.py /path/to/input_data_folder --pvalue_cutoff 0.01
