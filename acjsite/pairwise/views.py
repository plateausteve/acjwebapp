from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.http import HttpResponseRedirect, HttpResponse
from .models import Script, Comparison, ComparisonForm, Set
from random import sample
from django.views import generic
from numpy import log 
import numpy as np 
import operator
from operator import itemgetter


def index(request):
    return render(request, 'pairwise/index.html', {})

def compared(request):
    return render(request, 'pairwise/compared.html', {})

def compare(request):
    if request.method == 'POST':
        form = ComparisonForm(request.POST)
        if form.is_valid(): #of form is posted
            comparison = form.save(commit=False)
            comparison.judge = request.user
            comparison.scripti = Script.objects.get(pk=request.POST.get('scripti'))
            comparison.scriptj = Script.objects.get(pk=request.POST.get('scriptj'))
            if comparison.wini==1:
                comparison.winj=0
            else:
                comparison.winj=1
            comparison.save()

            #after the comparison above, update all scripts' computed fields with computations based on this comparison
            scripts = Script.objects.all()
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
                probability = round(((wins/comps)+.001), 3)
                setattr(script, 'prob_of_win_in_set', probability) 
                setattr(script, 'lo_of_win_in_set', logodds)
                script.save()
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

class ComparisonListView(generic.ListView):
    model = Comparison

def script_list(request):
    scripts = Script.objects.all().order_by('-lo_of_win_in_set')
    return render(request, 'pairwise/script_list.html', {'scripts': scripts, })


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

