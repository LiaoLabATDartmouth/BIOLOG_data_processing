##################################
# Written by Chen Liao, 08/23/2024
##################################

import numpy as np # type: ignore
import pandas as pd # type: ignore
import time
from datetime import datetime
import os
import re
from scipy.integrate import simpson # type: ignore
from scipy.stats import ttest_ind, ttest_rel, linregress # type: ignore
import random
random.seed(42)
from scipy.optimize import curve_fit # type: ignore
import argparse
from sklearn.metrics import r2_score
import warnings
warnings.filterwarnings('ignore')

# sort the columns using the custom key
def custom_sort_key(column):
    match = re.match(r"([A-Z]+)(\d+)", column)
    if match:
        return (match.group(1), int(match.group(2)))

#   find the longest string
def longest_string(strings):
    return max(strings, key=len)

#   custom type function to enforce a float range
def float_in_range(min_val, max_val):
    def range_checker(value):
        try:
            value = float(value)
        except ValueError:
            raise argparse.ArgumentTypeError(f"{value} is not a valid float")
        if not (min_val <= value <= max_val):
            raise argparse.ArgumentTypeError(f"{value} is out of range ({min_val} to {max_val})")
        return value
    return range_checker

#   custom type function to enforce an integer range
def integer_in_range(min_val, max_val):
    def range_checker(value):
        try:
            value = int(value)
        except ValueError:
            raise argparse.ArgumentTypeError(f"{value} is not a valid integer")
        if not (min_val <= value <= max_val):
            raise argparse.ArgumentTypeError(f"{value} is out of range ({min_val} to {max_val})")
        return value
    return range_checker


#   two growth curve models are defined
def Gompertz_growth_model(x, A, lag, mu):
    return A*np.exp(-np.exp(mu*np.exp(1)/A*(lag-x)+1))

def Logistic_growth_model(x, A, lag, mu):
    return A/(1+np.exp(4*mu/A*(lag-x)+2))

#   get R2 coefficient between observed growth curve and the best model fit
def get_r2_coef(function, popt, x, y):
    y_pred = function(x, *popt)
    return r2_score(y_pred=y_pred, y_true=y)

#   fitting growth curve model parameters
def fit_model_parameters(xdata, ydata, model):
    init_guess = [random.random(), random.random(), random.random()]
    try:
        if model == 'Logistic':
            best_fits, covar = curve_fit(
                Logistic_growth_model,
                xdata,
                ydata,
                p0=init_guess,
                bounds = ([0,0,0], [np.inf,xdata[-1],10]),
                maxfev=10000
            )
            r2 = get_r2_coef(Logistic_growth_model, best_fits, xdata, ydata)
        elif model == 'Gompertz':
            best_fits, covar = curve_fit(
                Gompertz_growth_model,
                xdata,
                ydata,
                p0=init_guess,
                bounds = ([0,0,0], [np.inf,xdata[-1],10]),
                maxfev=10000
            )
            r2 = get_r2_coef(Gompertz_growth_model, best_fits, xdata, ydata)
        return True, best_fits, r2
    except:
        return False, [np.nan] * len(init_guess), np.nan

