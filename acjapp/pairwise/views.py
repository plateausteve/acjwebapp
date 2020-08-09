from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.http import HttpResponseRedirect, HttpResponse
from .models import Script, Comparison, ComparisonForm, Set
from random import sample
from django.views import generic
from numpy import log, sqrt, corrcoef
import numpy as np 
import scipy
from scipy.stats.stats import pearsonr
import operator
from operator import itemgetter


def index(request):
    return render(request, 'pairwise/index.html', {})

def compared(request):
    return render(request, 'pairwise/compared.html', {})

def compare(request):
    if request.method == 'POST':
        form = ComparisonForm(request.POST)
        if form.is_valid():
            comparison = form.save(commit=False)
            comparison.judge = request.user
            comparison.scripti = Script.objects.get(pk=request.POST.get('scripti'))
            comparison.scriptj = Script.objects.get(pk=request.POST.get('scriptj'))
            if comparison.wini==1:
                comparison.winj=0
            else:
                comparison.winj=1
            comparison.set = Set.objects.get(pk=1)
            comparison.resulting_set_corr = comparison.set.cor_est_to_actual
            comparison.save()

            #after the comparison above, update all scripts' computed fields with computations based on latest comparison
            scripts = Script.objects.all()
            a = [] #we'll use a as one vector for a correlation computation actual parameter value-- only for development
            e = [] #we'll use e as the other vector for correlation -- LO or estimated parameter value
            for script in scripts:
                #count all the comparisons each script has been involved in
                comparisons_as_i_count = Comparison.objects.filter(scripti=script).count()
                comparisons_as_j_count = Comparison.objects.filter(scriptj=script).count()
                comps = comparisons_as_i_count + comparisons_as_j_count + .001
                setattr(script, 'comps_in_set', comps)

                #count all the comparisons each script has won
                wins_as_i_count = Comparison.objects.filter(wini=1, scripti=script).count()
                wins_as_j_count = Comparison.objects.filter(winj=1, scriptj=script).count()
                wins = wins_as_i_count + wins_as_j_count
                setattr(script, 'wins_in_set', wins)
                
                #compute the probability, odds, and logodds for each script
                odds = (wins/(comps - wins))+.001
                logodds = round(log(odds), 3)
                probability = round((wins/comps), 3)
                setattr(script, 'prob_of_win_in_set', probability) 
                setattr(script, 'lo_of_win_in_set', logodds)

                #compute the standard error of sample mean and RMSE of all comparisons for script
                p = probability - .001
                v = p*(1-p)/comps
                rmse = round(sqrt(wins*v/comps),3)
                setattr(script, 'rmse_in_set', rmse)

                
                #compute the estimated parameter value--an arbitrary linear function to closely match known values
                ep = 50 + (logodds * 5)
                setattr(script, 'estimated_parameter_in_set', ep)

                #append to the array for correlation of parameter values--only for development testing
                a.append(script.parameter_value)
                e.append(ep)
                
                script.save()

            #compute new set correlation of actual and estimated parameter values
            r = round(np.corrcoef(a,e)[0][1],3)
            set = Set.objects.get(pk=1) #for now, there is only one Set object to get
            setattr(set, 'cor_est_to_actual', r)
            set.save()
        return redirect('/compare')

    
    else: #if the form is being generated for the first time send the template what it needs
        
        #select the scripti with fewest comparisons so far (or random if tied), and select the scriptj with least difference in log odds (or random if tied)
        ordered_scripts = []
        for index, script in enumerate(Script.objects.all().order_by('comps_in_set','?'), start=0): #enumerate all the instances of Script in ascending order by number of comparisons
            if index == 0:
                scripti = Script.objects.get(pk=script.id) # for first iteration only, create an object to be scripti in the current comparison, the least-compared or if tied withothers, random select among least 
                loseti = scripti.lo_of_win_in_set # use this to compute differences in subsequent iterations
                lodiff = 0
            else:
                logetj = Script.objects.get(pk=script.id) #for subsequent interations, get the object to be used for LO field value set for each scriptj candidate
                losetj = logetj.lo_of_win_in_set
                lodiff = abs(loseti - losetj) # compute the difference in LO between scripti and scriptj candidate
            ordered_scripts.append([script.id, lodiff]) #add this computed LO difference value to the list of LO differences

        #if count of comparisons is greater than count of scripts in set, then resort by LO difference
        #note: there may be a better way to determine the switch, such as the SD of the LO reaching a certain spread, or the RMSE
        compcount = Comparison.objects.all().count()
        scriptcount = 3 * Script.objects.all().count()
        if compcount > scriptcount:
            j=sorted(ordered_scripts, key=operator.itemgetter(1)) #sort the list of lists from least LO difference to greatest
        else:
            j=ordered_scripts
        scriptjselector = j[1][0] # select from the second row, second column, this is the id of the scriptj candidate with the least difference in LO to the chosen scripti
        scriptj = Script.objects.get(pk=scriptjselector) #set the scriptj candidate object
        # now both scripti and scriptj objects are set and can be returned to the compare.html template

        form = ComparisonForm()
        return render(request, 'pairwise/compare.html', {
                'j': j,
                'scripti': scripti,
                'scriptj': scriptj,
                'form': form
                } 
                )

