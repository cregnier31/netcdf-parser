from django.contrib import admin
from apps.data_parser.models import Univers, Area, Variable, Product, Dataset, Subarea, Depth, PlotType, Stat, Plot, Kpi

admin.site.register(Area)
admin.site.register(Subarea)

admin.site.register(Univers)
admin.site.register(Variable)
admin.site.register(Dataset)
admin.site.register(Product)
admin.site.register(Depth)
admin.site.register(Stat)
admin.site.register(PlotType)

admin.site.register(Plot)

admin.site.register(Kpi)