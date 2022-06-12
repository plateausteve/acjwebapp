
# this function not currently in use. Selects 3 judges with top percent agreement when there are more than three
# when there are 0, 1, or 2 judges with comparisons for the given set it returns workable empties
# interrater percent agreement reference: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3900052/

import itertools
import pandas
from models import Comparison, Script
import numpy as np
from numpy import sqrt, re
from .utils import *

def make_groups_percentagree(setobject):
    try: # if comps exist for this set, query a list of unique judge ids who have made comparisons on this set
        judgelist = Comparison.objects.filter(set=setobject).values_list('judge_id', flat=True).distinct()
    except:
        judgelist = None
    if len(judgelist) < 2:
        bestgroup = []
        bestagreement = 0
        stats_df = None
        return bestgroup, bestagreement, stats_df

    #create scriptpairs from combinations of all scripts in set
    
    scripts = Script.objects.filter(set=setobject)
    scriptlist = []
    for script in scripts:
        scriptlist.append(script.id)
    judgecomps = {}
    # for each scriptpair add to the list of comparision judgments made by each judge-- 
    for judge in judgelist: # first iterate through all judges so you can update judge's list of comps
        column =[]
        scriptpairs = itertools.combinations(scriptlist, 2)
        for scriptpair in scriptpairs:        
            try: # get a comparison that matches that scriptpair order left and right if it exists for this judge
                comp = Comparison.objects.get(set = setobject, judge = judge, scripti__id = scriptpair[0], scriptj__id = scriptpair[1])
                row = [comp.scripti.id, comp.scriptj.id, comp.wini] 
            except:
                try: # get a comparison that matches reverse order of script pair if there is one for this judge
                    comp = Comparison.objects.get(set = setobject, judge = judge, scriptj__id = scriptpair[0], scripti__id = scriptpair[1] )
                    row = [comp.scriptj.id, comp.scripti.id]
                    if comp.wini == 1:
                        row.extend([0])
                    else:
                        row.extend([1])
                except:
                    #this judge has no matching comp in either order
                    comp = None
                    row = ([None, None, None])
            column.append(row)
        judgecomps.update({str(judge): column}) # update the dict to include the whole column
        # where each row in the column contains [scriptid, scriptid, win]

    if len(judgelist) > 2:
        combo_n = 3
    else:
        combo_n = 2
    judgegroups = itertools.combinations(judgelist, combo_n)
    judgegroupagreement = {} 
    judgegroupstats = {}
    judges=[]
    x=[]
    n=[]
    p=[]
    se=[]
    # calculate percent agreement among judges in each group
    for judgegroup in judgegroups:
        column = []
        for row in judgecomps[str(judgegroup[0])]:
            #row for first judge's list of comparisions
            flag = 0 # using this flag variable to signal any missing pair in another judge's comps
            
            if row == [None, None, None]: 
                # don't look for matching comps if the this pair hasn't been compared yet
                pass # skip this row and don't add it to the column
            else:
                #setting row_opp to the opposite decision is a clumsy way to set up to make sure the pair doesn't show up at all in other judges' comps
                if row[2] == 1:
                    row_opp = [row[0],row[1],0]
                else:
                    row_opp = [row[0],row[1],1]

                rowtally = 1 # judge agrees with self, next how about others?                
                
                if row in judgecomps[str(judgegroup[1])]:
                    rowtally += 1 # add one agreement for the second judge  
                elif row_opp not in judgecomps[str(judgegroup[1])]:
                    flag += 1 #the pair is not in second judge's list at all and signal not to add this row to the column    
                if combo_n > 2:
                    if row in judgecomps[str(judgegroup[2])]:  
                        rowtally += 1   # if there is a third judge, add one agreement for the third
                    elif row_opp not in judgecomps[str(judgegroup[2])]:
                        flag += 1 #the pair is not in the third judge's list at all and increase signal not to add this row to the column
                if flag == 0:
                    column.append(int(rowtally/combo_n)) #added Int() so it only counts 1 if all three agree, and only 0 if all three share that pair 
        judgegroupagreement.update({str(judgegroup): column})

        # calculating stats for each row and appending to list for later dictionary & dataframe 
        rowx=sum(judgegroupagreement[str(judgegroup)])
        rown=len(judgegroupagreement[str(judgegroup)])
        maxcomps = (len(scriptlist)*(len(scriptlist)-1))/2
        if rown * 20 > maxcomps: # only if n of shared comparisons > 1/20 possible comparisons
            judges.append(judgegroup) # judges is a key of the dictionary, adding to its values list
            x.append(rowx) # x will be a key, adding to values list
            n.append(rown) # n will be a key, adding to values list
            p.append(rowx/rown) # p will be a key, adding to values list
            std=np.std(judgegroupagreement[str(judgegroup)])
            se.append(std/sqrt(rown)) # se will be a key, adding to values list
        
    judgegroupstats.update({'judges': judges, "p": p,"se": se, "x": x, "n": n}) # finally, the dict. to build with keys and value lists
    
    df = pandas.DataFrame(judgegroupstats) # make a dataframe to pass to the template
    stats_df_indexkey=df.sort_values(by='p', ascending = False) # sort by p highest to lowest
    stats_df=stats_df_indexkey.set_index('judges')
    bestgroupstring = str(stats_df.index[0]) # choose first judgegroup string
    bestgroupids = re.findall('[0-9]+', bestgroupstring) # extract the numeric ids from string
    b = stats_df.iat[0, 0]
    bestagreement = round(b *100, 1)
    bestgroup = []
    for id in bestgroupids:
        bestgroup.append(int(id)) # turn the id strings into integers
    return bestgroup, bestagreement, stats_df


