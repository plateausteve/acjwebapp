from django.shortcuts import render, redirect, get_object_or_404
from datetime import datetime
from django.utils import timezone
from django.urls import reverse
from django.http import HttpResponseRedirect, HttpResponse
from .models import Script, ScriptForm, Comparison, ComparisonForm, Set, AutoComparisonForm, WinForm
from random import sample
from django.views import generic
from .utils import compute_scripts_and_save, script_selection, compute_diffs, compute_corr, compute_last_comparison_after_calcs, build_btl_array, get_scriptchart, get_resultschart
import operator
from operator import itemgetter
import numpy as np

def index(request):
    return render(request, 'pairwise/index.html', {})

def compared(request):
    return render(request, 'pairwise/compared.html', {})

def script_detail(request, pk):
    script=get_object_or_404(Script, pk=pk)
    return render(request, 'pairwise/script_detail.html', {'script': script})


def script_add(request):
    if request.method == "POST":
        form = ScriptForm(request.POST)
        if form.is_valid():
            script = form.save(commit=False)
            script.user = request.user
            script.save()
            return redirect('script_detail', pk=script.pk)
    else:
        form = ScriptForm()
    return render(request, 'pairwise/script_edit.html', {'form': form})

def script_edit(request, pk):
    script = get_object_or_404(Script, pk=pk)
    if request.method == "POST":
        form = ScriptForm(request.POST, instance=script)
        if form.is_valid():
            script = form.save(commit=False)
            script.user = request.user
            script.save()
            return redirect('script_detail', pk=script.pk)
    else:
        form = ScriptForm(instance=script)
    return render(request, 'pairwise/script_edit.html', {'form': form, 'script': script})

def script_list(request):
    script_table = Script.objects.all().order_by('-lo_of_win_in_set')
    set = Set.objects.get(pk=1)
    if request.method == 'POST': #if the auto-compare button has been clicked to get us here
        form = AutoComparisonForm(request.POST)
        if form.is_valid():
            comparison = form.save(commit=False)
            comparison.judge = request.user
            comparison.scripti = Script.objects.get(pk=request.POST.get('scripti'))
            comparison.scriptj = Script.objects.get(pk=request.POST.get('scriptj'))
            comparison.set = Set.objects.get(pk=1) #for now there is only one set object
            comparison.resulting_set_corr = comparison.set.cor_est_to_actual
            comparison.select_method = request.POST.get('select_method')
            start = timezone.now()
            end = timezone.now() #use datetime instead of timezone because of conversion from timestamp
            comparison.decision_end = end
            comparison.decision_start = start
            duration = end - start
            comparison.duration = duration
            #set winj value to the opposite of wini
            if comparison.scripti.parameter_value > comparison.scriptj.parameter_value:
                comparison.winj=0 
                comparison.wini=1
            else:
                comparison.winj=1
                comparison.wini=0
            #after the comparison above, update all scripts' computed fields with computations based on latest comparison, also set correlation
            compute_scripts_and_save()
            diffs, r = compute_last_comparison_after_calcs()      
        return redirect('/script_list')

    else: #if the form is being generated for the first time send the template what it needs, i.e. which two scripts to compare
        compslist, scripti, scriptj, orderby, epchangeratio, j = script_selection()
        listcount = len(compslist)
        diffs = compute_diffs()
        cht = get_scriptchart()
        cht2 = get_resultschart()
        form = AutoComparisonForm()
        
        return render(request, 'pairwise/script_list.html', {
                'listcount': listcount,
                'scripti': scripti,
                'scriptj': scriptj,
                'form': form,
                'script_table': script_table, 
                'set': set,
                'diffs': diffs,
                'chart_list': [cht, cht2],
                'orderby': orderby,
                } 
                )

def compare(request):
    if request.method == 'POST': #if submitting comparison form in order to arrive here 
        form = ComparisonForm(request.POST)
        if form.is_valid():
            comparison = form.save(commit=False)
            comparison.judge = request.user
            comparison.scripti = Script.objects.get(pk=request.POST.get('scripti'))
            comparison.scriptj = Script.objects.get(pk=request.POST.get('scriptj'))
            comparison.set = Set.objects.get(pk=1) #for now there is only one set object
            comparison.resulting_set_corr = comparison.set.cor_est_to_actual
            comparison.select_method = request.POST.get('select_method')
            comparison.difficulty_rating = comparison.difficulty_rating
            comparison.interest_rating = comparison.interest_rating
            comparison.uninterrupted = comparison.uninterrupted
            start = comparison.form_start_variable # still a float from form
            starttime = datetime.fromtimestamp(start) #convert back to datetime
            end = datetime.now() #use datetime instead of timezone because of conversion from timestamp
            comparison.decision_end = end
            comparison.decision_start = starttime
            duration = end - starttime
            comparison.duration = duration

            #set winj value to the opposite of wini
            if comparison.wini==1:
                comparison.winj=0 
            else:
                comparison.winj=1
            diffs, r = compute_last_comparison_after_calcs() 
        return redirect('/compare')

    else: #if the form is being generated for the first time send the template what it needs
        compslist, scripti, scriptj, orderby, epchangeratio, j = script_selection() 
        listcount = len(compslist)
        diffs = compute_diffs()
        set = Set.objects.get(pk=1)
        now = datetime.now() # use datetime not timezone in order to keep it the same through to other side of form 
        starttime = now.timestamp
        #figure out how to check that there are no more pairings for others either to prevent early abort
        if len(j) > 0: #as long as there are pairings available keep comparing
            form = WinForm()
            return render(request, 'pairwise/compare.html', {
                    'listcount': listcount,
                    'scripti': scripti,
                    'scriptj': scriptj,
                    'form': form,
                    'set': set,
                    'diffs': diffs,
                    'starttime': starttime,
                    'orderby': orderby,
                    } 
                )
        else: # when no more comparisons are available, stop and send to Script List page
            script_table = Script.objects.all().order_by('-lo_of_win_in_set')
            form = AutoComparisonForm()
            return render(request, 'pairwise/script_list.html', {
                'listcount': listcount,
                'scripti': scripti,
                'scriptj': scriptj,
                'form': form,
                'script_table': script_table, 
                'set': set,
                'diffs': diffs,
                } 
            )

