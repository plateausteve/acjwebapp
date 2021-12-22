from django.urls import path
from . import views



urlpatterns = [
    path('', views.index, name='index.html'),
    path('index/', views.index, name='index.html'),
    path('compare/', views.compare, name='compare.html'),
    path('comparisons/', views.ComparisonListView.as_view(), name='comparisons'),
    path('script_list/', views.script_list, name='scripts'),
    path('update/', views.update, name='update'),
    path('script_chart/', views.script_chart_view, name='script_chart'),
    path('script/add', views.script_add, name='script_add'),
    path('script/<int:pk>/edit/', views.script_edit, name='script_edit'),
    path('script/<int:pk>/', views.script_detail, name='script_detail'),
]