def compare_auto(request):
    comparisons_to_do = int((Script.objects.all().count() * (Script.objects.all().count()-1)/2) - Comparison.objects.all().count())
    #do all the comparisons needed
    for i in range(comparisons_to_do):
        ordered_scripts = [] # we'll use this array to select the pair of scripts to be compared
        #loop through all scripts in order from fewest comps so far to greatest, or random if same
        for index, script in enumerate(Script.objects.all().order_by('comps_in_set','?'), start=0): #enumerate all the instances of Script in ascending order by number of comparisons
            if index == 0:
                scripti = Script.objects.get(pk=script.id) # for first iteration only, create an object to be scripti in the current comparison, the least-compared or if tied withothers, random select among least 
                loseti = scripti.lo_of_win_in_set # use this to compute differences in subsequent iterations
                lodiff = 0
            else:
                logetj = Script.objects.get(pk=script.id) #for subsequent interations, get the object to be used for LO field value set for each scriptj candidate
                losetj = logetj.lo_of_win_in_set
                lodiff = abs(loseti - losetj) # compute the difference in LO between scripti and scriptj candidate
            ordered_scripts.append([script.id, lodiff]) #add this computed LO difference value to the list of LO differences

        #if current count of comparisons is greater than count of scripts in set, then re-sort by LO difference
        #note: there may be a better way to determine the switch, such as the SD of the LO reaching a certain spread, or the RMSE
        compcount = Comparison.objects.all().count()
        scriptcount = 3 * Script.objects.all().count()
        if compcount > scriptcount:
            j=sorted(ordered_scripts, key=operator.itemgetter(1)) #sort the list of lists from least LO difference to greatest
        else:
            j=ordered_scripts
        scriptjselector = j[1][0] # select from the second row, first column, this is the id of the scriptj candidate with the least difference in LO to the chosen scripti
        scriptj = Script.objects.get(pk=scriptjselector) #set the scriptj candidate object
        # now both scripti and scriptj objects are selected, time to assign wins and losses
        if scripti.parameter_value > scriptj.parameter_value: #compare scripts using development mode param value
            wini = 1
            winj = 0
        else:
            wini = 0
            winj = 1
        judge = request.user
        set = Set.objects.get(pk=1)
        resulting_set_corr = set.cor_est_to_actual
        Comparison.objects.create(set=set, scripti=scripti, scriptj=scriptj, judge=judge, wini=wini, winj=winj, resulting_set_corr=resulting_set_corr)
        
        #after a comparison above, update all scripts' computed fields with computations based on latest comparison
        scripts = Script.objects.all()
        a = [] #we'll use a as one vector for a correlation computation actual parameter value-- only for development
        e = [] #we'll use e as the other vector for correlation -- LO or estimated parameter value
        for script in scripts:
            #count all the comparisons each script has been involved in
            comparisons_as_i_count = Comparison.objects.filter(scripti=script).count()
            comparisons_as_j_count = Comparison.objects.filter(scriptj=script).count()
            comps = comparisons_as_i_count + comparisons_as_j_count + .001
            setattr(script, 'comps_in_set', comps)

            #count all the comparisons each script has won
            wins_as_i_count = Comparison.objects.filter(wini=1, scripti=script).count()
            wins_as_j_count = Comparison.objects.filter(winj=1, scriptj=script).count()
            wins = wins_as_i_count + wins_as_j_count
            setattr(script, 'wins_in_set', wins)
            
            #compute the probability, odds, and logodds for each script
            odds = (wins/(comps - wins))+.001
            logodds = round(log(odds), 3)
            probability = round((wins/comps), 3)
            setattr(script, 'prob_of_win_in_set', probability) 
            setattr(script, 'lo_of_win_in_set', logodds)

            #compute the standard error of sample mean and RMSE of all comparisons for script
            p = probability - .001
            v = p*(1-p)/comps
            rmse = round(sqrt(wins*v/comps),3)
            setattr(script, 'rmse_in_set', rmse)

            #compute the estimated parameter value--an arbitrary linear function to closely match known values
            ep = 50 + (logodds * 5)
            setattr(script, 'estimated_parameter_in_set', ep)

            #append to the array for correlation of parameter values--only for development testing
            a.append(script.parameter_value)
            e.append(ep)
            
            #save the new script calculation based on this comparison's results
            script.save()

        #compute new set correlation of actual and estimated parameter values
        r = round(np.corrcoef(a,e)[0][1],3)
        set = Set.objects.get(pk=1) #for now, there is only one Set object to get
        setattr(set, 'cor_est_to_actual', r)
        set.save()
    return redirect('/comparisons')

class ComparisonListView(generic.ListView):
    model = Comparison

def script_list(request):
    scripts = Script.objects.all().order_by('-lo_of_win_in_set')
    set = Set.objects.get(pk=1)
    return render(request, 'pairwise/script_list.html', {'scripts': scripts, 'set': set})



def update(request):
    scripts = Script.objects.all()
    for script in scripts:
                #count all the comparisons each script has been involved in
                script_comparisons_as_i_count = Comparison.objects.filter(scripti=script.pk).count()
                script_comparisons_as_j_count = Comparison.objects.filter(scriptj=script.pk).count()
                comps = script_comparisons_as_i_count + script_comparisons_as_j_count
                setattr(script, 'comps_in_set', comps)

                #count all the comparisons each script has won
                script_wins_as_i_count = Comparison.objects.filter(wini=1, scripti=script.pk).count()
                script_wins_as_j_count = Comparison.objects.filter(winj=1, scriptj=script.pk).count()
                wins = script_wins_as_i_count + script_wins_as_j_count
                setattr(script, 'wins_in_set', wins)
                
                #compute the probability, odds, and logodds for each script
                odds = (wins/(comps - wins + .001))
                logodds = log(odds)
                notzerocomps = comps + .001
                setattr(script, 'prob_of_win_in_set', round(wins/notzerocomps,3)) 
                setattr(script, 'lo_of_win_in_set', round(logodds,3))
                script.save()
    return render(request, 'pairwise/update.html', {})

