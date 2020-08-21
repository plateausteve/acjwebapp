from .models import Script, Comparison, Set
import numpy as np 
from numpy import log, sqrt, corrcoef
import operator
from operator import itemgetter

#def no_duplicate_pairings():
#   figure out how to prevent duplicate pairings wherever there is an ordered_scripts variable
#both of the ordered_scripts_by. .. functions below need a guard against selecting a pair that has already been done.
#after an ordered_scripts is made perhaps it checks each and deletes it if a similar combination has been done before?
def order_scripts_by_comps(compcount, scriptcount):
    ordered_scripts = []
    for index, script in enumerate(Script.objects.all().order_by('comps_in_set','?'), start=0): #enumerate all the instances of Script in ascending order by number of comparisons. Change this to RMSE if preferred.
        if index == 0:
            scripti = Script.objects.get(pk=script.id) # for first iteration only, create an object to be scripti in the current comparison, the least-compared or if tied withothers, random select among least 
            loi = scripti.lo_of_win_in_set # use this to compute differences in subsequent iterations
            rmse = scripti.rmse_in_set
            lodiff = 0
        else:  
            scriptj = Script.objects.get(pk=script.id) #temporary scriptj get and set: get the object to be used for LO field value set for each scriptj candidate
            loj = scriptj.lo_of_win_in_set
            rmse = scriptj.rmse_in_set
            lodiff = abs(loi - loj) # compute the difference in LO between scripti and scriptj candidate
        ordered_scripts.append([script.id, lodiff, rmse]) #add this computed LO difference value and rmse diff value to the list of differences between script i's attributes and script j's attributes
    #this is where the check against previously paired happens and deletes them from the list of lists
    return scripti, ordered_scripts 


def ordered_scripts_by_rmse(compcount, scriptcount):
    ordered_scripts = []
    for index, script in enumerate(Script.objects.all().order_by('-rmse_in_set','comps_in_set'), start=0): #enumerate all the instances of Script in ascending order by number of comparisons. Change this to RMSE if preferred.
        if index == 0:
            scripti = Script.objects.get(pk=script.id) # for first iteration only, create an object to be scripti in the current comparison, the least-compared or if tied withothers, random select among least 
            loi = scripti.lo_of_win_in_set # use this to compute differences in subsequent iterations
            rmse = scripti.rmse_in_set
            lodiff = 0
        else:
            scriptj = Script.objects.get(pk=script.id) #temporary scriptj get and set: get the object to be used for LO field value set for each scriptj candidate
            loj = scriptj.lo_of_win_in_set
            rmse = scriptj.rmse_in_set
            lodiff = abs(loi - loj) # compute the difference in LO between scripti and scriptj candidate
        ordered_scripts.append([script.id, lodiff, rmse]) #add this computed LO difference value and rmse diff value to the list of differences between script i's attributes and script j's attributes
    #this is where the check against previously paired happens and deletes them from the list of lists
    return scripti, ordered_scripts 


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
        odds = (wins/(comps - wins))+.001
        logodds = round(log(odds), 3)
        probability = round((wins/comps), 3)
        setattr(script, 'prob_of_win_in_set', probability) 
        setattr(script, 'lo_of_win_in_set', logodds)

        #compute the standard error of sample mean and RMSE of all comparisons for script, set this attribute
        p = probability - .001
        variance = p*(1-p)/comps
        rmse = round(sqrt(wins*variance/comps),3)
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

def script_selection():
    #select the scripti with fewest comparisons so far (or random if tied), and select the scriptj with least difference in log odds (or random if tied)
    compcount = Comparison.objects.all().count()
    scriptcount = 3 * Script.objects.all().count()
    if compcount < scriptcount:    # at first, select scripti by choosing from among those with least number of comparisons
        scripti, ordered_scripts = ordered_scripts_by_comps(compcount, scriptcount)
    else: #later select scripti by choosing from among those with greatest RMSE
        scripti, ordered_scripts = ordered_scripts_by_rmse(compcount, scriptcount)
    if compcount < scriptcount:
        j=ordered_scripts
    else:
        j=sorted(ordered_scripts, key=operator.itemgetter(1)) #sort the list of lists from least LO difference to greatest. For RMSE difference
    #j is an array of script.id, each script's LO difference between it and scripti, and each script's RMSE
    scriptjselector = j[1][0] # select from the second row, first column, this is the id of the scriptj candidate with the least difference in LO to the chosen scripti
    scriptj = Script.objects.get(pk=scriptjselector) #set the scriptj candidate object
    # now both scripti and scriptj objects are set and can be returned to the compare.html template
    return j, scripti, scriptj