#   read OD measurements from a specific Excel sheet
def read_OD_measurement(file_path, sheet_name, which_lab):
    df = pd.read_excel(file_path, header=None, sheet_name=sheet_name)
    if which_lab == 'Joao_Xavier_MSKCC':
        # the start row is the first row with keyword Cycle Nr.
        # the end row is the first full blank row after the start row
        if "Cycle Nr." in list(df[0]):
            start_row = df[df[0] == "Cycle Nr."].index[0]
            df_blank_rows = df[df.isna().all(axis=1)]
            end_row = df.index[-1]
            for idx in df_blank_rows.index:
                if idx >= start_row:
                    end_row = idx
                    break
            df = df.iloc[start_row:end_row+1, 1:].drop(2, axis=1).set_index(1)
        elif "Time" in list(df[0]):
            start_row = df[df[0] == "Time"].index[0]
            df_blank_rows = df[df.isna().all(axis=1)]
            end_row = df.index[-1]
            for idx in df_blank_rows.index:
                if idx >= start_row:
                    end_row = idx
                    break
            df = df.iloc[start_row:end_row+1, :].drop(1, axis=1).set_index(0)
        else:
            raise Exception("The data block must begin with 'Cycle Nr.' or 'Time'. Check data in sheet %s from file %s."%(sheet_name, file_path))

        # use the first row as header
        df.columns = df.iloc[0]
        df = df[1:]
        df = df.dropna(how='all')

        # rename time
        baseline_time = df.index[0]
        if isinstance(baseline_time, (int, np.int64, float)):
            # by default the unit is second
            df = df.rename({df.index[i]:float(df.index[i]-baseline_time)/3600.0 for i in range(len(df))})
        elif isinstance(baseline_time, str) and bool(re.fullmatch(r"\d+s", baseline_time)):
            # the unit is specified as second
            df = df.rename({idx:int(idx.replace("s","")) for idx in df.index})
            baseline_time = df.index[0]
            df = df.rename({df.index[i]:float(df.index[i]-baseline_time)/3600.0 for i in range(len(df))})
        else:
            raise Exception("The time unit cannot be parsed. Check data in sheet %s from file %s."%(sheet_name, file_path))
        df.index.name = None
    elif which_lab == 'Richard_Bennett_Brown':
        # find the start and end row of biolog data
        start_row = df[df[0] == 600].index[0] + 2
        end_row = df[df[0] == 'Results'].index[0] -2

        # get biolog data
        df = df.iloc[start_row:end_row+1, 1:].drop(2, axis=1).set_index(1)
        df.columns = df.iloc[0]
        df = df[1:]

        # rename time
        datetime1 = datetime.combine(datetime.min, df.index[1])
        datetime2 = datetime.combine(datetime.min, df.index[0])
        delta_t = (datetime1 - datetime2).total_seconds()/3600
        df = df.rename({df.index[i]:i*delta_t for i in range(len(df))})
        df.index.name = None
    else:
        raise Exception("Unrecognized lab format. Please contact Chen Liao for support.")

    return df

#   load OD measurements from all Excel files and sheets in a given folder
def load_all_OD_measurements(folder_path, which_lab):

    # get all excel files
    all_file_paths = []
    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.endswith('.xlsx'):
                all_file_paths.append(os.path.join(root, file))

    # read data into pandaframes
    all_data_frames = []
    for file_path in all_file_paths:
        try:
            sheet_names = pd.ExcelFile(file_path).sheet_names
        except:
            raise Exception("Close all Excel sheets and try again.")

        for sheet_name in sheet_names:
            # read specific excel sheet
            df = read_OD_measurement(file_path, sheet_name, which_lab)

            # unstack data frame
            df = df.stack().reset_index()
            df.columns = ['Time','Well','OD']
            df = df[df.OD.notnull()]

            # append metadata
            plate = sheet_name.split('_')[0]
            replicate = sheet_name.split('_')[1]
            strain = sheet_name.split('_')[2]
            df['Plate'] = plate
            df['Replicate'] = replicate
            df['Strain'] = strain

            # save data
            all_data_frames.append(df)

    # merge all data frames into one
    df_merged = pd.concat(all_data_frames)

    # add metabolite name
    biolog_info = []
    for plate in set(df_merged.Plate):
        df_plate = pd.read_csv("biolog_plate_info/%s_info.csv"%plate)
        biolog_info.append(df_plate)
    df_biolog_info = pd.concat(biolog_info)
    df_merged = pd.merge(
        df_merged,
        df_biolog_info[['Metabolite','Plate','Well']],
        left_on=['Plate','Well'],
        right_on=['Plate','Well'],
        how='left'
    )

    return df_merged[['Strain','Plate','Replicate','Well','Metabolite','Time','OD']]

