from .models import Script, Comparison, Set
import numpy as np 
import pandas as pd
from numpy import log, sqrt, corrcoef
from scipy.stats import spearmanr, kendalltau
import operator
from operator import itemgetter
from chartit import DataPool, Chart

def compute_last_comparison_after_calcs():
    diffs = compute_diffs()
    r = compute_corr()
    comparison=Comparison.objects.last()
    setattr(comparison, 'resulting_set_corr', r)
    setattr(comparison, 'average_diff_est_act', diffs)
    comparison.save()
    return diffs, r

def compute_same_p():
    scriptsp=Script.objects.all()
    for script in scriptsp:
        count=Script.objects.filter(prob_of_win_in_set=script.prob_of_win_in_set).count()
        setattr(script, 'count_same_p', count)
        script.save()
    return()

def build_compslist():
    comps = Comparison.objects.all()
    compslist = []
    for comp in comps:
        i = comp.scripti.id
        j = comp.scriptj.id 
        compslist.append([i, j])
    return compslist

def compute_corr():
    scripts = Script.objects.all()
    a = [] #we'll build a as one vector for actual parameter value in a corr computation -- only for development
    e = [] #we'll build e as the other vector, the estimated parameter value for the correlation
    for script in scripts:
        a.append(script.parameter_value)
        e.append(script.estimated_parameter_in_set)
    #compute new set correlation of actual and estimated parameter values
    # r = round(np.corrcoef(a,e)[0][1],3) disabled momentarily to try the kendalltau rank correlation
    #r, p = spearmanr(a,e) the rank correlation coefficient seems too inflated to be helpful
    r = round(kendalltau(a, e) [0],3)
    set = Set.objects.get(pk=1) #for now, there is only one Set object to get
    setattr(set, 'cor_est_to_actual', r)
    set.save()
    return(r)

def compute_diffs():
    scripts = Script.objects.all()
    count = Script.objects.count()
    diffs = 0
    for script in scripts:
        diffs += abs(script.parameter_value - script.estimated_parameter_in_set)
    diffs = round(diffs/count*100, 3)
    return(diffs)

def order_scripts(compslist, orderby, scriptcount):
    #select scripti as the first in a query with filter and order_by
    if orderby == 1: # select scripti as one with fewest comparisons so far, then random PROMISING
        scripts = enumerate(Script.objects.filter(comps_in_set__lt=scriptcount).order_by('comps_in_set', '?'), start=0)
    elif orderby == 2: 
        scripts = enumerate(Script.objects.filter(comps_in_set__lt=scriptcount).order_by('fisher_info', '?'), start=0)
    elif orderby == 3: 
        scripts = enumerate(Script.objects.filter(comps_in_set__lt=scriptcount).order_by('-se', '?'), start=0)
    elif orderby == 4: 
        scripts = enumerate(Script.objects.filter(comps_in_set__lt=scriptcount).order_by('-rmse_in_set', '?'), start=0)
    elif orderby == 5: # promising
        scripts = enumerate(Script.objects.filter(comps_in_set__lt=scriptcount).order_by('-count_same_p', '?'), start=0)
    
    ordered_scriptsj = []
    for index, script in scripts: 
        if index == 0: # first iteration set selected scripti as first in ordered scripts list
            scripti = script
            loi = script.lo_of_win_in_set
        else: # create an array of ordered scripts for scriptj selection
            scriptj = script 
            loj = script.lo_of_win_in_set    
            lodiff = abs(loi - loj) # compute the difference in LO between scripti and scriptj candidate
            fisher_info = script.fisher_info
            se = script.se
            rmse = script.rmse_in_set
            samep = script.count_same_p
            if [scripti.id, scriptj.id] not in compslist and [scriptj.id, scripti.id] not in compslist: #no replacement after selection of a pair
                ordered_scriptsj.append([script.id, lodiff, fisher_info, se, rmse, samep])
        #now resort the scriptj list by least of designated column in the array, the column determined by orderby 1:lodiff; 2:fisher_info; 3: se; 4:rmse; 5:samep
        #j=sorted(ordered_scriptsj, key = itemgetter(orderby)) 
        j=sorted(ordered_scriptsj, key = itemgetter(1)) #j is an array of script.id, LO diff, fisher info, se & rmse all possible pairs for scripti
    return scripti, j 

