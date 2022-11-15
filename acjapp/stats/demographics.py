import pandas as pd

data = pd.read_csv("stats/datafile.csv")
all_sets = list(set(data["Set"]))
all_demg = list(set(data["Race/Ethnicity"]))
all_demg.sort()
d = {}
i = 0
for one_set in all_sets:
    i += 1
    this_set = data.loc[data["Set"] == one_set]
    these_demg = list(set(this_set["Race/Ethnicity"]))
    d.update({"set": one_set})
    for demg in all_demg:
        if demg in these_demg:
            n = len(this_set.loc[this_set["Race/Ethnicity"] == demg].axes[0])
            p = round(n / len(this_set.axes[0]), 3) * 100
        else:
            n = 0
            p = 0
        d.update({
            f"{demg} n": [n],
            f"{demg} p": [p]
            })
    df = pd.DataFrame.from_dict(d)
    if i == 1:
        df1 = df
    else: 
        df1 = pd.concat([df1, df])
df1.set_index('set', inplace=True)
df1.to_csv("demog_table.csv") 
print(df1)


