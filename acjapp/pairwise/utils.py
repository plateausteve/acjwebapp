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

class ComputedScript:
    def __init__(self, id, idcode, idcode_f, comps, wins, logodds, probability, rmse, stdev, fisher_info, se, ep, lo95ci, hi95ci, samep, rank):
            self.id = id
            self.idcode = idcode
            self.idcode_f = idcode_f
            self.comps = int(comps)
            self.wins = wins
            self.logodds = logodds
            self.probability = probability
            self.rmse = rmse
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
    print("here")
    scriptcount = Script.objects.filter(set=set).count()
    compslist = build_compslist(set, userid)
    computed_scripts_for_user_in_set = get_computed_scripts(set, userid)
    maxcomps=(scriptcount * (scriptcount-1)/2)
    switch=min(scriptcount + (scriptcount * (scriptcount-1)/6), maxcomps)
    if len(compslist) < scriptcount: # random at the begining until comps = n, then . . . 
        random.shuffle(computed_scripts_for_user_in_set)   
        print("random")     
    elif len(compslist) < switch: #prioritize comps until comps = min of n+max/2.5 or max, then . . . 
        computed_scripts_for_user_in_set.sort(key = lambda x: (x.comps, x.samep, x.fisher_info)) # prioritize comps
        print("prioritize comps")
    else: #prioritize samep
        computed_scripts_for_user_in_set.sort(key = lambda x: (x.samep, x.comps, x.fisher_info)) # prioritize same p
        if computed_scripts_for_user_in_set[0].samep == -1: #if all computed scripts have unique values then abort
            return compslist, None, None, [] # everything is empty
        print("prioritize samep" )
    for x in computed_scripts_for_user_in_set:
        print(x.samep, " ", x.comps, " ", x.fisher_info)
    
    scriptj_possibilities = []

    # Go through all comparable scripts, and choose the first as scripti. 
    # Calculate the difference in log odds between scripti and every other script
    for i, script in enumerate(computed_scripts_for_user_in_set):
        if i == 0:
            if script.comps == scriptcount-1:
                return compslist, None, None, [] # everything is empty
            scripti = Script.objects.get(pk = script.id)
            loi = script.logodds
        elif [scripti.id, script.id] not in compslist and [script.id, scripti.id] not in compslist: # don't consider this scriptj if it's already been compared
            loj = script.logodds
            lodiff = abs(loi-loj)
            scriptj_possibilities.append([script.id, lodiff])
    
    # Based on the calculated log odds difference, choose the most similar script and display it on the page.
    if scriptj_possibilities: # if there are possibilities, we choose the most similar
        j_list = sorted(scriptj_possibilities, key=itemgetter(1))
        scriptj = Script.objects.get(pk = j_list[0][0]) # the item that has the smallest log odds difference (lodiff)
    else: # if there are no possibilities, we can't choose a scriptj at all. whatever recieves the request will have to deal with a NoneType
        j_list = []
        scriptj = None
    return compslist, scripti, scriptj, j_list


def get_computed_scripts(set, userid):
    computed_scripts_for_user_in_set =[]
    scripts = Script.objects.filter(set=set)

    for script in scripts:
        #count all the comparisons each script has been involved in for user
        comparisons_as_i_for_user_count = Comparison.objects.filter(scripti=script, judge__pk=userid).count()
        comparisons_as_j_for_user_count = Comparison.objects.filter(scriptj=script, judge__pk=userid).count()
        
        comps = comparisons_as_i_for_user_count + comparisons_as_j_for_user_count + .001
        #comps_display = comps/10

        #count all the comparisons each script has won
        wins_as_i_for_user_count = Comparison.objects.filter(wini=1, scripti=script, judge__pk=userid).count()
        wins_as_j_for_user_count = Comparison.objects.filter(winj=1, scriptj=script, judge__pk=userid).count()
        wins = wins_as_i_for_user_count + wins_as_j_for_user_count
        
        #compute the logodds and probability for each script
        odds = (wins/(comps - wins)) + .01
        logodds = round(log(odds), 3)
        probability = round((wins/comps), 3)

        #compute the standard deviation of sample, standard error of sample mean and RMSE for script
        mean = wins/comps #same as probability, but no rounding
        diffs = mean * (1 - mean)/comps # SE of mean of sample (which is all comparisons so far)
        rmse = round(sqrt(wins * diffs / comps),3)
        stdev = round(sqrt(((((1 - mean) ** 2) * wins) + (((0 - mean) ** 2) * (comps - wins))) / comps), 3)
        
        #compute the Fisher information for probability estimate 
        fisher_info = round(comps * probability * (1 - probability) + .01, 2)
        # possible for SE of probability estimate: se = round(stdev / sqrt(comps),3)
        se = round(1 / sqrt(fisher_info), 3)
    
        #compute the MLE of parameter value--an arbitrary linear function to closely match known values in dev or other convenient scale
        #this formula is based on previous testing with greys estimated to actual value
        #modeled the actual correlation between phi and theta at 300 comps using the 7n switchcount 
        #y intercept=57.689 and slope is 11.826 using old testing development system and greysep = round(57.689 + (logodds * 11.826), 3)
        ep = round(100 + (logodds * 7), 1)
        lo95ci = round(ep - (1.96 * se), 1)
        hi95ci = round(ep + (1.96 * se), 1)

        computed_scripts_for_user_in_set.append(
            ComputedScript(
                script.id,
                script.idcode, 
                script.idcode_f, 
                comps, 
                wins, 
                logodds, 
                '{:.2f}'.format(probability), 
                '{:.3f}'.format(rmse), 
                stdev, 
                fisher_info, 
                se, 
                ep, 
                lo95ci, 
                hi95ci, 
                0, 
                0
                )
        )
    #now decrease (for sorting later) samep by one for every script including self with matching probability and set a rank value fo each
    computed_scripts_for_user_in_set.sort(key = lambda x: x.ep, reverse=True)
    rank=0
    for script in computed_scripts_for_user_in_set:
        for match in computed_scripts_for_user_in_set:
            if match.probability == script.probability:
                match.samep -= 1
        if script.samep == -1: #if there's only one at that value, then increase rank increment 1 for next 
            rank += 1
        script.rank=rank
    
    return computed_scripts_for_user_in_set

def build_compslist(set, userid):
    comps = Comparison.objects.filter(set=set).filter(judge=userid)
    compslist = []
    for comp in comps:
        i = comp.scripti.id
        j = comp.scriptj.id 
        compslist.append([i, j])
    return compslist

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
                'rmse_in_set',
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
                    'rmse_in_set',
                    'count_same_p',
                    'fisher_info',
                    'comps_display',
                ]
            }}
            ],
        chart_options={
            'title': {'text': 'Script Data'}, 
            'xAxis': {'title': {'text': 'Item Number'}}, 
            'yAxis': {'title': {'text': 'Computed SE, RMSE, Fisher Info, & SD for Development'}}, 
            'legend': {'enabled': True}, 
            'credits': {'enabled': True}
        }
    )
    return cht

