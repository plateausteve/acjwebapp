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

# stats methods reference: http://personal.psu.edu/abs12/
# Aleksandra B. Slavković | Professor of Statistics
# Department of Statistics, Penn State University, University Park, PA 16802

from .models import Script, Comparison, Set, Student
from django.contrib.auth.models import User
import numpy as np
from numpy import log, sqrt, std
import random
import itertools
from operator import itemgetter
import pandas as pd
import csv
from scipy.stats import spearmanr, percentileofscore
import umap
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score, silhouette_samples

class ComputedScript:
    def __init__(self, id, idcode, idcode_f, comps, wins, logit, probability, stdev, fisher_info, se, ep, lo95ci, hi95ci, samep, rank, randomsorter, percentile):
            self.id = id
            self.idcode = idcode
            self.idcode_f = idcode_f
            self.comps = int(comps)
            self.wins = wins
            self.logit = logit
            self.probability = probability
            self.stdev = stdev
            self.fisher_info = fisher_info
            self.se = se
            self.ep = ep
            self.lo95ci = lo95ci
            self.hi95ci = hi95ci
            self.samep = samep
            self.rank = rank
            self.randomsorter = randomsorter
            self.percentile = percentile

def get_allowed_sets(userid):
    sets = Set.objects.filter(judges__id__exact=userid).order_by('pk')
    allowed_sets_ids = []
    for set in sets:
        allowed_sets_ids.append(set.id)
    return allowed_sets_ids

def script_selection(set, userid):
    scriptcount = Script.objects.filter(set=set).count()
    set_object = Set.objects.get(pk=set) # sometimes we need to use object not just the string of the set ID number
    compslist = build_compslist(set, userid)
    judges = [userid] #judges must be a list, even if it only has one judge in it
    computed_scripts_for_user_in_set = get_computed_scripts(set, judges)
    maxcomps=(scriptcount * (scriptcount-1)/2)
    switch=min(scriptcount + (scriptcount * (scriptcount-1)/6), maxcomps)
    if len(compslist) < switch: #prioritize minimum comps until comps = min of n+max/3 or max, then . . .
        computed_scripts_for_user_in_set.sort(key = lambda x: (x.comps, x.samep, x.fisher_info, x.randomsorter))
    else: #prioritize lowest same probability (less distinct estimate < -1, samep = -1 indicates unique estimate)
        computed_scripts_for_user_in_set.sort(key = lambda x: (x.samep, x.comps, x.fisher_info, x.randomsorter))
        if computed_scripts_for_user_in_set[0].samep == -1 and set_object.override_end == None:
            return compslist, None, None, [] # everything is empty

    # Go through all comparable scripts, and choose the first as scripti.
    # Then calculate the difference in probability 'p_diff' between scripti and every other script
    
    #create list of all probabilities in the set to calc standard deviation
    set_probabilities = [] 
    for script in computed_scripts_for_user_in_set:
        set_probabilities.append(float(script.probability))
    arr = np.array(set_probabilities)
    set_p_std = np.std(arr)
    
    #create a list of all possible script j's and order them for selection
    j_list = []
    for i, script in enumerate(computed_scripts_for_user_in_set):
        if i == 0:
            if script.comps == scriptcount-1:
                return compslist, None, None, [] # everything is empty
            scripti = Script.objects.get(pk = script.id)
            p_i = float(script.probability)
        elif [scripti.id, script.id] not in compslist and [script.id, scripti.id] not in compslist: # don't consider this for scriptj if it's already been compared
            p_j = float(script.probability)
            p_diff = round(abs(p_i - p_j - set_p_std), 3) # subtract 1 SD in probability to improve match.
            j_list.append([script.id, p_diff, script.comps, script.samep, script.fisher_info, script.randomsorter])
    
    # Based on lowest probability difference from 1 stdev away, then random index, choose the most similar script to display as scriptj
    if j_list:
        j_list.sort(key=itemgetter(1,5)) # 1 is p_diff, 5 is randomsorter
        scriptj = Script.objects.get(pk = j_list[0][0]) # the item that has the smallest log odds difference (lodiff)
    else: # if there are no possibilities, we can't choose a scriptj at all. whatever recieves the request will have to deal with a NoneType
        j_list = []
        scriptj = None
    return compslist, scripti, scriptj, j_list

