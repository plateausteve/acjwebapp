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
from .models import Script, Comparison, Set, WinForm
from random import sample
from django.views import generic
from .utils import compute_scripts_and_save, script_selection, get_scriptchart, get_resultschart, get_allowed_sets
import operator
from operator import itemgetter
import numpy as np

def index(request):
    if request.user.is_authenticated:
        userid=request.user.id
        allowed_sets_ids = get_allowed_sets(userid)
        request.session['sets']= allowed_sets_ids
    return render(request, 'pairwise/index.html', {})

def script_detail(request, pk):
    script=get_object_or_404(Script, pk=pk)
    return render(request, 'pairwise/script_detail.html', {'script': script})

def script_list(request, set):
    if Set.objects.filter(pk=set).exclude(owner=request.user).count()==0:
        html="<p>Set does not exist</p>"
        return HttpResponse(html)
    script_table = Script.objects.filter(set=set).order_by('-lo_of_win_in_set')
    cht = get_scriptchart()
    cht2 = get_resultschart()
    
    return render(request, 'pairwise/script_list.html', {
        'script_table': script_table, 
        'set': set,
        'chart_list': [cht, cht2],
        } 
    )

def SetView(request, pk):
    set_scripts = Script.objects.filter(set=str(pk)).order_by('-lo_of_win_in_set')
    return render(request, 'pairwise/set.html', {
        'pk': pk, 
        'set_scripts': set_scripts
        }
    )

def compare(request, set):
    userid=request.user.id
    allowed_sets_ids = get_allowed_sets(userid)
    request.session['sets']= allowed_sets_ids
    sets = request.session['sets']
    print(request.session['sets'])
    print(type(set))
    if int(set) not in allowed_sets_ids:    
        html="<p>Set not available.</p>"
        return HttpResponse(html)
    if request.method == 'POST': #if arriving here after submitting comparison form or script form
        winform = WinForm(request.POST)
        if winform.is_valid():
            comparison = winform.save(commit=False)
            comparison.judge = request.user
            comparison.scripti = Script.objects.get(pk=request.POST.get('scripti'))
            comparison.scriptj = Script.objects.get(pk=request.POST.get('scriptj'))
            comparison.set = Set.objects.get(pk=set)
            start = comparison.form_start_variable # still a float from form
            starttime = datetime.fromtimestamp(start) #convert back to datetime
            end = datetime.now() #use datetime instead of timezone because of conversion from timestamp
            comparison.decision_end = end
            comparison.decision_start = starttime
            duration = end - starttime
            comparison.duration = duration
            #winj value opposite of wini
            if comparison.wini==1:
                comparison.winj=0 
            else:
                comparison.winj=1
            comparison.save()
            compute_scripts_and_save(set)

    compslist, scripti, scriptj, j_list = script_selection(set)
    compscount = len(compslist) #save this for later so it ends after a large portion of possible comparisons are made.
    now = datetime.now() # must use datetime not timezone in order to keep it the same through to other side of form 
    starttime = now.timestamp
    set_object = Set.objects.get(pk=int(set))
    if len(j_list) > 0: 
        winform = WinForm()
        return render(request, 'pairwise/compare.html', {
                'scripti': scripti,
                'scriptj': scriptj,
                'winform': winform,
                'set': set,
                'starttime': starttime,
                'j_list': j_list,
                'allowed_sets_ids': allowed_sets_ids,
                'compscount': compscount,
                'set_object': set_object,
                } 
            )
    else: # when no more comparisons are available, stop and send to Script List page
        script_table = Script.objects.all().order_by('-lo_of_win_in_set')
        cht = get_scriptchart()
        cht2 = get_resultschart()
        return render(request, 'pairwise/script_list.html', { # TODO: this shouldn't be happening. can we call it differently?
            'script_table': script_table, 
            'set': set,
            'chart_list': [cht, cht2],
            } 
        )
       

def comparisons(request, set):
    comparisons = Comparison.objects.filter(set=set)
    return render(request, 'pairwise/comparison_list.html', {
        'set': set,
        'comparisons': comparisons,
    })

def update(request):
    compute_scripts_and_save(set)
    return render(request, 'pairwise/update.html')

def script_chart_view(request):
    cht2 = get_resultschart()
    cht = get_scriptchart()
    return render(request, 'pairwise/script_chart.html', {'chart_list': [cht, cht2]})