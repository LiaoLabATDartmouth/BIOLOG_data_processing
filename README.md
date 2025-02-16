# Overview
The script, biolog_proc.py, processes raw BIOLOG data files to identify the metabolites that support the growth of specfic strains. I implemented three quantitative metrics for this assessment: (1) endpoint OD; (2) area under the growth curve; and (3) specific growth rate. The specific growth rate is calculated by fitting a Logistic or Gompertz growth model to the observed OD values (see Zwietering, M.H., Jongenburger, I., Rombouts, F.M. and Van't Riet, K.J.A.E.M., 1990. Modeling of the bacterial growth curve. Applied and environmental microbiology, 56(6), pp.1875-1881, for details on these models). Each metric is evaluated based on two criteria: the average fold change of the metric (compared to negative control) must be >= `fc_cutoff`, and the p-value (based on a paried-sample t-test) must be < `pvalue_cutoff`.

__Since the raw BIOLOG data format varies depending on the plate reader and its setup, this script is customized to read machine-output data specific to each lab. Currently, we support the Richard Bennett Lab and the Joao Xavier Lab. Test examples for both labs are also provided.__

# Installation
No local installation is requierd, but you will need Python3 (https://www.python.org/downloads/) to run the script in the command line. The script has been tested on Python3.9 but should work with other Python3 versions. The command-line parsing library `argparse` is also required. It can be easily installed by running `pip3.x install argparse` where `3.x` corresponds to the Python version you use to run the script. For example, run `pip3.9 install argparse` if you use Python3.9.

# Basic Usage
Download the Github repository and place your raw BIOLOG Excel files in the folder `input_data_folder`. You can include as many files as you like; the script will automatically detect and parse each one. __The Excel file names can be arbituary, but the sheet names must follow the format: PMX_Y_Z (where X is the PM plate number, Y is the plate replicate number, and Z is the strain name)__. Ensure that each sheet name is unique and appears only once across all Excel files.

To run the script, type the following command in the command line:

__Python3 (or Python3.x) biolog_proc.py [optional arguments]__

`[optional_arguments]` indicates that you can use the script's default settings without providing any arguments. So the simplest command would be `Python3 (or Python3.x) biolog_proc.py`.

# Optional Arguments
`--input_path`: Specifies the path to the folder containing the input Biolog data. The default path is `input_data_folder`.
To use a different folder, such as `/Users/chenliao/Desktop/BIOLOG`, run the following command:
`python3 biolog_proc.py --input_path /Users/chenliao/Desktop/BIOLOG`

`--growth_model`: Specifies the growth curve model to be used for data fitting. The default model is 'Logistic'.
To use the Gompertz model, run the following command:
`python3 biolog_proc.py --growth_model Gompertz`

`--min_r2`: Specifies the minimum R² required for a successful growth curve fitting. The default value is 0.9.
To use a more stringent R² cutoff, run the following command:
`python3 biolog_proc.py --min_r2 0.95`

`--max_trials`: Specifies the maximum number of trial attempts for initial guesses during growth curve fitting. The default value is 50.
To increase the number of trial attempts, run the following command:
`python3 biolog_proc.py --max_trials 100`

`--fc_cutoff`: Specifies the minimum mean fold change for a positive growth phenotype. The default value is 1.2.
To use a more stringent fold change cutoff, run the following command:
`python3 biolog_proc.py --fc_cutoff 1.5`

`--pvalue_cutoff`: Specifies the maximum p-value for a positive growth phenotype. The default value is 0.05.
To apply a more stringent p-value cutoff, run the following command:
`python3 biolog_proc.py --pvalue_cutoff 0.01`

__Note: You can specify multiple arguments the same time. For example, if you want use non-default values for both `fc_cutoff` and `pvalue_cutoff`, run the following command: `python3 biolog_proc.py --fc_cutoff 1.5 --pvalue_cutoff 0.01`.__

# Ouput Formats
The script outputs a single Excel file named `output_%Y%m%d_%H%M%S.xlsx` (%Y: year, %m: month, %d: day, %H: hour, %M: minute, %S: second). The file contains two sheets: `All` and `Summary`.

The `All` sheet includes the following columns:
- Strain: Name of the strain
- Plate: Plate number ('PM1', 'PM2A', 'PM3B', 'PM4A')
- Well: Well ID (e.g., A5, C3)
- Metabolite: Name of the metabolite in the well
- LastCommonTime: The common end time point (unit hour) across all replicates
- EOD: Endpoint OD in each replicate (values separated by semicolons)
- EOD_Mean: Endpoint OD averaged across replicates
- EOD_MeanFC: Ratio of the endpoint OD between the current well and the A1 well (negative control), averaged across replicates
- EOD_Pvalue: Paired-sample t-test of the endpoint OD between the current well and the A1 well
- AUC: Area under the curve (unit hour*OD600) in each replicate	(values separated by semicolons)
- AUC_Mean: AUC averaged across replicates
- AUC_MeanFC: Ratio of AUC between the current well and the A1 well (negative control), averaged across replicates
- AUC_Pvalue: Paired-sample t-test of AUC between the current well and the A1 well
- CurveFit_R2: R2 value between the observed OD and the best model fit. It is the R2 value that first exceeds `min_r2` among all initial guess trials. If all R2 values remain below `min_r2` throughout the trials, the maximum R2 value from these trials is reported.
- SGR: Specific growth rate (unit 1/hour) in each replicate (values separated by semicolons). __If `CurveFit_R2` is less than `min_r2` for a specific well, its corresponding SGR value is set to NaN__.
- SGR_Mean: SGR averaged across replicates
- SGR_MeanFC: Ratio of SGR between the current well and the A1 well (negative control), averaged across replicates
- SGR_Pvalue: Paired-sample t-test of SGR between the current well and the A1 well
- GrowthStatus: For each metric, positive growth (`+`) is assigned when the mean fold change is >= `fc_cutoff` and the p-value is < `pvalue_cutoff`. Otherwise, negative growth ('-') is assigned. The growth status of all three metrics is then combined into a 3-letter string in the order of Endpoint approach, AUC approach, SGR approach. For example, `++-` indicates positive growth determined by the endpoint OD approach and AUC approach, but negative growth determined by the SGR approach.

The `Summary` sheet reformats the `GrowthStatus` column from the `All` sheet to faciliate growth status comparison across strains. It lists only the metabolites where at least one strain shows positive growth as determined by at least one approach.