def get_computed_scripts(set, judges):
    eps_of_set = []
    computed_scripts_for_user_in_set =[]
    scripts = Script.objects.filter(set=set)
    for script in scripts:
        comps, wins = compute_comps_wins(script, judges)
        logit, probability, stdev, fisher_info, se, ep, hi95ci, lo95ci, randomsorter = compute_more(comps, wins)
        computed_scripts_for_user_in_set.append(
            ComputedScript(
                script.id,
                script.idcode,
                script.idcode_f,
                comps,
                wins,
                logit,
                '{:.3f}'.format(probability),
                '{:.2f}'.format(stdev),
                round(fisher_info,2),
                se,
                ep,
                lo95ci,
                hi95ci,
                0, # samep is set separately
                0, # rank is set separately
                randomsorter,
                0, # percentile is set separately
                )
        )
    computed_scripts_for_user_in_set = set_ranks(computed_scripts_for_user_in_set)
    return computed_scripts_for_user_in_set

def build_compslist(set, userid):
    comps = Comparison.objects.filter(set=set).filter(judge=userid)
    compslist = []
    for comp in comps:
        i = comp.scripti.id
        j = comp.scriptj.id
        compslist.append([i, j])
    return compslist

def compute_comps_wins(script, judges):
    comps = .001 # prevents divide-by-zero error in calculating probability
    wins = 0
    for judge in judges:
        #count all the comparisons each script has been involved in for user
        comparisons_as_i_for_judge_count = Comparison.objects.filter(scripti=script, judge__pk=judge).count()
        comparisons_as_j_for_judge_count = Comparison.objects.filter(scriptj=script, judge__pk=judge).count()
        thisjudgecomps = comparisons_as_i_for_judge_count + comparisons_as_j_for_judge_count

        #count all the comparisons this script has won
        wins_as_i_for_judge_count = Comparison.objects.filter(wini=1, scripti=script, judge__pk=judge).count()
        wins_as_j_for_judge_count = Comparison.objects.filter(wini=0, scriptj=script, judge__pk=judge).count()
        thisjudgewins = wins_as_i_for_judge_count + wins_as_j_for_judge_count

        comps += thisjudgecomps
        wins += thisjudgewins
    return comps, wins

def compute_more(comps, wins):
    #compute probability of winning for each script based on comparisons so far
    probability = wins/(comps) # comps comes in with a .001 so no error dividing by 0
    # probability = (wins + .5)/(comps + 1) # see https://personal.psu.edu/abs12/stat504/Lecture/lec3_4up.pdf slide 23
    # compute the standard deviation of sample of comparisons for this script
    stdev = sqrt(((((1 - probability) ** 2) * wins) + (((0 - probability) ** 2) * (int(comps) - wins))) / (comps + .001))
    #compute other attributes only if not all wins or all losses so far
    if (round(probability, 3) == 1) or (probability <= 0):
        logit = None
        fisher_info = 0
        se = None
        ep = None
        hi95ci = None
        lo95ci = None
    else:
        se = round(stdev/sqrt(comps),3)
        # standard error of p scale measures variability of the sample mean about the true mean
        # see https://personal.psu.edu/abs12/stat504/Lecture/lec3_4up.pdf slide 13
        logit = round(log(probability/(1 - probability)), 3) # also called the MLE of phi φ
        fisher_info = comps * probability * ( 1 - probability) # slide 33 the fisher information for phi
        # see http://personal.psu.edu/abs12//stat504/online/01b_loglike/10_loglike_alternat.htm
        # "an asymptotic confidence interval constructed on the φ scale will be more accurate in coverage than an interval constructed on the p scale"
        # note: the CI for logit is fine for this, we don't need to transform it back to p as in this article
        ci = 1.96 * sqrt(1/fisher_info) # 95% CI of at the MLE of phi--see slide 30
        logithi95 = logit + ci
        logitlo95 = logit - ci
        #b = 10 # determine the spread of parameter values
        #a = int(100 - (3.18 * b )) # aim for max parameter of 100 for logit=3.18 / p = .96)
        ep = round((logit + 5) * 10, 1) # scores will range from 4 to 96 generally
        hi95ci = round((logithi95 + 5) * 10, 1)
        lo95ci = round((logitlo95 + 5) * 10, 1)

    randomsorter = random.randint(0,1000)
    return logit, probability, stdev, fisher_info, se, ep, hi95ci, lo95ci, randomsorter
    # more here: http://personal.psu.edu/abs12//stat504/online/01b_loglike/01b_loglike_print.htm

