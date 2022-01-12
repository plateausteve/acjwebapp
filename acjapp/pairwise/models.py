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

from io import open_code
from os import renames
from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.db.models.aggregates import StdDev
from django.db.models.fields import FloatField
from django.utils import timezone
from django import forms
from numpy import log, sqrt
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
    pdf_link_option = models.URLField(blank=True, null=True, verbose_name="optional url source of a publicly available pdf hosted online")
    idcode = models.PositiveIntegerField(editable = True, default = 1000, blank=False, null=False, verbose_name="person ID code")
    
    def idcode_f(self):
        f = self.idcode
        return '%06d' % (f)

    def __str__(self):
        return str(self.pk)

class ScriptSnapshot(models.Model):
    judge = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="the judge whose comparisions generated this script snapshot")
    set = models.ForeignKey(Set, on_delete=models.CASCADE, blank=True, null=True, verbose_name="the one set to which this script snapshot belongs")
    script = models.ForeignKey(Script, on_delete=models.CASCADE, related_name="+", verbose_name="the script of this snapshot")
    comps = models.FloatField(editable = False, blank=True, null=True, verbose_name="comparisons in this snapshot")
    wins = models.FloatField(editable = False, blank=True, null=True, verbose_name="wins in this snapshot")

    def __str__(self):
        return str(self.pk)

    def logodds(self):
        odds = self.wins/(self.comps - self.wins) + .01
        logodds = round(log(odds), 3)
        return logodds

    def probability(self):
        probability = round((self.wins/self.comps), 3)
        return probability

    def rmse(self):
        mean = self.wins/self.comps 
        diffs = mean * (1 - mean)/self.comps
        rmse = round(sqrt(self.wins * diffs / self.comps), 3)
        return rmse 

    def stdev(self):
        mean = self.wins/self.comps 
        stdev = round(sqrt(((((1 - mean) ** 2) * self.wins) + (((0 - mean) ** 2) * (self.comps - self.wins))) / self.comps), 3)
        return stdev 
    
    def fisher_info(self):
        fisher_info = round(self.comps * (self.wins/self.comps) * (1 - (self.wins/self.comps)) + .01, 2)
        return fisher_info
    
    def se(self):
        fisher_info = round(self.comps * (self.wins/self.comps) * (1 - (self.wins/self.comps)) + .01, 2)
        se = round(1 / sqrt(fisher_info), 3)
        return se

    def ep(self):
        odds = self.wins/(self.comps - self.wins) + .01
        logodds = round(log(odds), 3)
        ep = round(100 + (logodds * 7),1)
        return ep
    

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

    def duration_HHmm(self):
        seconds = self.duration.total_seconds()
        return '%02d:%02d:%02d' % (int((seconds/3600)%3600), int((seconds/60)%60), int((seconds)))

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
""" 
class ScriptSnapshotForm(forms.ModelForm):
    class Meta:
        model = ScriptSnapshot
        fields = 
        widgets = {
            
        } """