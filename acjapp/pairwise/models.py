from django.conf import settings
from django.db import models
from django.utils import timezone
from django import forms
from numpy import log 
import numpy as np 

class Set(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="the user who uploaded the scripts of this set")
    name = models.CharField(max_length=100)
    published_date = models.DateTimeField(blank=True, null=True)
    cor_est_to_actual = models.FloatField(default=0)

    def publish(self):
        self.published_date = timezone.now()
        self.save()
    
    def __str__(self):
        return self.name

class Script(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="the user who uploaded the script")
    set = models.ForeignKey(Set, on_delete=models.CASCADE, blank=True, null=True, verbose_name="the one set to which the script belongs")
    pdf = models.FileField(upload_to="scripts/pdfs", null=True, blank=True)
    image = models.FileField(upload_to="scripts/images", null=True, blank=True)
    parameter_value = models.PositiveSmallIntegerField(verbose_name="the hidden parameter value to be compared by the user in development")
    wins_in_set = models.PositiveSmallIntegerField(default=0, verbose_name="count of all comparisons in which this script wins")
    comps_in_set = models.PositiveSmallIntegerField(default=0, verbose_name="count of all comparisons with this script")
    prob_of_win_in_set = models.FloatField(default=0, verbose_name="ratio of wins to comparisons for this script")
    lo_of_win_in_set = models.FloatField(default=0, verbose_name="log odds of winning for this script")
    estimated_parameter_in_set = models.FloatField(default=0, verbose_name="estimated parameter from comparisons of this script")
    rmse_in_set = models.FloatField(default=0, verbose_name="RSME of parameter for this script")

    def __str__(self):
        return str(self.pk)

    def compute(self): #not using this single script update until I understand better how to call it, instead it's in a for loop in views.py
        compsi = Comparison.objects.filter(scripti = pk).count()
        compsj = Comparison.objects.filter(scriptj = pk).count()
        comps = winsi + winsj + .001
        winsi = Comparison.objects.filter(scripti = pk, wini=1).count()
        winsj = Comparison.objects.filter(scriptj = pk, winj=1).count()
        wins = compsi + compsj
        self.comps_in_set = comps
        self.wins_in_set = wins
        self.prob_of_win_in_set = round(wins/comps, 3)
        odds = (wins/(comps - wins))
        logodds = round(log(odds), 3)
        self.lo_of_win_in_set = logodds
        self.save()



class Comparison(models.Model):
    set = models.ForeignKey(Set, on_delete=models.CASCADE, verbose_name="the set to which this comparison belongs")
    judge = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="the user judging the pair")
    scripti = models.ForeignKey(Script, on_delete=models.CASCADE, related_name="+", verbose_name="the left script in the comparison")
    scriptj = models.ForeignKey(Script, on_delete=models.CASCADE, related_name="+", verbose_name="the right script in the comparison")
    class Win(models.IntegerChoices):
        Lesser = 0
        Greater = 1
    wini = models.PositiveSmallIntegerField(choices=Win.choices, verbose_name="is left lesser or greater?")
    winj = models.PositiveSmallIntegerField(choices=Win.choices, verbose_name="is right lesser or greater?")
    resulting_set_corr = models.FloatField(default=0, verbose_name="storing the resulting correlation of set est param to actual")

    def __str__(self):
        return str(self.pk)

class ComparisonForm(forms.ModelForm):
    class Meta:
        model = Comparison
        fields = ['wini','scripti','scriptj']
        widgets = {
            'scripti': forms.HiddenInput(), 
            'scriptj': forms.HiddenInput(),
        }