def set_ranks(computed_scripts_for_user_in_set):
    #now decrease (for sorting later) samep by one for every script including self with matching probability and set a rank value fo each
    script_ranks = []
    computed_scripts_for_user_in_set.sort(key = lambda x: x.probability, reverse=True)
    rank = 0
    for script in computed_scripts_for_user_in_set:
        for match in computed_scripts_for_user_in_set:
            if match.probability == script.probability:
                match.samep -= 1
        if script.samep == -1: #if there's only one at that value, then increase rank increment 1 for next
            rank += 1
        script.rank = rank
        script_ranks.append(len(computed_scripts_for_user_in_set)-rank)
    # calculate percentile in this set using the list of ranks in set
    for script in computed_scripts_for_user_in_set:
        r = len(script_ranks)-script.rank
        perc = percentileofscore(script_ranks, float(r), kind='mean')
        script.percentile = '{:.2f}'.format(perc)
    return computed_scripts_for_user_in_set

def make_groups(setid, judgelist):
    setobject = Set.objects.get(pk=setid)
    preselected_judges = len(judgelist)
    if judgelist == []: #judgelist input is only used to get combined stats for a set of preselected judges
        try: # if comps exist for this set, query a list of unique judge ids who have made comparisons on this set
            judgelist = Comparison.objects.filter(set=setobject).values_list('judge_id', flat=True).distinct()
        except:
            judgelist = None
    if len(judgelist) == 1:
        bestgroup = []
        bestagreement = 0
        corrstats_df = None
        groupplotdata = pd.DataFrame({"cluster":[],"x":[],"y":[],"silhouette":[]})
        return bestgroup, bestagreement, corrstats_df, [], groupplotdata
    
    #empty dictionary to contain the judges' rankings
    set_judge_script_rank = {}

    #if there are more than one judge for this set, get computed scripts for each.
    for judge in judgelist:
        computed_scripts = get_computed_scripts(setobject, [judge])
        computed_scripts.sort(key = lambda x: x.id)
        set_judge_script_rank[judge]=[]
        for script in computed_scripts:
            set_judge_script_rank[judge].append(script.rank)
    
    #when only two, easy peasy
    if len(judgelist) == 2:
        judge1 = judgelist[0]
        judge2 = judgelist[1]
        coef, p = spearmanr(set_judge_script_rank[judge1],set_judge_script_rank[judge2]) 
        bestgroup = judgelist
        bestagreement = coef
        corrstats_df = pd.DataFrame(set_judge_script_rank)
        groupplotdata = pd.DataFrame({"cluster":[],"x":[],"y":[],"silhouette":[]})
        return bestgroup, bestagreement, corrstats_df, [], groupplotdata
    
    #when 3 or more, use combinations to find the correlations of all pairs 
    #and average correlations of all combinations of 3
    else:
        judgepairs = itertools.combinations(judgelist, 2)
        judgepaircorr = {}
        corr_chart_data=[]
        for judgepair in judgepairs:
            judge1 = judgepair[0]
            judge2 = judgepair[1]
            coef, p = spearmanr(set_judge_script_rank[judge1], set_judge_script_rank[judge2])
            judgepaircorr[judgepair]=[coef, p]
            if coef >= .6:
                corr_chart_data.append([str(judge1), str(judge2), round(coef,3)])
        corr_df = pd.DataFrame(corr_chart_data, columns = ["judge1", "judge2", "rho"]) # this is just used with preselected judges
        print(corr_df)

        judgegroups = itertools.combinations(judgelist, 3)
        corrdata = []
        for judgegroup in judgegroups:
            judge1=judgegroup[0]
            judge2=judgegroup[1]
            judge3=judgegroup[2]
            rho1 = judgepaircorr[(judge1,judge2)][0] #combine these 2 lines as so: rho1, p1 = 
            p1 = judgepaircorr[(judge1,judge2)][1]
            rho2 = judgepaircorr[(judge1,judge3)][0]
            p2 = judgepaircorr[(judge1,judge3)][1]
            rho3 = judgepaircorr[(judge2,judge3)][0]
            p3 = judgepaircorr[(judge2,judge3)][1]
            rho_list = [rho1, rho2, rho3]
            rho_average = np.mean(rho_list)
            data = [
                (judge1,judge2,judge3),
                rho_average,
                (judge1,judge2),
                rho1,
                p1,
                (judge1,judge3),
                rho2,
                p2,
                (judge2,judge3),
                rho3,
                p3,
            ]
            corrdata.append(data)


        # when more than three judges,
        # also do the makegroups using UMAP dimension reduction and K-means clustering
        if len(judgelist) == 3:
            groupplotdata = pd.DataFrame({"cluster":[],"x":[],"y":[],"silhouette":[]}) # empty dataframe column labels
        else:
            # first, set up dataframe with judges as rows and probabilities of each item in columns 
            df = pd.DataFrame(set_judge_script_rank).transpose()
        
            #reduce dimensions to 2 with UMAP
            reducer = umap.UMAP(
                n_neighbors=len(judgelist)-1,
                min_dist=0.0,
                n_components=2,
                random_state=42
            ).fit_transform(df)
            
            #now to select the number of clusters with the greatest silhouette average
            #iterate through clusters from 2 to n-1, sort by silhouette average, select that as best grouping
            models=[]
            for i in range(2, len(reducer)):
                kmeans = KMeans(
                    init="random",
                    n_clusters=i,
                    n_init=10,
                    max_iter=300,
                    random_state=42
                ).fit(reducer)
                silhouette_avg = silhouette_score(reducer, kmeans.labels_)
                models.append([i, kmeans, silhouette_avg])

            #sort the models best to worst 
            sorted_models = sorted(models, key=itemgetter(2), reverse=True)

            #assign kmeans object to the first(best) model in the sorted list
            kmeans=sorted_models[0][1]
            #get the silhouette score of each judge in this grouping
            silhouette = silhouette_samples(reducer, kmeans.labels_)

            #output x & y & group for each judge in a group
            arr = []
            for i, group in enumerate(kmeans.labels_):
                arr.append([group, reducer[i][0], reducer[i][1], silhouette[i]])
            labeledarray = np.array(arr)
            groupplotdata = pd.DataFrame(
                labeledarray, 
                index=df.index.values.tolist(), 
                columns = ["cluster","x","y","silhouette"]
                ).sort_values(by=['cluster','silhouette'], ascending=False)

    df = pd.DataFrame(corrdata, columns = ['Judge Group', 'Rho Average','Pair 1 Judges', 'Pair 1 Rho','Pair 1 P-value', 'Pair 2 Judges', 'Pair 2 Rho', 'Pair 2 P-value', 'Pair 3 Judges', 'Pair 3 Rho', 'Pair 3 P-value'])
    df_sorted = df.sort_values(by='Rho Average', ascending=False)
    corrstats_df = df_sorted.set_index('Judge Group')
    if preselected_judges == 0:
        b = corrstats_df.iat[0, 0]
    else:
        b = corr_df["rho"].mean()
    bestagreement = round(b,3)
    bestgroup = pd.DataFrame.first_valid_index(corrstats_df)

    return bestgroup, bestagreement, corrstats_df, corr_chart_data, groupplotdata 
    #add a list of 2D arrays for scatterplot of each group?

