from django import forms
from .models import Comparison, Student, Script
from django.db import models


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

class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = [
            'idcode',
            'user',
            'first_name',
            'last_name',
            'birth_date',
            'gender',
            'race',
            'ed',
            'el'
        ]
        widgets = {'user': forms.HiddenInput()}

class ScriptForm(forms.ModelForm):
    class Meta:
        model = Script
        fields = [
            'user',
            'pdf',
            'idcode',
            'student',
            'grade',
            'age',
            'date'
        ]
        widgets = {
            'user': forms.HiddenInput(),
            'student': forms.HiddenInput(),
        }



