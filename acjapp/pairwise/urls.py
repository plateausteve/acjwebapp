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

from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('index/', views.index, name='index'),
    path('compare/<set>/', views.compare, name='compare'),
    path('compare/', views.compare, name='compare'),
    path('comparisons/<set>/', views.comparisons, name='comparisons'),
    path('groupresults/<setjudges>/', views.groupresults, name='groupresults'),
    path('script/<int:pk>/', views.script, name='script'),
    path('myresults/<int:pk>/', views.myresults, name='myresults'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('account/',views.myaccount, name='account'),
    path('student/<int:id>/',views.student, name='student'),
    path('student/add/', views.add_student, name='addstudent'),
    path('student/delete/<int:id>/', views.delete_student, name='deletestudent'),
    path('script/delete/<int:id>/', views.delete_script, name='deletescript'),
    path('script/add/', views.add_script, name='addscript'),
    path('account/changepassword/', views.change_password, name='changepassword')
]