# used from the django manage.py python shell
def bulkcreatescripts(filepath, user_id, set_id):
    # in python shell define the variable as this example
    # bulkcreatescripts("data/set4.csv",24,4)
    file = open(filepath, "r", encoding='utf-8-sig')
    csv_reader = csv.reader(file)
    for row in csv_reader:
        id=int(row[0])
        script = Script(set_id=set_id, idcode=id, user_id=user_id)
        script.save()
        print("Created script instance for for idcode ", id, "in set ", set_id, " for user ", user_id)
    return

# used from the django manage.py python shell
# usage example: a, b = judgereport(30)
def judgereport(judgeid):
    sets = get_allowed_sets(judgeid)
    report = []
    for set in sets:
        n = Comparison.objects.filter(judge__pk = judgeid, set = set).count()
        scriptcount = Script.objects.filter(set=set).count()
        setobject = Set.objects.get(pk=set)
        if setobject.override_end == None:
            maxcomps = int(scriptcount * (scriptcount-1) * .333)
        else:
            maxcomps = setobject.override_end
        report.append([set, n, maxcomps])
    df = pd.DataFrame(report, columns = ["Set","Done So Far","End"])
    htmltable = df.to_html(index=False)
    return df, htmltable

# used from the django manage.py python shell
# usage example: a,b,c,d,e = groupstats(4, [1,27,26],[36,35,38])
def groupstats(set, judgelist1, judgelist2):
    computed_scripts = get_computed_scripts(set, judgelist1)
    rankorder1_df = pd.DataFrame([script.__dict__ for script in computed_scripts ]) # convert list of objects into a dataframe
    rankorder1_df.drop(['idcode_f', 'fisher_info', 'samep', 'randomsorter', 'percentile','comps','wins','stdev','probability','se','ep','lo95ci','hi95ci'], axis = 1, inplace=True) # drop unneeded columns
    idorder1_df = rankorder1_df.sort_values("id")
    if judgelist2 == []:
        rankorder2_df = "None"
        idorder2_df = "None"
        rankcorr_df = "None"
    else:
        computed_scripts = get_computed_scripts(set, judgelist2)
        rankorder2_df = pd.DataFrame([script.__dict__ for script in computed_scripts ])
        rankorder2_df.drop(['idcode_f', 'fisher_info', 'samep', 'randomsorter', 'percentile','comps','wins','stdev','probability','se','ep','lo95ci','hi95ci'], axis = 1, inplace=True) # drop unneeded columns
        idorder2_df = rankorder2_df.sort_values("id")
        rankcorr_df = idorder1_df.corrwith(idorder2_df, axis = 0, method = "spearman")
    return rankorder1_df, idorder1_df, rankorder2_df, idorder2_df, rankcorr_df


