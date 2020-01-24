from django.urls import path

from . import views

app_name = 'data_parser'
urlpatterns = [
    path('extract', views.ExtractorApiView.as_view(), name='extract'),
    path('filters', views.GetFiltersApiView.as_view(), name='filters'),
    path('plot', views.FindPlotApiView.as_view(), name='plot'),
    path('kpi_insitu', views.FindKpiInsituApiView.as_view(), name='kpi_insitu'),
    path('kpi_sat', views.FindKpiSatApiView.as_view(), name='kpi_sat'),
    path('kpi_score', views.FindKpiScoreApiView.as_view(), name='kpi_score'),
    path('autocomplete', views.AutocompleteApiView.as_view(), name='autocomplete'),
    path('png', views.GetPngApiView.as_view(), name='png'),
]