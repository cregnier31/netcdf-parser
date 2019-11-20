from django.urls import path

from . import views

app_name = 'data_parser'
urlpatterns = [
    path('extract', views.ExtractorApiView.as_view(), name='extract'),
]