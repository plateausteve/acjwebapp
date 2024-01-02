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
from datetime import datetime
from django.http import HttpResponse
from .models import Script, Comparison, Set, WinForm, Student
from .utils import * 
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
import mpld3
from mpld3 import plugins
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('svg')
import ast

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
def script(request, pk):
    script=get_object_or_404(Script, pk=pk)
    return render(request, 'pairwise/script.html', {'script': script})

@login_required(login_url="login")
def groupresults(request, setjudges):
    if "-" in list(setjudges): #enter preselected judgelist after set number in url with dashes between.
        setjudges = setjudges.split("-")
        set = str(setjudges[0])
        judgelist =[]
        for judge in setjudges[1:]:
            judgelist.append(int(judge))
        j, a, corrstats_df, corr_chart_data, groupplotdata = make_groups(set, judgelist) 
        j = judgelist #override j returned from make_groups to include all judges assigned in request url

    else: 
        set = setjudges
        judgelist = [] # the make_groups function can take preselected judges when desired
        j, a, corrstats_df, corr_chart_data, groupplotdata = make_groups(set, judgelist)
    if len(j) < 2:
        judges = [request.user.id]
        a = 1
        corrstats = None
    else:
        judges = j
        corrstats = corrstats_df.to_html()
    
    clusterchart = chartmaker(groupplotdata)
    computed_scripts = get_computed_scripts(set, judges)

    #build lists to send to Highchart charts for error bar chart -- re-sort for low to high scores
    lohi_computed_scripts = sorted(computed_scripts, key = lambda x: x.probability)
    scriptids=[]
    fisher=[]
    scores=[]
    scoreerrors=[]
    for script in lohi_computed_scripts:
        if script.ep == None:
            pass
        else: 
            scriptids.append(script.idcode)
            fisher.append(script.fisher_info)
            scores.append(script.ep)
            scoreerrors.append([script.lo95ci, script.hi95ci])
    return render(request, 'pairwise/groupresults.html', {
        'script_table': computed_scripts, 
        'set': set,
        'judges': judges,
        'a': a,
        'corrstats': corrstats,
        'corr_chart_data': corr_chart_data,
        'scriptids': scriptids,
        'fisher': fisher,
        'scores': scores,
        'scoreerrors': scoreerrors,
        'groupplotdata': groupplotdata,
        'clusterchart': clusterchart
        } 
    )

@login_required(login_url="login")
def myresults(request, pk):
    judges = []
    judges.append(request.user.id)
    allowed_sets_ids = get_allowed_sets(request.user.id)
    request.session['sets'] = allowed_sets_ids
    computed_scripts = get_computed_scripts(pk, judges)
    computed_scripts.sort(key = lambda x: x.probability, reverse=True)
    return render(request, 'pairwise/myresults.html', {
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
    return render(request, 'pairwise/comparisons.html', {
        'set': set,
        'comparisons': comparisons,
        }
    )
       
@login_required(login_url="login")
def compare(request, set):
    userid=request.user.id
    allowed_sets_ids = get_allowed_sets(userid)
    request.session['sets']= allowed_sets_ids
    message = "" # empty message will be ignored in template
    if int(set) not in allowed_sets_ids:    
        html = "<p>ERROR: Set not available.</p>"
        return HttpResponse(html) 
    if request.method == 'POST': #if arriving here after submitting a form
        winform = WinForm(request.POST)
        if winform.is_valid():
            comparison = winform.save(commit=False)
            comparison.judge = request.user
            comparison.scripti = Script.objects.get(pk=request.POST.get('scripti'))
            comparison.scriptj = Script.objects.get(pk=request.POST.get('scriptj'))
            comparison.set = Set.objects.get(pk=set)
            start = comparison.form_start_variable # still a float from form
            starttime = datetime.fromtimestamp(start) # convert back to datetime
            end = datetime.now() # use datetime instead of timezone
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
    script_count = Script.objects.filter(set=set).count()
    compsmax = int(script_count * (script_count - 1) * .5)
    now = datetime.now()
    starttime = now.timestamp
    set_object = Set.objects.get(pk=set)
    if set_object.override_end == None: # check if a comparisons limit override has been defined for the set
        compstarget = int(round((.66 * compsmax),-1))
    else:
        compstarget = set_object.override_end
    winform = WinForm()
    if len(j_list) == 0 or compscount >= compstarget:
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
            'compsmax': compsmax,
            'compstarget': compstarget,
            'set_object': set_object,
            'message': message
            } 
        )

def chartmaker(groupplotdata):
    fig, ax = plt.subplots()
    fig.set_size_inches(6,6)
    points = ax.scatter(groupplotdata['x'], groupplotdata['y'], c=groupplotdata['cluster'], cmap='tab10')
    labels=[]
    n = len(groupplotdata['cluster'])
    c = list(groupplotdata['cluster'])
    s = list(groupplotdata['silhouette'])
    index = groupplotdata.index.values.tolist()
    for i  in range(0, n):
        labels.append(["Group: " + str(int(c[i])) + "; Judge: "+ str(index[i])+"; Silhouette: " + str(round(s[i],3))])
    
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title('UMAP Projection of Judge Groups')

    tooltip = plugins.PointHTMLTooltip(
        points, 
        labels, 
        voffset=10, 
        hoffset=10 
    )

    plugins.connect(fig, tooltip)

    clusterchart=mpld3.fig_to_html(fig=fig)
    return clusterchart

@login_required(login_url="login")
def myaccount(request):
    accountid = request.user.id
    allowed_sets_ids = get_allowed_sets(request.user.id)
    request.session['sets'] = allowed_sets_ids
    return render(request, 'pairwise/account.html', {
        'accountid': accountid, 
        'allowed_sets_ids': allowed_sets_ids
        }
    )