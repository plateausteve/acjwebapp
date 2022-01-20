# Drawing Test - Django-based comparative judgement for art assessment
# Copyright (C) 2021  Steve and Ray Heil

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from .models import Script, Comparison, Set
from numpy import log, sqrt
import operator
import random
from operator import itemgetter
from chartit import DataPool, Chart
import pandas

class ComputedScript:
    def __init__(self, id, idcode, idcode_f, comps, wins, logit, probability, stdev, fisher_info, se, ep, lo95ci, hi95ci, samep, rank):
            self.id = id
            self.idcode = idcode
            self.idcode_f = idcode_f
            self.comps = int(comps)
            self.wins = wins
            self.logit = logit
            self.probability = probability
            self.stdev = stdev
            self.fisher_info = fisher_info
            self.se = se
            self.ep = ep
            self.lo95ci = lo95ci
            self.hi95ci = hi95ci
            self.samep = samep #note that samep will be negative for multiple sorting lambda in script_selection() won't do a regualr and reverse sort
            self.rank = rank 

def get_allowed_sets(userid):
    list = Set.objects.filter(judges__id__exact=userid)
    allowed_sets_ids = []
    for set in list:
        allowed_sets_ids.append(set.id)
    return allowed_sets_ids

def script_selection(set, userid):
    scriptcount = Script.objects.filter(set=set).count()
    compslist = build_compslist(set, userid)
    judges = []
    judges.append(userid)
    computed_scripts_for_user_in_set = get_computed_scripts(set, judges)
    maxcomps=(scriptcount * (scriptcount-1)/2)
    switch=min(scriptcount + (scriptcount * (scriptcount-1)/6), maxcomps)
    if len(compslist) < scriptcount: # random at the begining until comps = n, then . . . 
        random.shuffle(computed_scripts_for_user_in_set)      # random is not working yet
    elif len(compslist) < switch: #prioritize comps until comps = min of n+max/2.5 or max, then . . . 
        computed_scripts_for_user_in_set.sort(key = lambda x: (x.comps, x.samep, x.fisher_info)) # prioritize comps
    else: #prioritize samep
        computed_scripts_for_user_in_set.sort(key = lambda x: (x.samep, x.comps, x.fisher_info)) # prioritize same p
        if computed_scripts_for_user_in_set[0].samep == -1: #if all computed scripts have unique values then abort
            return compslist, None, None, [] # everything is empty    
    scriptj_possibilities = []

    # Go through all comparable scripts, and choose the first as scripti. 
    # Calculate the difference in probability between scripti and every other script
    for i, script in enumerate(computed_scripts_for_user_in_set):
        if i == 0:
            if script.comps == scriptcount-1:
                return compslist, None, None, [] # everything is empty
            scripti = Script.objects.get(pk = script.id)
            p_i = float(script.probability)
        elif [scripti.id, script.id] not in compslist and [script.id, scripti.id] not in compslist: # don't consider this scriptj if it's already been compared
            p_j = float(script.probability)
            p_diff = abs(p_i - p_j)
            scriptj_possibilities.append([script.id, p_diff])
    
    # Based on the calculated probability difference, choose the most similar script and display it on the page.
    if scriptj_possibilities: # if there are possibilities, we choose the most similar
        j_list = sorted(scriptj_possibilities, key=itemgetter(1))
        scriptj = Script.objects.get(pk = j_list[0][0]) # the item that has the smallest log odds difference (lodiff)
    else: # if there are no possibilities, we can't choose a scriptj at all. whatever recieves the request will have to deal with a NoneType
        j_list = []
        scriptj = None
    return compslist, scripti, scriptj, j_list

def get_computed_scripts(set, judges):
    computed_scripts_for_user_in_set =[]
    scripts = Script.objects.filter(set=set)
    for script in scripts:
        comps, wins = compute_comps_wins(script, judges)
        logit, probability, stdev, fisher_info, se, ep, hi95ci, lo95ci = compute_more(comps, wins)
        computed_scripts_for_user_in_set.append(
            ComputedScript(
                script.id,
                script.idcode, 
                script.idcode_f, 
                comps, 
                wins, 
                logit, 
                '{:.2f}'.format(probability), 
                '{:.2f}'.format(stdev), 
                '{:.2f}'.format(fisher_info), 
                se, 
                ep, 
                lo95ci, 
                hi95ci, 
                0, 
                0
                )
        )  
    computed_scripts_for_user_in_set = set_ranks(computed_scripts_for_user_in_set)
    return computed_scripts_for_user_in_set

def build_compslist(set, userid):
    comps = Comparison.objects.filter(set=set).filter(judge=userid)
    compslist = []
    for comp in comps:
        i = comp.scripti.id
        j = comp.scriptj.id 
        compslist.append([i, j])
    return compslist