#--------------
# main function
#--------------
if __name__ == "__main__":
    # create the parser
    parser = argparse.ArgumentParser(description="command-line argument parser")

    # add arguments
    parser.add_argument('--input_path', type=str, default="input_data", help='Path to the folder containing the input BIOLOG Excel files')
    parser.add_argument('--growth_model', type=str, default='Logistic', choices=['Logistic', 'Gompertz'], help='Choose between Logistic and Gompertz for modeling growth curve')
    parser.add_argument('--min_r2', type=float_in_range(0.0, 1.0), default=0.90, help='Minimum R2 for growth curve model fitting')
    parser.add_argument('--max_trials', type=integer_in_range(1, 10000), default=50, help='Maximum number of trial attempts of initial guesses for growth curve model fitting')
    parser.add_argument('--fc_cutoff', type=float_in_range(1.0, np.inf), default=1.2, help='Minimum mean fold change for positive growth phenotype')
    parser.add_argument('--pvalue_cutoff', type=float_in_range(0.0, 1.0), default=0.05, help='Maximum P-value for positive growth phenotype')
    parser.add_argument('--output_file_prefix', type=str, default="output", help='Prefix of output file name')
    parser.add_argument('--reference_strain', type=str, default="", help='Reference strain to which all other strains are compared against')
    parser.add_argument('--which_lab', type=str, default="Joao_Xaviver_MSKCC", help='The laboratory where OD data was measured')

    # parse the arguments
    args = parser.parse_args()

    # read input files
    df_input = load_all_OD_measurements(args.input_path, args.which_lab)
    df_input.Time = df_input.Time.astype(float)
    df_input.OD = df_input.OD.astype(float)

    # processing results are stored in res
    all_res = []

    # iterate over all combinations of strains, plates, and wells
    all_strains = list(df_input.drop_duplicates('Strain').Strain)
    for strain in all_strains:
        all_plates = list(df_input[df_input.Strain==strain].drop_duplicates('Plate').sort_values('Plate').Plate)
        for plate in all_plates:
            # determine end time point as the last common time point across replicates
            df_A1 = df_input[(df_input.Strain==strain) & (df_input.Plate==plate) & (df_input.Well=='A1')] # negative control well
            df_A1_endpoints = df_A1.groupby('Replicate')['Time'].max().reset_index()
            last_common_time = df_A1_endpoints.Time.min()

            # analyze growth curve for each well
            neg_ctr_final_od = None # OD at the last time point
            neg_ctr_auc = None # area under the cruve
            neg_ctr_sgr = None # specific growth rate

            all_wells = list(df_input[(df_input.Strain==strain) & (df_input.Plate==plate)].drop_duplicates('Well').Well)
            all_wells = sorted(all_wells, key=custom_sort_key) # make sure that wells are processed from A to H and 1 to 12 in order
            # print(all_wells)
            for well in all_wells:
                df_well = df_input[(df_input.Strain==strain) & (df_input.Plate==plate) & (df_input.Well==well)]
                metabolite = df_well.Metabolite.values[0]
                all_replicates = list(df_well.drop_duplicates('Replicate').sort_values('Replicate').Replicate)

                # For each replicate, if last_common_time is not in the data, add this time point with interpolation
                for rep in all_replicates:
                    df_well_rep = df_well[df_well.Replicate==rep]
                    if last_common_time not in list(df_well_rep.Time):
                        od_at_last_common_time = np.interp(last_common_time, df_well_rep['Time'].to_numpy(), df_well_rep['OD'].to_numpy())
                        new_row_df = pd.DataFrame({'Strain': [strain], 'Plate': [plate], 'Replicate': [rep], 'Well': [well], 'Metabolite':[metabolite], 'Time': [last_common_time], 'OD': [od_at_last_common_time]})
                        df_well = pd.concat([df_well, new_row_df], ignore_index=True)

                # remove time points after last_common_time
                df_well = df_well[df_well.Time <= last_common_time].sort_values(['Replicate', 'Time'])
                curr_well_res = [strain, plate, well, metabolite, last_common_time]

                #-------------------
                # end point approach
                #-------------------
                curr_well_final_od = df_well[df_well.Time==last_common_time].sort_values('Replicate').OD.to_numpy()
                curr_well_final_od = np.round(curr_well_final_od.astype(float), 3)
                if (well == 'A1') or ((plate == 'PM4A') and (well == 'F1')):
                    neg_ctr_final_od = curr_well_final_od.copy()
                    fold_change_final_od = [1.0] * len(neg_ctr_final_od)
                    pvalue_final_od = np.nan
                else:
                    fold_change_final_od = curr_well_final_od/neg_ctr_final_od
                    pvalue_final_od = ttest_rel(curr_well_final_od, neg_ctr_final_od, alternative='greater')[1]
                curr_well_res.extend([",".join(map(str, curr_well_final_od)), np.mean(curr_well_final_od), np.mean(fold_change_final_od), np.round(pvalue_final_od, 6)])

                #---------------------
                # area under the curve
                #---------------------
                curr_well_auc_list = []
                for rep in all_replicates:
                    xdata = df_well[df_well.Replicate==rep].Time.to_numpy()
                    ydata = df_well[df_well.Replicate==rep].OD.to_numpy()
                    area = simpson(y=ydata, x=xdata)
                    curr_well_auc_list.append(area)
                curr_well_auc = np.array(curr_well_auc_list)
                curr_well_auc = np.round(curr_well_auc.astype(float), 3)
                if (well == 'A1') or ((plate == 'PM4A') and (well == 'F1')):
                    neg_ctr_auc = curr_well_auc.copy()
                    fold_change_auc = [1.0] * len(neg_ctr_auc)
                    pvalue_auc = np.nan
                else:
                    fold_change_auc = curr_well_auc/neg_ctr_auc
                    pvalue_auc = ttest_rel(curr_well_auc, neg_ctr_auc, alternative='greater')[1]
                curr_well_res.extend([",".join(map(str, curr_well_auc)), np.mean(curr_well_auc), np.mean(fold_change_auc), np.round(pvalue_auc, 6)])

                #---------------------------
                # growth curve model fitting
                #---------------------------
                curr_well_sgr_list = []
                curr_well_r2_list = []
                for rep in all_replicates:
                    xdata = df_well[df_well.Replicate==rep].Time.to_numpy().astype(float)
                    ydata = df_well[df_well.Replicate==rep].OD.to_numpy().astype(float)
                    log_rely = np.log(ydata/ydata[0])

                    # try random initial guesses
                    max_r2 = 0
                    n = 0
                    while (max_r2 < args.min_r2) & (n < args.max_trials):
                        _ok, _optp, _r2 = fit_model_parameters(xdata, log_rely, args.growth_model)
                        if _ok:
                            optp = _optp
                            if _r2 > max_r2:
                                max_r2 = _r2
                        n += 1
                    if n < args.max_trials:
                        curr_well_sgr_list.append(optp[2]) # A, lag, mu
                        curr_well_r2_list.append(max_r2)
                    else:
                        # use the simplest model instead
                        slope, _, rvalue, _, _ = linregress(xdata, log_rely)
                        if slope < 0.0:
                            slope = 0.001
                            rvalue = np.nan
                        curr_well_sgr_list.append(slope)
                        curr_well_r2_list.append(rvalue ** 2)

                curr_well_sgr = np.array(curr_well_sgr_list)
                curr_well_sgr = np.round(curr_well_sgr.astype(float), 3)
                curr_well_r2 = np.array(curr_well_r2_list)
                curr_well_r2 = np.round(curr_well_r2.astype(float), 3)
                if (well == 'A1') or ((plate == 'PM4A') and (well == 'F1')):
                    neg_ctr_sgr = curr_well_sgr.copy()
                    fold_change_sgr = [1.0] * len(neg_ctr_sgr)
                    pvalue_sgr = np.nan
                else:
                    fold_change_sgr = curr_well_sgr/neg_ctr_sgr
                    # remove nan in both current and A1 well data before calculating p value
                    non_nan_indices = ~np.isnan(curr_well_sgr) & ~np.isnan(neg_ctr_sgr)
                    filtered_curr_well_sgr = curr_well_sgr[non_nan_indices]
                    filtered_neg_ctr_sgr = neg_ctr_sgr[non_nan_indices]
                    pvalue_sgr = ttest_rel(filtered_curr_well_sgr, filtered_neg_ctr_sgr, alternative='greater')[1]
                curr_well_res.extend([",".join(map(str, curr_well_r2)), ",".join(map(str, curr_well_sgr)), np.nanmean(curr_well_sgr), np.nanmean(fold_change_sgr), np.round(pvalue_sgr, 6)])

                #-------------
                # save results
                #-------------
                all_res.append(curr_well_res)

    #-----------------------------------
    # generate a detailed summary report
    #-----------------------------------
    df_all_res = pd.DataFrame(all_res,
                              columns=['Strain','Plate','Well','Metabolite','LastCommonTime',
                                       'EOD','EOD_Mean','EOD_MeanFC','EOD_Pvalue',
                                       'AUC','AUC_Mean','AUC_MeanFC','AUC_Pvalue',
                                       'CurveFit_R2', 'SGR','SGR_Mean','SGR_MeanFC','SGR_Pvalue'
                                       ])

    # determine growth status based on fold change and pvalue cutoffs
    growth_status = []
    for fod_fc, fod_pv, auc_fc, auc_pv, sgr_fc, sgr_pv in zip(df_all_res.EOD_MeanFC, df_all_res.EOD_Pvalue, df_all_res.AUC_MeanFC, df_all_res.AUC_Pvalue, df_all_res.SGR_MeanFC, df_all_res.SGR_Pvalue):
        status_str = ''
        if (fod_fc >= args.fc_cutoff) and (fod_pv < args.pvalue_cutoff):
            status_str += '+'
        else:
            status_str += '-'
        if (auc_fc >= args.fc_cutoff) and (auc_pv < args.pvalue_cutoff):
            status_str += '+'
        else:
            status_str += '-'
        if (sgr_fc >= args.fc_cutoff) and (sgr_pv < args.pvalue_cutoff):
            status_str += '+'
        else:
            status_str += '-'
        growth_status.append(status_str)
    df_all_res['GrowthStatus'] = growth_status

    #-------------------------------------------------
    # Compare qualitative growth status across strains
    #-------------------------------------------------
    df_gs = df_all_res.copy()
    df_gs = df_gs[['Strain','Plate','Metabolite','GrowthStatus']]
    df_gs = pd.pivot_table(df_gs, index=['Plate','Metabolite'], columns='Strain', values='GrowthStatus', aggfunc=longest_string).fillna('---')
    df_gs = df_gs[~(df_gs == '---').all(axis=1)]
    all_strains = list(df_gs.columns)
    for strain in all_strains:
        df_gs[strain + '_EOD'] = [status[0] for status in df_gs[strain]]
        df_gs[strain + '_AUC'] = [status[1] for status in df_gs[strain]]
        df_gs[strain + '_SGR'] = [status[2] for status in df_gs[strain]]
    df_gs = df_gs.reset_index().drop(all_strains, axis=1)

    #---------------------------------------------------
    # Compare quantitative growth metrics across strains
    #---------------------------------------------------
    if args.reference_strain is not None:
        res_stats = []
        for metric in ['EOD', 'AUC', 'SGR']:
            df_metric = df_all_res.copy()
            df_metric = df_metric[['Strain','Plate','Metabolite'] + [metric]]
            df_metric = pd.pivot_table(df_metric, index=['Plate','Metabolite'], columns='Strain', values=metric, aggfunc='first').fillna('')

            all_strains = list(df_metric.columns)
            if args.reference_strain not in all_strains:
                continue

            for idx in df_metric.index:
                ref_strain_values = df_metric.loc[idx, args.reference_strain]
                if ref_strain_values != '':
                    ref_strain_values = eval(df_metric.loc[idx, args.reference_strain])
                    for curr_strain in all_strains:
                        if curr_strain != args.reference_strain:
                            curr_strain_values = df_metric.loc[idx, curr_strain]
                            if curr_strain_values != '':
                                curr_strain_values = eval(df_metric.loc[idx, curr_strain])

                                # compare current strain values against reference strain values
                                fold_change = np.mean(curr_strain_values) / np.mean(ref_strain_values)
                                ttest_pvalue = ttest_ind(curr_strain_values, ref_strain_values, equal_var=False, alternative='greater')[1] # Welch's t-test
                                res_stats.append([
                                    idx[0],        # plate
                                    idx[1],        # metabolite
                                    curr_strain,   # strain
                                    metric,        # metric
                                    fold_change,   # fold change
                                    ttest_pvalue   # pvalue
                                ])
        df_stats = pd.DataFrame(res_stats, columns = ["Plate","Metabolite","Strain","Metric","FoldChange","Pvalue"])

    #-------------------
    # save to excel file
    #-------------------
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    with pd.ExcelWriter(f"%s.{timestamp}.xlsx"%(args.output_file_prefix), engine='openpyxl') as writer:
        df_all_res.to_excel(writer, sheet_name='Full_report', index=False)
        df_gs.to_excel(writer, sheet_name='Comparison_growth_quali', index=False)
        if len(df_stats) > 0:
            df_stats.to_excel(writer, sheet_name='Comparison_growth_quant', index=False)

