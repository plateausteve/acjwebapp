#!/usr/bin/env python3

import pandas as pd
from scipy.stats import fisher_exact



top = 90
data = pd.read_csv("datafile.csv")
groups = [0] # trigger for all sets
groups.extend(list(set(data["Set"]))) 
data_col_names = ["Gender", "Race/Ethnicity", "EL"] 
f = open("ind_test_results_" + str(top) + ".txt", "w")
f.write("Fisher's exact test (2-tailed) for TOP (" + str(top) + "% +) and NOT TOP frequency for each demographic variable within each group.\nUsing scipy.stats.fisher_exact() function\n\n")
f.close
f = open("ind_test_results_" + str(top) + ".txt", "a")
for group in groups:
    if group > 0:
        group_data = data.loc[data["Set"] == group]  
    else: 
        group_data = data

    # for this group and with all demographic variables/columns
    top_cdat_group = group_data.loc[data["Percentile CDAT"] >= top, :]
    not_cdat_group = group_data.loc[data["Percentile CDAT"] < top, :]
    top_obs_group = group_data.loc[data["Percentile Obs"] >= top, :] 
    not_obs_group1 = group_data.loc[pd.isnull(data["Percentile Obs"]), :]
    not_obs_group2 = group_data.loc[data["Percentile Obs"] < top, :]
    not_obs_group = pd.concat([not_obs_group1, not_obs_group2], axis = 0, sort = False) 
    for data_col_name in data_col_names: 
        # for each of the variables/columns in the list create new one-dimensional df with freq of subcategories as rows
        f_top_cdat_group = top_cdat_group.loc[:, data_col_name].value_counts()
        f_not_cdat_group = not_cdat_group.loc[:, data_col_name].value_counts()
        f_top_obs_group = top_obs_group.loc[:, data_col_name].value_counts()
        f_not_obs_group = not_obs_group.loc[:, data_col_name].value_counts()
        
        cdat_df = pd.concat([f_top_cdat_group, f_not_cdat_group], axis = 1, sort=False, keys = ["Top", "Not"]).dropna(how = "all")#.astype(dtype="int32")
        cdat_df.fillna(0, inplace=True)

        obs_df = pd.concat([f_top_obs_group, f_not_obs_group], axis = 1, sort=False, keys = ["Top", "Not"]).dropna(how = "all")#.astype(dtype="int32")
        obs_df.fillna(0, inplace=True)
        
        if group > 0:
            f.write("SET " + str(group) + ", " + data_col_name + " CDAT\n\n")
        else:
            f.write("All sets " + data_col_name + " CDAT\n\n")
        for i, dv in cdat_df.iterrows():
            f_dv_top_group = int(dv["Top"])
            f_ot_top_group = int(cdat_df.loc[:, "Top"].sum() - f_dv_top_group)
            f_dv_not_group = int(dv["Not"])
            f_ot_not_group = int(cdat_df.loc[:, "Not"].sum() - f_dv_not_group)
            contab = [[f_dv_top_group, f_ot_top_group], [f_dv_not_group, f_ot_not_group]]
            oddsratio, pvalue = fisher_exact(contab)
            contab_data = {"Top": [f_dv_top_group, f_ot_top_group], "Not": [f_dv_not_group, f_ot_not_group]}
            contab_df = pd.DataFrame(contab_data, index = [data_col_name + " " + i, data_col_name + " not " + i])
            f.write(contab_df.to_string())
            f.write("\nOddsratio: " + str(round(oddsratio, 3)) + " P-value: " + str(pvalue) + "\n\n")
        if group > 0:
            f.write("SET " + str(group) + ", " + data_col_name + " OBSERVATION\n\n")
        else:
            f.write("All sets " + data_col_name + " OBSERVATION\n\n")
        for i, dv in obs_df.iterrows():
            f_dv_top_group = int(dv["Top"])
            f_ot_top_group = int(obs_df.loc[:, "Top"].sum() - f_dv_top_group)
            f_dv_not_group = int(dv["Not"])
            f_ot_not_group = int(obs_df.loc[:, "Not"].sum() - f_dv_not_group)
            contab = [[f_dv_top_group, f_ot_top_group], [f_dv_not_group, f_ot_not_group]]
            oddsratio, pvalue = fisher_exact(contab)
            contab_data = {"Top": [f_dv_top_group, f_ot_top_group], "Not": [f_dv_not_group, f_ot_not_group]}
            contab_df = pd.DataFrame(contab_data, index = [data_col_name + " " + i, data_col_name + " not " + i])
            f.write(contab_df.to_string())
            f.write("\nOddsratio: " + str(round(oddsratio, 3)) + " P-value: " + str(pvalue) + "\n\n") 
    f.write("-----------------------------------\n\n")
f.close()
