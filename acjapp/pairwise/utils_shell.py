from models import Script, Set, Student
from utils import get_computed_scripts
from django.contrib.auth.models import User
import pandas as pd
import csv

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
