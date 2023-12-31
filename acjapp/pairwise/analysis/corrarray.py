from pairwise.models import Comparison, Set
from pairwise.utils import get_computed_scripts
import itertools
import random
from scipy.stats import spearmanr

def corrpairs(setid, cormin):
    setobject = Set.objects.get(pk=setid)
    try: # if comps exist for this set, query a list of unique judge ids who have made comparisons on this set
        judgelist = Comparison.objects.filter(set=setobject).values_list('judge_id', flat=True).distinct()
    except:
        judgelist = []
    if len(judgelist) <2:
        return [], []
    
    # create a list of scripts with rankings for each judge in each set
    set_judge_script_rank = {}
    for judge in judgelist:
        computed_scripts = get_computed_scripts(setobject, [judge])
        computed_scripts.sort(key = lambda x: x.id)
        set_judge_script_rank[judge]=[]
        for script in computed_scripts:
            set_judge_script_rank[judge].append(script.rank)


    

    if len(judgelist) == 2:
        coef, p = spearmanr(set_judge_script_rank[0],set_judge_script_rank[1])
        return [], []
    else:
        judgepairs = itertools.combinations(judgelist, 2)
        judgepaircorr = {}
        corr_chart_data=[]
        for judgepair in judgepairs:
            judge1 = judgepair[0]
            judge2 = judgepair[1]
            coef, p = spearmanr(set_judge_script_rank[judge1], set_judge_script_rank[judge2])
            judgepaircorr[judgepair]=[coef, p]
            if coef >= cormin:
                corr_chart_data.append([int(judge1), int(judge2), round(coef,3)])
        judgecorrvector = {}
        for judge1 in judgelist:
            judgecorrvector[judge1] = []
            for judge2 in judgelist:
                if judge1 == judge2:
                    pass
                else:
                    coef, p = spearmanr(set_judge_script_rank[judge1], set_judge_script_rank[judge2])
                    judgecorrvector[judge1].append([int(judge2), coef, p])





    return corr_chart_data, judgecorrvector