def compare_all(request):
    Comparison.objects.all().delete()
    comparisons_to_do = Script.objects.count() * 10 #save for later int((Script.objects.all().count() * (Script.objects.all().count()-1)/2) - Comparison.objects.all().count())
    set = Set.objects.get(pk=1)
    #do all the comparisons determined
    for x in range(comparisons_to_do):
        compslist, scripti, scriptj, orderby, epchangeratio = script_selection()
        listcount = len(compslist)
        # now both scripti and scriptj objects are selected, time to assign wins and losses
        if scriptj is not None: #only move ahead if j isn't an empty list
            if scripti.parameter_value > scriptj.parameter_value: #compare scripts using development mode param value
                wini = 1
                winj = 0
            else:
                wini = 0
                winj = 1
            judge = request.user
            start = timezone.now()
            end = timezone.now()
            duration = end - start
            #create a new comparison with all variables that can be set before computing other variables
            Comparison.objects.create(
                set=set, 
                scripti=scripti, 
                scriptj=scriptj, 
                judge=judge, 
                wini=wini, 
                winj=winj, 
                decision_end=end, 
                decision_start=start, 
                duration=duration,
                select_method=orderby,
                epchangeratio=epchangeratio,
                )
            #calculate remaining variables for the newly created comparison record, now that the needed info is stored there.
            compute_scripts_and_save()
            diffs, r = compute_last_comparison_after_calcs()
            
    script_table = Script.objects.all().order_by('-lo_of_win_in_set')
    form = AutoComparisonForm()
    cht = get_scriptchart()
    cht2 = get_resultschart()

    return render(request, 'pairwise/script_list.html', {
        'listcount': listcount,
        'compslist': compslist,
        'scripti': scripti,
        'scriptj': scriptj,
        'form': form,
        'script_table': script_table, 
        'set': set,
        'diffs': diffs,
        'chart_list': [cht, cht2],
        'orderby': orderby,
        } 
        )

def compare_auto(request):
    comparisons_to_do = Script.objects.count() # save for later int((Script.objects.all().count() * (Script.objects.all().count()-1)/2) - Comparison.objects.all().count())
    set = Set.objects.get(pk=1)
    #do all the comparisons determined
    for x in range(comparisons_to_do):
        compslist, scripti, scriptj, orderby, epchangeratio = script_selection()
        listcount = len(compslist)
        # now both scripti and scriptj objects are selected, time to assign wins and losses
        if scriptj is not None: #only move ahead ther is a j script
            if scripti.parameter_value > scriptj.parameter_value: #compare scripts using development mode param value
                wini = 1
                winj = 0
            else:
                wini = 0
                winj = 1
            judge = request.user
            diffs=compute_diffs()
            start = timezone.now()
            end = timezone.now()
            duration = end - start
            Comparison.objects.create(
                set=set, 
                scripti=scripti, 
                scriptj=scriptj, 
                judge=judge, 
                wini=wini, 
                winj=winj, 
                decision_end=end, 
                decision_start=start, 
                duration=duration,
                select_method=orderby,
                epchangeratio = epchangeratio
                )
            compute_scripts_and_save()
            diffs, r = compute_last_comparison_after_calcs()        
    diffs = compute_diffs()
    script_table = Script.objects.all().order_by('-lo_of_win_in_set')
    form = AutoComparisonForm()
    cht = get_scriptchart()
    cht2 = get_resultschart()

    return render(request, 'pairwise/script_list.html', {
        'listcount': listcount,
        'compslist': compslist,
        'scripti': scripti,
        'scriptj': scriptj,
        'form': form,
        'script_table': script_table, 
        'set': set,
        'diffs': diffs,
        'chart_list': [cht, cht2],
        'orderby': orderby,
        } 
        )



class ComparisonListView(generic.ListView):
    model = Comparison

def update(request):
    r=compute_scripts_and_save()
    return render(request, 'pairwise/update.html', {'r': r})

def script_chart_view(request):
    cht2 = get_resultschart()
    cht = get_scriptchart()
    return render(request, 'pairwise/script_chart.html', {'chart_list': [cht, cht2]})

#def results_chart_view(request):
    #cht = get_resultschart()
    #return render(request, 'pairwise/results.html', {'resultschart': cht})



