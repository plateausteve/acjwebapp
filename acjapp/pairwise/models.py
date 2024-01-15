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



class Student(models.Model):
    idcode = models.PositiveBigIntegerField(
        editable=True, 
        default=100000, 
        blank=False, 
        null=False, 
        verbose_name="student ID code"
    ) 
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        blank=True, 
        null=True, 
        verbose_name="user who uploaded the student information"
    )
    first_name = models.CharField(
        max_length=80, 
        editable=True,
        verbose_name="first name(s)"
    )
    last_name = models.CharField(
        max_length=80,
        editable=True,
        verbose_name="last name(s)"
    )
    birth_date = models.DateField(
        default=datetime.date(
            datetime.date.today().year-10, 
            datetime.date.today().month, 
            datetime.date.today().day
            ),
        editable=True,
        verbose_name="student date of birth"
    )
    gender_choices = [
        ("F","female"),
        ("M","male"),
        ("N","nonbinary")
    ]
    gender = models.CharField(
        max_length=1, 
        choices=gender_choices,
        editable=True,
        verbose_name="student gender"
    )
    race_choices = [
        ("A","Asian"),
        ("B","Black or African American"),
        ("H","Hispanic or Latino of any race"),
        ("N","American Indian or Alaska Native"),
        ("P","Native Hawaiian or other Pacific Islander"),
        ("W","White"),
        ("M","Two or more races"),
        ("X","Decline to state"),
    ]
    race = models.CharField(
        max_length=1, 
        editable=True,
        choices=race_choices, 
        verbose_name="student race/ethnicity"
    )
    ed = models.CharField(
        choices=[
            ("N","Not economically disadvantaged"),
            ("Y","Economically disadvantaged")
            ],
        max_length=1,
        editable=True,
        verbose_name="student economic disadvantage"
    )
    el = models.CharField(
        choices=[
            ("N","Not currently and English learner"),
            ("Y","Currently an English learner")
            ],
        max_length=1,
        editable=True,
        verbose_name="student English learner status"
    )

    def idcode_f(self):
        f = self.idcode
        return '%06d' % (f)
    
    def __str__(self):
        return str(self.idcode)

class Test(models.Model):
    name = models.CharField(max_length=200, verbose_name="name of the test")

    greater_statement = models.CharField(
        default="Greater", 
        max_length=50, 
        verbose_name="comparative terms posed as question for judges about the items"
    )

    description = models.TextField(
        max_length=400,
        verbose_name="description of this test"
    )

    administration = models.TextField(
        max_length=400,
        verbose_name="parameters for administration"
    )

    def __str__(self):
        return str(self.name)
    
class Set(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        verbose_name="the user who uploaded the scripts of this set"
    )
    judges = models.ManyToManyField(
        settings.AUTH_USER_MODEL, 
        related_name='judges', 
        verbose_name="the users with comparing capabilities for this set", 
        blank=True
    )
    
    test = models.ForeignKey(
        Test,
        on_delete=models.SET_NULL,
        blank=True, 
        null=True, 
        verbose_name="test administered to students in this set"
    )
    
    override_end = models.PositiveSmallIntegerField(
        editable = True, 
        blank = True, 
        null = True, 
        verbose_name = "end after so many comparisons override"
    )
    class Meta:
        managed = True

    def __str__(self):
        return str(self.pk)

class Script(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        blank=True, 
        null=True, 
        verbose_name="user who uploaded the script"
    )
    sets = models.ManyToManyField(
        Set,
        related_name="sets",
        blank=True, 
        editable=True,
        verbose_name="set(s) to which the script belongs"
    )
    pdf = models.FileField(
        upload_to="scripts/pdfs", 
        null=True, 
        blank=True
    )
    idcode = models.PositiveIntegerField(
        editable = True, 
        default = 10000, 
        blank=False, 
        null=False, 
        verbose_name="script ID code"
    )
    student = models.ForeignKey(
        Student, 
        on_delete=models.SET_NULL,
        blank=True, 
        null=True, 
        verbose_name="student to which the script belongs"
    )
    grade_choices = [
        (0, "Kindergarten"),
        (1, "First"),
        (2, "Second"),
        (3, "Third"),
        (4, "Fourth"),
        (5, "Fifth"),
        (6, "Sixth"),
        (7, "Seventh"),
        (8, "Eighth"),
        (9, "Ninth"),
        (10, "Tenth"),
        (11, "Eleventh"),
        (12, "Twelfth")
    ]
    grade = models.IntegerField(
        choices=grade_choices, 
        default=4, 
        verbose_name="student grade in school at time of test"
    )
    age = models.FloatField(
        blank=True,
        null=True,
        verbose_name="age of student at time of test"
    ) 
    date = models.DateField(
        blank=True,
        null=True,
        verbose_name="date the student took the test (YYYY-MM-DD)"
    )
    
    def idcode_f(self):
        f = self.idcode
        return '%06d' % (f)

    def __str__(self):
        return str(self.pk)

    class Meta:
        managed = True

class Comparison(models.Model):
    set = models.ForeignKey(
        Set, 
        on_delete=models.CASCADE, 
        verbose_name="the set to which this comparison belongs"
    )
    judge = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        verbose_name="the user judging the pair"
    )
    scripti = models.ForeignKey(
        Script, 
        on_delete=models.CASCADE, 
        related_name="+", 
        verbose_name="the left script in the comparison"
        )
    scriptj = models.ForeignKey(
        Script, 
        on_delete=models.CASCADE, 
        related_name="+", 
        verbose_name="the right script in the comparison"
    )
    wini = models.PositiveSmallIntegerField(
        blank=True, 
        null=True, 
        verbose_name="is left lesser or greater?"
    )
    form_start_variable = models.FloatField(
        blank=True, 
        null=True
    )
    decision_start = models.DateTimeField(
        editable = False, 
        blank=True, 
        null=True
    )
    decision_end = models.DateTimeField(
        editable = False, 
        blank=True, 
        null=True
    )
    duration = models.DurationField(blank=True, null=True)

    def duration_HHmm(self):
        seconds = round(self.duration.total_seconds(),0)
        return datetime.timedelta(seconds=seconds)

    def __str__(self):
        return str(self.pk)

