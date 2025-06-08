from django.urls import path
from . import views

urlpatterns = [
    path('', views.job_search_view, name='job_search'),
    path('statistics/', views.statistics_view, name='statistics'),
]