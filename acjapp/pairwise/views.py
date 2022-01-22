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
from .utils import ComputedScript, get_computed_scripts, script_selection, get_scriptchart, get_resultschart, get_allowed_sets, corr_matrix, make_groups, set_ranks, compute_comps_wins, compute_more
import operator
from operator import itemgetter
import numpy as np
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm

def index(request):
    if request.user.is_authenticated:
        userid=request.user.id
        allowed_sets_ids = get_allowed_sets(userid)
        request.session['sets'] = allowed_sets_ids
    return render(request, 'pairwise/index.html', {})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            if 'next' in request.POST:
                return redirect(request.POST.get('next'))
            else:
                return redirect('index.html')
    else:
        form = AuthenticationForm()
    return render(request,'pairwise/login.html', {'form': form })

def logout_view(request):
    if request.method == 'POST':
        logout(request)
        return redirect('index.html')

@login_required(login_url="login")
def script_detail(request, pk):
    script=get_object_or_404(Script, pk=pk)
    return render(request, 'pairwise/script_detail.html', {'script': script})

@login_required(login_url="login")
def script_list(request, set):
    k, p = corr_matrix(set) #get kendall's Tau and Pearson's standard correlation
    print(k)
    print(p)
    try:
        judges = make_groups(k)[0] # List index out of range error here when s doesn't create a group
    except:
        judges = [request.user.id]
        print("exception")
    computed_scripts = get_computed_scripts(set, judges)
    #cht = get_scriptchart(computed_scripts)
    #cht2 = get_resultschart(computed_scripts)
    return render(request, 'pairwise/script_list.html', {
        'script_table': computed_scripts, 
        'set': set,
        'judges': judges,
        'k': k.to_html(),
        'p': p.to_html()
        #'chart_list': [cht, cht2],
        } 
    )

@login_required(login_url="login")
def set_view(request, pk):
    judges = []
    judges.append(request.user.id)
    allowed_sets_ids = get_allowed_sets(request.user.id)
    request.session['sets']= allowed_sets_ids
    computed_scripts = get_computed_scripts(pk, judges)
    computed_scripts.sort(key = lambda x: x.probability, reverse=True)
    return render(request, 'pairwise/set.html', {
        'pk': pk, 
        'set_scripts': computed_scripts
        }
    )

@login_required(login_url="login")
def comparisons(request, set):
    userid=request.user.id
    allowed_sets_ids = get_allowed_sets(userid)
    request.session['sets']= allowed_sets_ids
    if int(set) not in allowed_sets_ids:    
        html="<p>ERROR: Set not available.</p>"
        return HttpResponse(html)
    comparisons = Comparison.objects.filter(set=set, judge=userid)
    return render(request, 'pairwise/comparison_list.html', {
        'set': set,
        'comparisons': comparisons,
        }
    )
       

@login_required(login_url="login")
def compare(request, set):
    userid=request.user.id
    allowed_sets_ids = get_allowed_sets(userid)
    request.session['sets']= allowed_sets_ids
    message = ""
    if int(set) not in allowed_sets_ids:    
        html="<p>ERROR: Set not available.</p>"
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
            
            # make sure page refresh doesn't duplicate a comparison
            try:
                last_comp_by_user = Comparison.objects.filter(judge=request.user).latest('pk')

            except:
                last_comp_by_user = None #note: this may not be necessary if query automatically gives us none
                comparison.save()
            if last_comp_by_user:
                if (comparison.scripti == last_comp_by_user.scripti) and (comparison.scriptj == last_comp_by_user.scriptj) and (comparison.judge == last_comp_by_user.judge):        
                    message = "No comparison saved."
                else:
                    comparison.save()      
                    message = "Comparison saved."
  
    #whether POST or GET, set all these variables afresh and render comparision form template        
    compslist, scripti, scriptj, j_list = script_selection(set, userid)
    compscount = len(compslist)
    now = datetime.now()
    starttime = now.timestamp
    set_object = Set.objects.get(pk=set)
    winform = WinForm()
    if len(j_list)==0:
        scripti=None
        scriptj=None
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
            'message': message
            } 
        )