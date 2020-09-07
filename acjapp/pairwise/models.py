from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from django import forms
from numpy import log 
import numpy as np 
import datetime

class Set(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="the user who uploaded the scripts of this set")
    #assessors = models.ManyToManyField(User, related_name=???, verbose_name="the users with comparing capabilities", blank=True)
    name = models.CharField(max_length=100)
    published_date = models.DateTimeField(blank=True, null=True)
    cor_est_to_actual = models.FloatField(default=0)
    greater_statement = models.TextField(default="more", verbose_name="the question posed for assessors about the items")

    def publish(self):
        self.published_date = timezone.now()
        self.save()
    
    def __str__(self):
        return self.name

class Script(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="the user who uploaded the script")
    set = models.ForeignKey(Set, on_delete=models.CASCADE, blank=True, null=True, verbose_name="the one set to which the script belongs")
    pdf = models.FileField(upload_to="scripts/pdfs", null=True, blank=True) #how do you deal with PDFs? Not working now.
    image = models.FileField(upload_to="scripts/images", null=True, blank=True)
    parameter_value = models.PositiveSmallIntegerField(verbose_name="the hidden parameter value to be compared in development")
    wins_in_set = models.PositiveSmallIntegerField(editable = False, default=0, verbose_name="count of all comparisons in which this script wins")
    comps_in_set = models.PositiveSmallIntegerField(editable = False, default=0, verbose_name="count of all comparisons with this script")
    prob_of_win_in_set = models.FloatField(editable = False, default=0, verbose_name="ratio of wins to comparisons for this script")
    lo_of_win_in_set = models.FloatField(editable = False, default=0, verbose_name="&phi; log odds of winning for this script")
    lo95ci = models.FloatField(editable = False, default=0, verbose_name="@phi; log odds low 95% confidence interval")
    hi95ci = models.FloatField(editable = False, default=0, verbose_name="@phi; log odds high 95% confidence interval")
    estimated_parameter_in_set = models.FloatField(editable = False, default=0, verbose_name="MLE of parameter from comparisons of this script")
    fisher_info = models.FloatField(editable = False, default=0, verbose_name="Fisher information for MLE of parameter based on comparison data")
    se = models.FloatField(editable = False, default=0, verbose_name="standard error of parameter for this script")
    stdev = models.FloatField(editable = False, default=0, verbose_name="standard deviation of comps sample for this script")
    rmse_in_set = models.FloatField(editable = False, default=0, verbose_name="RMSE of parameter for this script")
    count_same_p = models.IntegerField(editable = False, blank=True, null=True)

    def __str__(self):
        return str(self.pk)

class ScriptForm(forms.ModelForm):
    class Meta:
        model = Script
        fields = [
            'user', 'set', 'pdf', 'parameter_value']
        widgets = {
            'user': forms.HiddenInput(),
        }



class Comparison(models.Model):
    set = models.ForeignKey(Set, on_delete=models.CASCADE, verbose_name="the set to which this comparison belongs")
    judge = models.ForeignKey(settings.AUTH_USER_MODEL, editable = False, on_delete=models.CASCADE, verbose_name="the user judging the pair")
    scripti = models.ForeignKey(Script, on_delete=models.CASCADE, related_name="+", verbose_name="the left script in the comparison")
    scriptj = models.ForeignKey(Script, on_delete=models.CASCADE, related_name="+", verbose_name="the right script in the comparison")
    class Win(models.IntegerChoices):
        Lesser = 0
        Greater = 1
    wini = models.PositiveSmallIntegerField(choices=Win.choices, verbose_name="is left lesser or greater?")
    winj = models.PositiveSmallIntegerField(blank=True, null=True, verbose_name="is right lesser or greater?")
    resulting_set_corr = models.FloatField(default=0, editable = False, verbose_name="computing the resulting correlation of set est param to actual")
    class Interruption(models.IntegerChoices):
        Uninterrupted = 1
        Interrupted = 0
    uninterrupted = models.IntegerField(choices=Interruption.choices, editable = False, default=1, blank=False, verbose_name="is the comparison interrupted or uninterrupted allowing valid duration computation")
    class Interest(models.IntegerChoices):
        Not_at_all_interesting = 1
        Not_interesting = 2
        Neutral = 3
        Interesting = 4
        Very_interesting = 5
    interest_rating = models.IntegerField(choices=Interest.choices, editable = False, default=3, blank=False, verbose_name="how interesting is this comparison")
    class Difficulty(models.IntegerChoices):
        Not_at_all_difficult = 0
        Not_too_difficult = 1
        Difficult = 2
        Very_difficult = 3
    difficulty_rating = models.IntegerField(choices=Difficulty.choices, editable = False, default=0, blank=False, verbose_name="how difficult is the comparison to judge?")
    form_start_variable = models.FloatField(blank=True, null=True)
    decision_start = models.DateTimeField(editable = False, blank=True, null=True)
    decision_end = models.DateTimeField(editable = False, blank=True, null=True)
    duration = models.DurationField(editable = False, blank=True, null=True)

    def __str__(self):
        return str(self.pk)

class ComparisonForm(forms.ModelForm):
    class Meta:
        model = Comparison
        fields = ['wini','scripti','scriptj', 'form_start_variable'] # 'uninterrupted', 'interest_rating', 'difficulty_rating', 
        widgets = {
            'scripti': forms.HiddenInput(), 
            'scriptj': forms.HiddenInput(),
            'form_start_variable': forms.HiddenInput(),
        }

class AutoComparisonForm(forms.ModelForm):
    class Meta:
        model = Comparison
        fields = ['scripti','scriptj']
        widgets = {
            'scripti': forms.HiddenInput(), 
            'scriptj': forms.HiddenInput(),

        }

class WinForm(forms.ModelForm):
        class Meta:
            model = Comparison
            fields = ['wini','scripti','scriptj', 'form_start_variable']
            widgets = {
                'wini':forms.HiddenInput(),
                'scripti': forms.HiddenInput(), 
                'scriptj': forms.HiddenInput(),
                'form_start_variable': forms.HiddenInput(),
            }
