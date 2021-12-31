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
    judges = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='judges', verbose_name="the users with comparing capabilities for this set", blank=True)
    name = models.CharField(max_length=100)
    greater_statement = models.CharField(default="Greater", max_length=50, verbose_name="the comparative adjective posed as question for judges about the items")
    
    def __str__(self):
        return str(self.pk)

class Script(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="the user who uploaded the script")
    set = models.ForeignKey(Set, on_delete=models.CASCADE, blank=True, null=True, verbose_name="the one set to which the script belongs")
    pdf = models.FileField(upload_to="scripts/pdfs", null=True, blank=True)
    idcode = models.PositiveIntegerField(editable = True, default = 1000, blank=False, null=False, verbose_name="person ID code")
    wins_in_set = models.PositiveSmallIntegerField(editable = False, default=0, verbose_name="count of all comparisons in which this script wins")
    comps_in_set = models.PositiveSmallIntegerField(editable = False, default=0, verbose_name="count of all comparisons with this script")
    comps_display = models.FloatField(editable = False, default=0, verbose_name="1/10th count of all comparisons with this script")
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
    form_start_variable = models.FloatField(blank=True, null=True)
    decision_start = models.DateTimeField(editable = False, blank=True, null=True)
    decision_end = models.DateTimeField(editable = False, blank=True, null=True)
    duration = models.DurationField(editable = False, blank=True, null=True)
    
    def __str__(self):
        return str(self.pk)

class WinForm(forms.ModelForm):
    class Meta:
        model = Comparison
        fields = ['set','wini','scripti','scriptj', 'form_start_variable']
        widgets = {
            'set': forms.HiddenInput(),
            'wini': forms.HiddenInput(),
            'scripti': forms.HiddenInput(),
            'scriptj': forms.HiddenInput(),
            'form_start_variable': forms.HiddenInput(),
        }