def script_selection():
    #select scripti
    scriptcount = Script.objects.count()
    compslist = build_compslist()
    compcount = len(compslist)
    orderby = 5
    scripti, j = order_scripts(compslist, orderby, scriptcount)
    if len(j) > 0:
        scriptjselector = j[0][0] # select from the first row, first column, this is the id of the scriptj candidate matching criteria
        scriptj = Script.objects.get(pk=scriptjselector) #set the scriptj candidate object
    else:
        scriptj = None # FIX: better check to see if a different scripti is available with unpaired scriptjs to compare before returning this function.
    return compslist, j, scripti, scriptj, orderby

def compute_scripts_and_save():
    scripts = Script.objects.all()
    a = [] #we'll build a as one vector for actual parameter value in a corr computation -- only for development
    e = [] #we'll build e as the other vector, the estimated parameter value for the correlation
    for script in scripts:
        #count all the comparisons each script has been involved in, including the most recent, set this attribute
        comparisons_as_i_count = Comparison.objects.filter(scripti=script).count()
        comparisons_as_j_count = Comparison.objects.filter(scriptj=script).count()
        comps = comparisons_as_i_count + comparisons_as_j_count + .01
        setattr(script, 'comps_in_set', comps)
        setattr(script, 'comps_display', comps/10)

        #count all the comparisons each script has won, set this attribute
        wins_as_i_count = Comparison.objects.filter(wini=1, scripti=script).count()
        wins_as_j_count = Comparison.objects.filter(winj=1, scriptj=script).count()
        wins = wins_as_i_count + wins_as_j_count
        setattr(script, 'wins_in_set', wins)
        
        #compute the logodds and probability for each script, set these attributes
        odds = (wins/(comps - wins)) + .01
        logodds = round(log(odds), 3)
        probability = round((wins/comps), 3)
        setattr(script, 'prob_of_win_in_set', probability) 
        setattr(script, 'lo_of_win_in_set', logodds)

        #compute the standard deviation of sample, standard error of sample mean and RMSE for script, set this attribute
        mean = wins/comps #same as probability, but no rounding
        diffs = mean * (1 - mean)/comps # SE of mean of sample (which is all comparisons so far)
        rmse = round(sqrt(wins * diffs / comps),3)
        stdev = round(sqrt(((((1 - mean) ** 2) * wins) + (((0 - mean) ** 2) * (comps - wins))) / comps), 3)
        setattr(script, 'rmse_in_set', rmse)
        setattr(script, 'stdev', stdev)
        
        #compute the Fisher information for probability estimate 
        fisher_info = round(comps * probability * (1 - probability) + .01, 2)
        # possible for SE of probability estimate: se = round(stdev / sqrt(comps),3)
        se = round(1 / sqrt(fisher_info), 3)
        setattr(script, 'fisher_info', fisher_info)
        setattr(script, 'se', se)
    
        #compute the MLE of parameter value--an arbitrary linear function to closely match known values in dev or other convenient scale
        ep = round(57.689 + (logodds * 11.826),3) 
        #modeled the actual correlation between phi and theta at 300 comps using the 7n switchcount 
        #y intercept=57.689 and slope is 11.826
        lo95ci = round(ep - (1.96 * se), 3)
        hi95ci = round(ep + (1.96 * se), 3)
        setattr(script, 'estimated_parameter_in_set', ep)
        setattr(script, 'lo95ci', lo95ci)
        setattr(script, 'hi95ci', hi95ci)

        script.save()
    #compute, set, and save attributes for all scripts that depend on above calculations
    compute_same_p() #this saves all scripts with newly computed same p count
    r = compute_corr() #this saves the new resulting set correlation
    return

def build_btl_array():
    scriptsx = Script.objects.all()
    scriptsy = Script.objects.all()
    btl_array = []
    for scripti in scriptsx:
        row = []
        loi = scripti.lo_of_win_in_set
        for scriptj in scriptsy:
            loj = scriptj.lo_of_win_in_set
            lodiff = round(loi - loj,3)
            btl = round(np.exp(lodiff)/(1 + np.exp(lodiff)), 2) #probability that scripti will beat scriptj according to BTL Model
            row.append(btl)
        row = pd.Series(row)
        btl_array.append(row)
    df = pd.DataFrame(btl_array)
    return btl_array, df

def get_resultschart():
    resultsdata = DataPool(
        series=[{
            'options': {
                'source': Script.objects.filter(se__lt=7)             
            },
            'terms': [
                'id',
                'estimated_parameter_in_set',
                #'lo95ci',
                #'hi95ci',
                'parameter_value',
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
                    'parameter_value',
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

def get_scriptchart():
    scriptdata = DataPool(
        series=[{
            'options': {
                'source': Script.objects.filter(se__lt=7)
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