# Added this function for command-line use, just like make_groups above but takes judgelist as input, skips selecting best group. 
# Needs to be consolidated into above function and view if used in web app                
def group_stats(setobject, judgelist):
    if len(judgelist) < 2:
        bestgroup = []
        bestagreement = 0
        corrstats_df = None
        return bestgroup, bestagreement, corrstats_df
    #create scriptpairs from combinations of all scripts in set
    scripts = Script.objects.filter(set=setobject)
    scriptlist = []
    for script in scripts:
        scriptlist.append(script.id)
    judgecomps = {}
    # for each scriptpair add to the list of comparision judgments made by each judge-- 
    for judge in judgelist: # first iterate through all judges so you can update judge's list of comps
        column = []
        scriptpairs = itertools.combinations(scriptlist, 2)
        for scriptpair in scriptpairs:        
            try: # get a comparison that matches that scriptpair order left and right if it exists for this judge
                comp = Comparison.objects.get(set = setobject, judge = judge, scripti__id = scriptpair[0], scriptj__id = scriptpair[1])
                row = [comp.scripti.id, comp.scriptj.id, comp.wini] 
            except:
                try: # get a comparison that matches reverse order of script pair if there is one for this judge
                    comp = Comparison.objects.get(set = setobject, judge = judge, scriptj__id = scriptpair[0], scripti__id = scriptpair[1] )
                    row = [comp.scriptj.id, comp.scripti.id]
                    if comp.wini == 1:
                        row.extend([0])
                    else:
                        row.extend([1])
                except:
                    #this judge has no matching comp in either order
                    comp = None
                    row = ([None, None, None])
            column.append(row)
        judgecomps.update({str(judge): column}) # update the dict to include the whole column
        # where each row in the column contains [scriptid, scriptid, win]
    if len(judgelist) > 2:
        combo_n = 3
    else:
        combo_n = 2
    judgegroups = itertools.combinations(judgelist, combo_n)
    judgegroupagreement = {} 
    judgegroupstats = {}
    judges=[]
    x=[]
    n=[]
    p=[]
    se=[]
    # calculate percent agreement among judges in each group
    for judgegroup in judgegroups:
        column = []
        for row in judgecomps[str(judgegroup[0])]:
            #row for first judge's list of comparisions
            flag = 0 # using this flag variable to signal any missing pair in another judge's comps
            
            if row == [None, None, None]: 
                # don't look for matching comps if the this pair hasn't been compared yet
                pass # skip this row and don't add it to the column
            else:
                #setting row_opp to the opposite decision is a clumsy way to set up to make sure the pair doesn't show up at all in other judges' comps
                if row[2] == 1:
                    row_opp = [row[0],row[1],0]
                else:
                    row_opp = [row[0],row[1],1]

                rowtally = 1 # judge agrees with self, next how about others?                
                
                if row in judgecomps[str(judgegroup[1])]:
                    rowtally += 1 # add one agreement for the second judge  
                elif row_opp not in judgecomps[str(judgegroup[1])]:
                    flag += 1 #the pair is not in second judge's list at all and signal not to add this row to the column    
                if combo_n > 2:
                    if row in judgecomps[str(judgegroup[2])]:  
                        rowtally += 1   # if there is a third judge, add one agreement for the third
                    elif row_opp not in judgecomps[str(judgegroup[2])]:
                        flag += 1 #the pair is not in the third judge's list at all and increase signal not to add this row to the column
                if flag == 0:
                    column.append(int(rowtally/combo_n)) #added Int() so it only counts 1 if all three agree, and only 0 if all three share that pair 
        judgegroupagreement.update({str(judgegroup): column})

        # calculating stats for each row and appending to list for later dictionary & dataframe 
        rowx=sum(judgegroupagreement[str(judgegroup)])
        rown=len(judgegroupagreement[str(judgegroup)])
        maxcomps = (len(scriptlist)*(len(scriptlist)-1))/2
        if rown * 20 > maxcomps: # only if n of shared comparisons > 1/20 possible comparisons
            judges.append(judgegroup) # judges is a key of the dictionary, adding to its values list
            x.append(rowx) # x will be a key, adding to values list
            n.append(rown) # n will be a key, adding to values list
            p.append(rowx/rown) # p will be a key, adding to values list
            std=np.std(judgegroupagreement[str(judgegroup)])
            se.append(std/sqrt(rown)) # se will be a key, adding to values list    
    judgegroupstats.update({'judges': judges, "p": p,"se": se, "x": x, "n": n}) # finally, the dict. to build with keys and value lists
    df = pandas.DataFrame(judgegroupstats) # make a dataframe to pass to the template
    stats_df_indexkey=df.sort_values(by='p', ascending = False) # sort by p highest to lowest
    stats_df=stats_df_indexkey.set_index('judges')
    bestgroupstring = str(stats_df.index[0]) # choose first judgegroup string
    bestgroupids = re.findall('[0-9]+', bestgroupstring) # extract the numeric ids from string
    b = stats_df.iat[0, 0]
    bestagreement = round(b *100, 1)
    bestgroup = []
    for id in bestgroupids:
        bestgroup.append(int(id)) # turn the id strings into integers
    return bestgroup, bestagreement, stats_df          


def corr_matrix(setid):
    set_judge_script_rank = {}
    set_judge_script_estimate = {}
    set = Set.objects.get(pk=setid)
    for judge in set.judges.all():
        computed_scripts = get_computed_scripts(set, [judge.id])
        computed_scripts.sort(key = lambda x: x.id)
        set_judge_script_rank[judge.id]=[]
        set_judge_script_estimate[judge.id]=[]
        for script in computed_scripts:
            set_judge_script_rank[judge.id].append(script.rank)
            set_judge_script_estimate[judge.id].append(script.logit)
    rankdf = pandas.DataFrame(data = set_judge_script_rank)
    estdf = pandas.DataFrame(data = set_judge_script_estimate)
    k = rankdf.corr('kendall')
    s = rankdf.corr('spearman')
    p = estdf.corr('pearson')
    return s, k, p