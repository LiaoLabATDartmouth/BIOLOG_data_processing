# Overview
The script, biolog_proc.py, processes BIOLOG OD measurements to identify the nutrients that support the growth of specfic strains. I implemented three quantitative metrics for this assessment: (1) endpoint OD; (2) area under the growth curve; and (3) specific growth rate. The specific growth rate is calculated by fitting a Logistic or Gompertz growth model to the observed OD values (see this [paper](https://journals.asm.org/doi/10.1128/aem.56.6.1875-1881.1990) for details of these models). For each growth metric, the growth/no growth status is evaluated based on two criteria: the average fold change of the metric (compared to negative control) must be >= `fc_cutoff`, and the p-value (based on a paried-sample t-test) must be < `pvalue_cutoff`.

# Installation
No local installation is requierd, but you will need Python3 (https://www.python.org/downloads/) to run the script in the command line. The script has been tested on Python3.9 but should work with other Python3 versions. The command-line parsing library `argparse` is also required. It can be easily installed by running `pip3.x install argparse` where `3.x` corresponds to the Python version you use to run the script. For example, run `pip3.9 install argparse` if you use Python3.9.

# Basic Usage
Download the Github repository and place your raw BIOLOG data files in a folder. You will have the opportunity to specify the folder path using the `--input_path` argument (see below). In this folder, you can include as many files as you like; the script will automatically detect and parse each one. __The Excel file names can be arbituary, but the sheet names must follow the format: PMX_Y_Z (where X is the PM plate number, Y is the plate replicate number, and Z is the strain name)__. Ensure that each sheet name is unique and appears only once across all Excel files.

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

'--output_file_prefix': Specifies the prefix of output file name. The default value is 'output'.
If you prefer a different prefix name, run the following command:
`python3 biolog_proc.py --output_file_prefix Xavier_lab_data_test`

`--reference_strain`: Specifies the reference strain to which all other strains are compared against. The default value is None.
To specify a reference strain, run the following command:
`python3 biolog_proc.py --reference_strain WT`

`--which lab`: Specifies the laboratory where the OD measurements were performed. The default value is Joao_Xavier_MSKCC.
__As the raw data format varies depending on the plate reader and its setup, this script is customized to read machine-output data specific to each laboratory. Currently, we support the Richard Bennett Lab (Richard_Bennett_Brown) and the Joao Xavier Lab (Joao_Xavier_MSKCC).__
For Richard Bennett lab members, run the following command:
`python3 biolog_proc.py --which_lab Richard_Bennett_Brown`

__Note: You can specify multiple arguments the same time. For example, if you want use non-default values for both `fc_cutoff` and `pvalue_cutoff`, run the following command: `python3 biolog_proc.py --fc_cutoff 1.5 --pvalue_cutoff 0.01`.__

# Ouput Formats
The script outputs a single Excel file named `[output_file_prefix].%Y%m%d_%H%M%S.xlsx` (%Y: year, %m: month, %d: day, %H: hour, %M: minute, %S: second). When running the script, you can specify the prefix of output file name using the `--output_file_perfix' argument. Typically, the output file contains three sheets: `Full_report`, `Comparison_growth_quali`, and `Comparison_growth_quant`.

The `Full_report` sheet includes the following columns:
- Strain: Name of the strain
- Plate: Plate number (e.g., 'PM1', 'PM2A')
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
- CurveFit_R2: The R2 value between the observed OD and the best-fitting model. It is the first R2 value that exceeds `min_r2` among all initial guess trials. If all R2 values remain below `min_r2`, a linear regression model will be applied to reestimate the specific growth rate and its R2 value. If the estimated growth rate is negative, it will be set to 0.001, and the corresponding R2 value will be set to `nan`.
- SGR: Specific growth rate (unit 1/hour) in each replicate (values separated by semicolons).
- SGR_Mean: SGR averaged across replicates
- SGR_MeanFC: Ratio of SGR between the current well and the A1 well (negative control), averaged across replicates
- SGR_Pvalue: Paired-sample t-test of SGR between the current well and the A1 well
- GrowthStatus: For each metric, positive growth (`+`) is assigned when the mean fold change is >= `fc_cutoff` and the p-value is < `pvalue_cutoff`. Otherwise, negative growth ('-') is assigned. The growth status of all three metrics is then combined into a 3-letter string in the order of Endpoint approach, AUC approach, SGR approach. For example, `++-` indicates positive growth determined by the endpoint OD approach and AUC approach, but negative growth determined by the SGR approach.

The `Comparison_growth_quali` sheet reformats the `GrowthStatus` column from the `Full_report` sheet to faciliate growth status comparison across strains. It lists only the metabolites where at least one strain shows positive growth as determined by at least one approach.

The `Comparison_growth_quant` sheet compares each growth metric between individual strains and a user-specified reference strain (see the `--reference_strain` argument). If no reference strain is provided, no comparisons will be performed, and this sheet will not be included in the output file. For each comparison, the sheet reports the fold change in mean growth metric values and p-values from an independent sample Welch’s t-test.
