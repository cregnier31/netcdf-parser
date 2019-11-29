from django.urls import path

from . import views

app_name = 'data_parser'
urlpatterns = [
    path('extract', views.ExtractorApiView.as_view(), name='extract'),
    path('filters', views.GetFiltersApiView.as_view(), name='filters'),
    path('plot', views.FindPlotApiView.as_view(), name='plot'),
]