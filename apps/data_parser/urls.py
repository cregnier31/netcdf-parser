from django.urls import path

from . import views

app_name = 'data_parser'
urlpatterns = [
    path('extract', views.ExtractorApiView.as_view(), name='extract'),
    path('exploit', views.ExploitDataApiView.as_view(), name='exploit'),
]