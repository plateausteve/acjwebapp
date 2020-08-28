from .models import Script, Comparison, Set
import numpy as np 
import pandas as pd
from numpy import log, sqrt, corrcoef
import operator
from operator import itemgetter

def build_compslist():
    comps = Comparison.objects.all()
    compslist = []
    for comp in comps:
        i = comp.scripti.id
        j = comp.scriptj.id 
        compslist.append([i, j])
    return compslist

def order_scripts(compslist, orderby, scriptcount):
    ordered_scriptsj = []
    scriptcount -= 1
    if orderby == "rmse":
        scripts = enumerate(Script.objects.filter(comps_in_set__lt=scriptcount, se__lt=10).order_by('-rmse_in_set', 'comps_in_set', '?'), start=0)
        # enumerate all instances of Script not maxed out already, not SE of 10 (all wins or all losses), ordered by lowest SE, then lowest comps so far, then random
    elif orderby == "comps":
        scripts = enumerate(Script.objects.filter(comps_in_set__lt=scriptcount).order_by('comps_in_set', '?'), start=0)
        # enumerate all instances of Script not maxed out already, ordered by lowest comps so far, then random
    else:
        scripts = enumerate(Script.objects.filter(comps_in_set__lt=scriptcount).order_by('?'), start=0)
        # enumerate all instances of Script not maxed out already, ordered by random
    for index, script in scripts: 
        fisher_info = script.fisher_info
        se = script.se
        rmse = script.rmse_in_set
        if index > 0: #after first time through the loop do scriptjs
            scriptj = script 
            loj = script.lo_of_win_in_set    
            lodiff = abs(loi - loj) # compute the difference in LO between scripti and scriptj candidate
            if [scripti.id, scriptj.id] not in compslist and [scriptj.id, scripti.id] not in compslist:
                ordered_scriptsj.append([script.id, lodiff, fisher_info, se, rmse])
        else: # first time through the loop do scripti 
            scripti = script 
            loi = script.lo_of_win_in_set # use this to compute differences in subsequent iterations
            lodiff = 0
        #now resort the scriptj list by least lo diff that's the second row in the array
        j=sorted(ordered_scriptsj, key = operator.itemgetter(1))
        #j is an array of script.id, each script's LO difference between it and other data that only be useful in development
    return scripti, j 

def script_selection():
    #select the scripti with fewest comparisons so far (or random if tied), and select the scriptj with least difference in log odds (or random if tied)
    scriptcount = Script.objects.count()
    switchcount = 5 * scriptcount
    compslist = build_compslist()
    compcount = len(compslist)
    if compcount < switchcount: # at first, select scripti by choosing from among those with least number of comparisons
        orderby = "comps" 
    else: # later select scripti by choosing from among those with highest SE
        orderby = "rmse"    
    scripti, j = order_scripts(compslist, orderby, scriptcount)
    if len(j) > 0:
        scriptjselector = j[0][0] # select from the first row, first column, this is the id of the scriptj candidate matching criteria
        scriptj = Script.objects.get(pk=scriptjselector) #set the scriptj candidate object
        return compslist, j, scripti, scriptj
    else:
        scriptj = None # FIX: better check to see if a different scripti is available with unpaired scriptjs to compare before returning this function.
        return compslist, j, scripti, scriptj

def compute_scripts_and_save():
    scripts = Script.objects.all()
    a = [] #we'll build a as one vector for actual parameter value in a corr computation -- only for development
    e = [] #we'll build e as the other vector, the estimated parameter value for the correlation
    for script in scripts:
        #count all the comparisons each script has been involved in, including the most recent, set this attribute
        comparisons_as_i_count = Comparison.objects.filter(scripti=script).count()
        comparisons_as_j_count = Comparison.objects.filter(scriptj=script).count()
        comps = comparisons_as_i_count + comparisons_as_j_count + .001
        setattr(script, 'comps_in_set', comps)

        #count all the comparisons each script has won, set this attribute
        wins_as_i_count = Comparison.objects.filter(wini=1, scripti=script).count()
        wins_as_j_count = Comparison.objects.filter(winj=1, scriptj=script).count()
        wins = wins_as_i_count + wins_as_j_count
        setattr(script, 'wins_in_set', wins)
        
        #compute the logodds and probability for each script, set these attributes
        odds = (wins/(comps - wins)) + .001
        logodds = round(log(odds), 3)
        probability = round((wins/comps), 3)
        setattr(script, 'prob_of_win_in_set', probability) 
        setattr(script, 'lo_of_win_in_set', logodds)

        #compute the standard error of sample mean and RMSE of all comparisons for script, set this attribute
        mean = wins/comps #same as probability, but no rounding
        diffs = mean * (1 - mean)/comps # SE of mean of sample (which is all comparisons so far)
        rmse = round(sqrt(wins * diffs / comps),3)
        setattr(script, 'rmse_in_set', rmse)
        
        #compute the Fisher information and standard error for MLE parameter value 
        fisher_info = round(comps * probability * (1 - probability) + .01, 2)
        se = round(1 / sqrt(fisher_info), 3)
        

        #compute the MLE of parameter value--an arbitrary linear function to closely match known values in dev or other convenient scale
        ep = round(50 + (logodds * 10),3)
        lo95ci = round(logodds - (1.96 * sqrt(1 / fisher_info)), 3)
        hi95ci = round(logodds + (1.96 * sqrt(1 / fisher_info)), 3)
        setattr(script, 'estimated_parameter_in_set', ep)
        setattr(script, 'lo_lo95ci', lo95ci)
        setattr(script, 'lo_hi95ci', hi95ci)
        setattr(script, 'fisher_info', fisher_info)
        setattr(script, 'se', se)

        #append to the array for correlation of development-only assigned parameter values--only for development testing
        a.append(script.parameter_value)
        e.append(ep)
    
        script.save()

    #compute new set correlation of actual and estimated parameter values
    r = round(np.corrcoef(a,e)[0][1],5)
    set = Set.objects.get(pk=1) #for now, there is only one Set object to get
    setattr(set, 'cor_est_to_actual', r)
    set.save()
    return()

def compute_diffs():
    scripts = Script.objects.all()
    count = Script.objects.count()
    diffs = 0
    for script in scripts:
        diffs += abs(script.parameter_value - script.estimated_parameter_in_set)
    diffs = round(diffs/count, 3)
    return(diffs)

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