def compute_more(comps, wins):
    #compute probability of winning for each script based on comparisons so far
    probability = wins/(comps + .001)
    #compute the standard deviation of sample and standard error of sample mean 
    stdev = sqrt(((((1 - probability) ** 2) * wins) + (((0 - probability) ** 2) * (int(comps) - wins))) / (comps + .001))
    #print(stdev)
    #compute if not all wins or all losses so far
    if (round(probability,3) == 1) or (probability <= 0):
        logit = None
        fisher_info = 0
        se = None
        ep = None
        hi95ci = None
        lo95ci = None
    else: 
        fisher_info = probability * (1 - probability) # Fisher Info is a function of probability
        se = round(1 / sqrt(wins * fisher_info),3)  # SE is a function of probability
        logit = round(log(probability/(1 - probability)),3) #logit is a function of probability
        logit_hi95ci = logit + (1.96 *se) # pretty sure SE is applied to the logit as an estimate of accuracy
        logit_lo95ci = logit - (1.96 *se)
        ep = round(100 + (logit * 15), 1)
        hi95ci = round(100 + (logit_hi95ci * 10), 1)
        lo95ci = round(100 + (logit_lo95ci * 10), 1)
    #print("p:", probability, "logit:", logit)
    return logit, probability, stdev, fisher_info, se, ep, hi95ci, lo95ci

def set_ranks(computed_scripts_for_user_in_set):
    #now decrease (for sorting later) samep by one for every script including self with matching probability and set a rank value fo each
    computed_scripts_for_user_in_set.sort(key = lambda x: x.probability, reverse=True)
    rank=0
    for script in computed_scripts_for_user_in_set:
        for match in computed_scripts_for_user_in_set:
            if match.probability == script.probability:
                match.samep -= 1
        if script.samep == -1: #if there's only one at that value, then increase rank increment 1 for next 
            rank += 1
        script.rank=rank
    return computed_scripts_for_user_in_set

def compute_comps_wins(script, judges):
    comps = .001
    wins = 0
    for judge in judges:
        #count all the comparisons each script has been involved in for user
        comparisons_as_i_for_judge_count = Comparison.objects.filter(scripti=script, judge__pk=judge).count()
        comparisons_as_j_for_judge_count = Comparison.objects.filter(scriptj=script, judge__pk=judge).count()
        
        thisjudgecomps = comparisons_as_i_for_judge_count + comparisons_as_j_for_judge_count
        #comps_display = comps/10

        #count all the comparisons this script has won
        wins_as_i_for_judge_count = Comparison.objects.filter(wini=1, scripti=script, judge__pk=judge).count()
        wins_as_j_for_judge_count = Comparison.objects.filter(wini=0, scriptj=script, judge__pk=judge).count()
        thisjudgewins = wins_as_i_for_judge_count + wins_as_j_for_judge_count
    
        comps += thisjudgecomps 
        wins += thisjudgewins
    return comps, wins

def corr_matrix(setid):
    judges = []
    set_judge_script_rank = {}
    set_judge_script_estimate = {}
    set = Set.objects.get(pk=setid)
    for judge in set.judges.all():
        judges.append(judge.id)
        computed_scripts = get_computed_scripts(set, judges)
        computed_scripts.sort(key = lambda x: x.id)
        set_judge_script_rank[judge.id]=[]
        set_judge_script_estimate[judge.id]=[]
        for script in computed_scripts:
            set_judge_script_rank[judge.id].append(script.rank)
            set_judge_script_estimate[judge.id].append(script.logit)
    rankdf = pandas.DataFrame(data = set_judge_script_rank)
    estdf = pandas.DataFrame(data = set_judge_script_estimate)
    rankcorr = rankdf.corr('kendall')
    estcorr = estdf.corr('spearman')
    return rankcorr, estcorr

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


# everything below this line is broken until new chart generator can be found or query can be generated possibly create a model just for each chart?
def get_resultschart(computed_scripts):
    resultsdata = DataPool(
        series=[{
            'options': {
                'source': Script.objects.all() #Script.objects.filter(se__lt=7).order_by('estimated_parameter_in_set')#can't get order by to affect chart x axis yet             
            },
            'terms': [
                'id',
                'estimated_parameter_in_set',
                #'lo95ci',
                #'hi95ci',
            ]
        }]
    )
    cht2= Chart(
        datasource=resultsdata,
        series_options=[{
            'options': {
                'type': 'scatter',
                'linewidth': '1',
            },
            'terms': {
                'id': [ 
                    'estimated_parameter_in_set',
                    #'lo95ci',
                    #'hi95ci',
                ],
            }
        }],
        chart_options={
            'title': {'text': 'Results'},
            'xAxis': {'title':{'text': 'Item Number'}},
            'yAxis': {'title': {'text': 'Estimated & Actual Parameter Value'}},
            'legend': {'enabled': True},
            'credits': {'enabled': True}
            }
    )
    return cht2

def get_scriptchart(computed_scripts):
    scriptdata = DataPool(
        series=[{
            'options': {
                'source':Script.objects.all() #Script.objects.filter(se__lt=7).order_by('estimated_parameter_in_set')#can't get order by to affect chart x axis yet
            },
            'terms': [
                'id',
                'se',
                'stdev',
                'count_same_p',
                'fisher_info',
                'comps_display',
            ]
        }]
    )
    cht = Chart(
        datasource=scriptdata,
        series_options=[{
            'options': {
                'type': 'scatter', 
                'lineWidth': '1',
            },
            'terms': {
                'id': [ 
                    'se', 
                    'stdev', 
                    'count_same_p',
                    'fisher_info',
                    'comps_display',
                ]
            }}
            ],
        chart_options={
            'title': {'text': 'Script Data'}, 
            'xAxis': {'title': {'text': 'Item Number'}}, 
            'yAxis': {'title': {'text': 'Computed SE, Fisher Info, & SD for Development'}}, 
            'legend': {'enabled': True}, 
            'credits': {'enabled': True}
        }
    )
    return cht
