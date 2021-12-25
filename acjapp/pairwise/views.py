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

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from datetime import datetime
from django.utils import timezone
from django.urls import reverse
from django.http import HttpResponseRedirect, HttpResponse
from .models import Script, ScriptForm, Comparison, ComparisonForm, Set, WinForm
from random import sample
from django.views import generic
from .utils import compute_scripts_and_save, script_selection, build_btl_array, get_scriptchart, get_resultschart
import operator
from operator import itemgetter
import numpy as np

def index(request):
    return render(request, 'pairwise/index.html', {})

def script_detail(request, pk):
    script=get_object_or_404(Script, pk=pk)
    return render(request, 'pairwise/script_detail.html', {'script': script})

def script_list(request):
    script_table = Script.objects.all().order_by('-lo_of_win_in_set')
    set = Set.objects.get(pk=3)
    cht = get_scriptchart()
    cht2 = get_resultschart()
    
    return render(request, 'pairwise/script_list.html', {
        'script_table': script_table, 
        'set': set,
        'chart_list': [cht, cht2],
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
            comparison.set = Set.objects.get(pk=3)
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
            print (comparison.judge, comparison.duration, comparison.scripti, comparison.scriptj)
            #set winj value to the opposite of wini
            if comparison.wini==1:
                comparison.winj=0 
            else:
                comparison.winj=1
        comparison.save()
        compute_scripts_and_save()

        return redirect('/compare')


    else: #if the form is being generated for the first time send the template what it needs
        compslist, scripti, scriptj, j_list = script_selection() #  j_list can be used to end comparisons when list is empty
        compscount = len(compslist)
        set = Set.objects.get(pk=3)
        now = datetime.now() # use datetime not timezone in order to keep it the same through to other side of form 
        starttime = now.timestamp
        #I think I figured out how to check that there are no more pairings for others either to prevent early abort
        # If this breaks down the line you know where to look
        if len(j_list) > 0: #as long as there are pairings available keep comparing
            form = WinForm()
            return render(request, 'pairwise/compare.html', {
                    'form': form,
                    'set': set,
                    'starttime': starttime,
                    'j_list': j_list,
                    } 
                )

        else: # when no more comparisons are available, stop and send to Script List page
            script_table = Script.objects.all().order_by('-lo_of_win_in_set')
            set = Set.objects.get(pk=3)
            cht = get_scriptchart()
            cht2 = get_resultschart()
            return render(request, 'pairwise/script_list.html', { # TODO: this shouldn't be happening. can we call it differently?
                'script_table': script_table, 
                'set': set,
                'chart_list': [cht, cht2],
                } 
            )

class ComparisonListView(generic.ListView):
    model = Comparison

def update(request):
    compute_scripts_and_save()
    return render(request, 'pairwise/update.html')

def script_chart_view(request):
    cht2 = get_resultschart()
    cht = get_scriptchart()
    return render(request, 'pairwise/script_chart.html', {'chart_list': [cht, cht2]})

#def results_chart_view(request):
    #cht = get_resultschart()
    #return render(request, 'pairwise/results.html', {'resultschart': cht})

def script_add(request): # not currently in use--front end add
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

def script_edit(request, pk): # not currently in use--front end edit
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

