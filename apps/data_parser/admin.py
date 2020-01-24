from django.contrib import admin
from apps.data_parser.models import Universe, Area, Variable, Product, Dataset, Subarea, Depth, PlotType, Stat, Plot, KpiInsitu

admin.site.register(Area)
admin.site.register(Subarea)

admin.site.register(Universe)
admin.site.register(Variable)
admin.site.register(Dataset)
admin.site.register(Product)
admin.site.register(Depth)
admin.site.register(Stat)
admin.site.register(PlotType)

admin.site.register(Plot)

admin.site.register(KpiInsitu)