def bulkassignscripts(filepath):
    # in python shell send variable as in this example:
    # bulkcreatescripts("analysis/scriptsetassignments.csv")
    file = open(filepath, "r", encoding='utf-8-sig')
    csv_reader = csv.reader(file)
    for row in csv_reader:
        scriptobjectcount = Script.objects.filter(idcode=int(row[1])).count()
        if scriptobjectcount == 1:
            continue
        try:
            scriptobjects = Script.objects.filter(idcode=int(row[1]))
        except:
            continue
        for scriptobject in scriptobjects:
            print(row)
            setid=int(row[0])
            setobject = Set.objects.get(pk=setid)
            userobject = User.objects.get(pk=setobject.owner_id)
            try: 
                student=Student.objects.get(idcode=row[1])
                student.idcode=int(row[1])
                student.birth_date=row[2]
                student.first_name="N/A"
                student.last_name="N/A"
                student.user=userobject
                student.gender=row[5]
                student.race=row[3]
                student.ed=row[6]
                student.el=row[7]
                student.save()
            except:
                student=Student(
                    idcode=int(row[1]),
                    birth_date=row[2],
                    first_name="N/A",
                    last_name="N/A",
                    user=userobject,
                    gender=row[5],
                    race=row[3],
                    ed=row[6],
                    el=row[7])
                student.save()
            scriptobject.sets.add(setobject)
            scriptobject.age=float(row[9])
            scriptobject.date=row[8]
            scriptobject.student = student
            scriptobject.save()
    return