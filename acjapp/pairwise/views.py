from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.http import HttpResponseRedirect, HttpResponse
from .models import Script, Comparison, ComparisonForm, Set, AutoComparisonForm
from random import sample
from django.views import generic
from .utils import compute_scripts_and_save, script_selection

def index(request):
    return render(request, 'pairwise/index.html', {})

def compared(request):
    return render(request, 'pairwise/compared.html', {})

def script_list(request):
    script_table = Script.objects.all().order_by('-lo_of_win_in_set')
    set = Set.objects.get(pk=1)
    if request.method == 'POST':
        form = AutoComparisonForm(request.POST)
        if form.is_valid():
            comparison = form.save(commit=False)
            comparison.judge = request.user
            comparison.scripti = Script.objects.get(pk=request.POST.get('scripti'))
            comparison.scriptj = Script.objects.get(pk=request.POST.get('scriptj'))
            comparison.set = Set.objects.get(pk=1)#for now there is only one set object
            comparison.resulting_set_corr = comparison.set.cor_est_to_actual
            #set winj value to the opposite of wini
            if comparison.scripti.parameter_value > comparison.scriptj.parameter_value:
                comparison.winj=0 
                comparison.wini=1
            else:
                comparison.winj=1
                comparison.wini=0
            comparison.save()
            compute_scripts_and_save()#after the comparison above, update all scripts' computed fields with computations based on latest comparison
        return redirect('/script_list')

    else: #if the form is being generated for the first time send the template what it needs, i.e. which two scripts to compare
        j, scripti, scriptj = script_selection() 
        form = AutoComparisonForm()
        return render(request, 'pairwise/script_list.html', {
                'j': j,
                'scripti': scripti,
                'scriptj': scriptj,
                'form': form,
                'script_table': script_table, 
                'set': set,
                } 
                )

def compare(request):
    if request.method == 'POST':
        form = ComparisonForm(request.POST)
        if form.is_valid():
            comparison = form.save(commit=False)
            comparison.judge = request.user
            comparison.scripti = Script.objects.get(pk=request.POST.get('scripti'))
            comparison.scriptj = Script.objects.get(pk=request.POST.get('scriptj'))
            comparison.set = Set.objects.get(pk=1)#for now there is only one set object
            comparison.resulting_set_corr = comparison.set.cor_est_to_actual
            
            #set winj value to the opposite of wini
            if comparison.wini==1:
                comparison.winj=0 
            else:
                comparison.winj=1
            comparison.save()
            #after the comparison above, update all scripts' computed fields with computations based on latest comparison
            compute_scripts_and_save()
        return redirect('/compare')

    
    else: #if the form is being generated for the first time send the template what it needs, i.e. which two scripts to compare
        j, scripti, scriptj = script_selection() 
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
    compcount = Comparison.objects.all().count()
    scriptcount = 20 * Script.objects.all().count() #when to switch selection algorithms
    #do all the comparisons needed
    for i in range(comparisons_to_do):
        scripti, ordered_scripts = ordered_scripts_by_comps(compcount, scriptcount)
        if compcount > scriptcount:
            j=sorted(ordered_scripts, key=operator.itemgetter(1)) #sort the list of lists from least LO difference to greatest
        else:
            j=ordered_scripts
        #j is an array of all ordered scripts. Do we really need all 30? Why not just do the first two instead of looping through all? Interesting for debug info.
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
        compute_scripts_and_save()
        compcount -= 1
    return redirect('/comparisons')



class ComparisonListView(generic.ListView):
    model = Comparison


def update(request):
    compute_scripts_and_save()
    return render(request, 'pairwise/update.html', {})

