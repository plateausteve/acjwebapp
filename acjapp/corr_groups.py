# /usr/bin/python3.8

import pandas
from math import nan

def main():
    pass

def make_groups(df):
    similar_groups = []
    ignore = []
    
    for col in df.columns:
        for row in df.loc[[col]]:
            if 0.7 <= df[col][row] < 1.0: # temp values to artificually create a group of 3
                if not col in ignore: # if we already have group [1, 2], we don't want [2, 1]
                    ignore.append(row) 
                    if len(similar_groups) > 0:
                        for group in similar_groups:
                            if group[0] == col:
                                if not row in group:
                                    group.append(row) # add to an existing group 
                                    #print(f"adding {row} to group {group}")                               
                            else: 
                                similar_groups.append([col, row]) # create a new group
                                #print(f"creating group [{col}, {row}] -- not first time")                            
                    else:
                        similar_groups.append([col, row])
                        #print(f"creating group [{col}, {row}] -- first time")  
    #print(df)
    return similar_groups
