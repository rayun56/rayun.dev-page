from django.urls import path

from . import views

app_name = 'main'
urlpatterns = [
    path('', views.index, name='index'),
    path('projects/', views.projects, name='projects'),
    path('crudtober/', views.crudtober, name='crudtober'),
    path('reserved/', views.reserved, name='reserved')
]
