from .models import Script, Comparison, Set
import numpy as np 
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
    
def ordered_scripts_by_comps(compcount, switchcount, compslist):
    ordered_scripts = []
    for index, script in enumerate(Script.objects.all().order_by('comps_in_set','?'), start=0): #enumerate all the instances of Script in ascending order by number of comparisons. Change this to RMSE if preferred.
        if index == 0: #scripti is set as the first in the ordered set
            scripti = script # for first iteration only, create an object to be scripti in the current comparison, the least-compared or if tied withothers, random select among least 
            loi = scripti.lo_of_win_in_set # use this to compute differences in subsequent iterations
            rmse = scripti.rmse_in_set
            lodiff = 0
        else: # all the others get added
            scriptj = script #temporary scriptj get and set: get the object to be used for LO field value set for each scriptj candidate
            loj = scriptj.lo_of_win_in_set
            rmse = scriptj.rmse_in_set
            lodiff = abs(loi - loj) # compute the difference in LO between scripti and scriptj candidate
            #prevent appending this combination to the ordered_scripts list when it exists already in compslist
            if [scripti.id, scriptj.id] not in compslist and [scriptj.id, scripti.id] not in compslist: 
                ordered_scripts.append([script.id, lodiff, rmse]) #add this computed LO difference value and rmse diff value to the list of differences between script i's attributes and script j's attributes
            #else skip it, eliminating duplicate comparisons.
    return scripti, ordered_scripts 


def ordered_scripts_by_rmse(compcount, switchcount, compslist):
    ordered_scripts = []
    for index, script in enumerate(Script.objects.all().order_by('-rmse_in_set','comps_in_set'), start=0): #enumerate all the instances of Script in ascending order by number of comparisons. Change this to RMSE if preferred.
        if index == 0:
            scripti = script # first time through the loop script i 
            loi = scripti.lo_of_win_in_set # use this to compute differences in subsequent iterations
            rmse = scripti.rmse_in_set
            lodiff = 0
        else:
            scriptj = script #other times through the loop scripts j
            loj = script.lo_of_win_in_set
            rmse = script.rmse_in_set
            lodiff = abs(loi - loj) # compute the difference in LO between scripti and scriptj candidate
            if [scripti.id, scriptj.id] not in compslist and [scriptj.id, scripti.id] not in compslist:
                ordered_scripts.append([script.id, lodiff, rmse]) #add this computed LO difference value and rmse diff value to the list of differences between script i's attributes and script j's attributes
    return scripti, ordered_scripts 


def script_selection():
    #select the scripti with fewest comparisons so far (or random if tied), and select the scriptj with least difference in log odds (or random if tied)
    switchcount = 20 * Script.objects.count()
    compslist = build_compslist()
    compcount = len(compslist)
    if compcount < switchcount:    # at first, select scriptj by choosing from among those with least number of comparisons
        scripti, ordered_scripts = ordered_scripts_by_comps(compcount, switchcount, compslist)
    else: #later select scriptj by choosing from among those with least LO diff to scripti
        scripti, ordered_scripts = ordered_scripts_by_rmse(compcount, switchcount, compslist)
    j=sorted(ordered_scripts, key = operator.itemgetter(1)) #sort the list of lists from least LO difference to greatest. 
    #j is an array of script.id, each script's LO difference between it and scripti, and each script's RMSE
    scriptjselector = j[0][0] # select from the first row, first column, this is the id of the scriptj candidate matching criteria
    scriptj = Script.objects.get(pk=scriptjselector) #set the scriptj candidate object
    # now both scripti and scriptj objects are set and can be returned to the compare.html template
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
        mean = wins/comps
        diffs = mean*(1-mean)/comps # SE of mean of sample (which is all comparisons so far)
        rmse = round(sqrt(wins*diffs/comps),3)
        setattr(script, 'rmse_in_set', rmse)
        
        #compute the estimated parameter value--an arbitrary linear function to closely match known values in dev or other convenient scale
        ep = round(50 + (logodds * 5),3)
        setattr(script, 'estimated_parameter_in_set', ep)

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

