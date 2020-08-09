from django.urls import path
from . import views



urlpatterns = [
    path('', views.index, name='index.html'),
    path('index/', views.index, name='index.html'),
    path('compare/', views.compare, name='compare.html'),
    path('compared/', views.compared, name='compared.html'),
    path('comparisons/', views.ComparisonListView.as_view(), name='comparisons'),
    path('script_list/', views.script_list, name='scripts'),
    path('update/', views.update, name='update')
]