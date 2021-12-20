from .models import Script, Comparison, Set
import numpy as np 
import pandas as pd
from numpy import log, sqrt, corrcoef
from scipy.stats import spearmanr, kendalltau
import operator
from operator import itemgetter
from chartit import DataPool, Chart

def compute_script_ep(logodds):
    ep = round(57.689 + (logodds * 11.826), 3)
    #modeled the actual correlation between phi and theta at 300 comps using the 7n switchcount 
    #y intercept=57.689 and slope is 11.826
    return ep

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

def script_selection():
    #select scripti, scriptj, determine orderby, get j list for display in debug info
    scriptcount = Script.objects.count()
    compslist = build_compslist()
    changelist = []
    for x in range(5): #for each of 5 selection methods do the loop to define scripti and scriptj and add to a list the resulting change
        # x selects scripti as the first in a query filtered and order_by'ed for that scripti selection method
        if x == 0: # select scripti as one with fewest comparisons so far, then random-- shown to work best from 4x to 6x count of scripts 
            scripts = enumerate(Script.objects.filter(comps_in_set__lt=scriptcount).order_by('comps_in_set', '?'), start=0)
        elif x == 1: 
           scripts = enumerate(Script.objects.filter(comps_in_set__lt=scriptcount).order_by('fisher_info', '?'), start=0)
        elif x == 2: 
            scripts = enumerate(Script.objects.filter(comps_in_set__lt=scriptcount).order_by('-se', '?'), start=0)
        elif x == 3: 
            scripts = enumerate(Script.objects.filter(comps_in_set__lt=scriptcount).order_by('-rmse_in_set', '?'), start=0)
        elif x == 4: # shown to work best from 0x to 5x and 8x up
            scripts = enumerate(Script.objects.filter(comps_in_set__lt=scriptcount).order_by('-count_same_p', '?'), start=0)
        scriptsj = [] #set an empty scriptsj list for this iteration of x
        start = 0 #this start variable allows loop to continue if the first starting point results in no pairable scriptj 
        while len(scriptsj) == 0 and start < Script.objects.count(): # when scriptj list is empty, loop through scripts to assign scripti, sortable scriptj ids, 
            for index, script in scripts: # iterate through all scripts, assigning scripti to the one at the starting point, list of others' ids as scriptj
                if index > start:
                    if [scripti.id, script.id] not in compslist and [script.id, scripti.id] not in compslist:  #no replacement 
                        loj = script.lo_of_win_in_set    
                        lodiff = abs(loi - loj) # compute the difference in LO between scripti and scriptj candidate
                        fisher_info = script.fisher_info
                        se = script.se
                        rmse = script.rmse_in_set
                        samep = script.count_same_p
                        scriptsj.append([script.id, lodiff, fisher_info, se, rmse, samep]) #j is an array of all possible scriptj's important variables
                else: # index <= start and the first iteration set scripti as first in ordered scripts list
                    scripti = script # this works because it overrides previous times scripti has been assigned as start variable increases
                    loi = script.lo_of_win_in_set
                print("x:", x, "index:", index, "start:", start, "script:", script, "length scriptsj:", len(scriptsj))
            start += 1 
        # now the while loop is done, scriptsj is a list. Add a row for this x, this scripti and this scriptj selection to changelist.
        if len(scriptsj) > 0:
            j=sorted(scriptsj, key = itemgetter(1)) # sort scriptsj by least lodiff
            scriptjselector = j[0][0] # select from the first row, first column, this is the id of the scriptj candidate matching criteria
            scriptj = Script.objects.get(pk = scriptjselector) #set the scriptj candidate object
        
            # now that scripti and scriptj are set for this iteration of x, determine how much change
            # there would be for this selection method--use for selecting best selection method

            # first set the difference between est and actual value before this pairing would occur
            idiffold = abs(scripti.estimated_parameter_in_set - scripti.parameter_value)
            jdiffold = abs(scriptj.estimated_parameter_in_set - scriptj.parameter_value)
            diffsumold = idiffold + jdiffold
            
            # next anticipate the difference between est and actual value after this pairing would occur

            # first compute which script gets the new win
            if scripti.parameter_value > scriptj.parameter_value:
                iwin = 1
                jwin = 0 
            else:
                iwin = 0
                jwin = 1
            
            # start with new comps, wins, odds, logodds, and ep for scripti
            inewcomps = scripti.comps_in_set + 1.01
            inewwins = scripti.wins_in_set + iwin
            inewodds = (inewwins /  (inewcomps - inewwins)) + .01
            inewlogodds = log(inewodds)
            inewep = compute_script_ep(inewlogodds)

            # next compute new comps, wins, odds, logodds, and ep for scriptj
            jnewcomps = scriptj.comps_in_set + 1.01
            jnewwins = scriptj.wins_in_set + jwin
            jnewodds = (jnewwins / (jnewcomps - jnewwins)) +.01
            jnewlogodds = round(log(jnewodds), 3)
            jnewep = compute_script_ep(jnewlogodds)

            print("i: ", inewcomps, inewwins, inewodds, inewlogodds, inewep, "j: ", jnewcomps, jnewwins, jnewodds, jnewlogodds, jnewep  )
            
            # next compute new differences in ep after this comparison would occur
            # add to change list to be sorted and selected at the end
            idiffnew = abs(inewep - scripti.parameter_value)
            jdiffnew = abs(jnewep - scriptj.parameter_value)
            diffsumnew = idiffnew + jdiffnew
            epchangeratio = abs(diffsumnew / (diffsumold + .01))
            changelist.append([x, epchangeratio, scripti.id, scriptj.id]) # append to change list x as index, change value, scripti id, scriptj id.
        else:
            scriptj = None
        #now all x have been tried and changelist has been created
        if len(changelist) > 0:
            xsorted = sorted(changelist, key = itemgetter(1))
            orderby = xsorted[0][0] 
            scriptiselector = xsorted[0][2]
            scriptjselector = xsorted[0][3]
            scripti = Script.objects.get(pk = scriptiselector)
            scriptj = Script.objects.get(pk = scriptjselector)
            print(changelist)
        #after all selection methods x have been tried, return the function    
        print("len(compslist):", len(compslist)," i id: ", scripti, "j id: ", scriptj, "sel method: ", orderby)
        print("got to the end of loop testing 5 sel methods")
    return compslist, scripti, scriptj, orderby, epchangeratio

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
        ep = compute_script_ep(logodds) 
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