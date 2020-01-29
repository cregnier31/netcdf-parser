from django.db import models
from datetime import datetime
from django.contrib.postgres.fields import JSONField

class Area(models.Model):
    name = models.CharField(max_length=50)
    fullname = models.CharField(max_length=50)

    def __str__(self):
        return self.fullname

class Universe(models.Model):
    name = models.CharField(max_length=50)
    areas = models.ManyToManyField(Area, related_name='universes')

    def __str__(self):
        return self.name

class Variable(models.Model):
    name = models.CharField(max_length=50)
    universe = models.ForeignKey(Universe, related_name='variables', on_delete=models.CASCADE)

    def __str__(self):
        return self.name

class Dataset(models.Model):
    name = models.CharField(max_length=50)
    variable = models.ForeignKey(Variable, related_name='datasets', on_delete=models.CASCADE)

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=256)
    catalogue_url = models.CharField(max_length=512)
    documentation_url = models.CharField(max_length=512, null=True)
    comment = models.TextField(null=True)
    area = models.ForeignKey(Area, related_name='products', on_delete=models.CASCADE)
    datasets = models.ManyToManyField(Dataset, related_name='products')

    def __str__(self):
        return self.name


class Subarea(models.Model):
    name = models.CharField(max_length=50)
    product = models.ForeignKey(Product, related_name='subareas', on_delete=models.CASCADE)

    def __str__(self):
        return self.name

class Depth(models.Model):
    name = models.CharField(max_length=50)
    subareas = models.ManyToManyField(Subarea, related_name='depths')

    def __str__(self):
        return self.name

class Stat(models.Model):
    name = models.CharField(max_length=50)
    depths = models.ManyToManyField(Depth, related_name='stats')

    def __str__(self):
        return self.name

class PlotType(models.Model):
    name = models.CharField(max_length=50)
    stats = models.ManyToManyField(Stat, related_name='plot_types')

    def __str__(self):
        return self.name

#### Result ###################################################################
class Plot(models.Model):
    filename = models.CharField(max_length=256)
    area = models.ForeignKey(Area, on_delete=models.CASCADE)
    subarea = models.ForeignKey(Subarea, on_delete=models.CASCADE)
    universe = models.ForeignKey(Universe, on_delete=models.CASCADE)
    variable = models.ForeignKey(Variable, on_delete=models.CASCADE)
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    depth = models.ForeignKey(Depth, on_delete=models.CASCADE)
    stat = models.ForeignKey(Stat, on_delete=models.CASCADE)
    plot_type = models.ForeignKey(PlotType, on_delete=models.CASCADE)

    def __str__(self):
        return self.filename

#### Kpi Insitu ###############################################################

class KpiInsitu(models.Model):
    what = models.CharField(max_length=32)
    variable = models.ForeignKey(Variable, on_delete=models.CASCADE)
    area = models.ForeignKey(Area, on_delete=models.CASCADE)
    product = models.CharField(max_length=256)
    content = JSONField()
    start = models.DateTimeField(default=datetime.now, blank=True)
    end = models.DateTimeField(default=datetime.now, blank=True)
    month = models.IntegerField(null=True)
    year = models.IntegerField(null=True)

    def __str__(self):
        return self.product + '_' + self.what + '_' + self.variable.name

#### Kpi Sat ##################################################################

class KpiSat(models.Model):
    sat = models.CharField(max_length=32)
    area = models.ForeignKey(Area, on_delete=models.CASCADE)
    content = JSONField()
    start = models.DateTimeField(default=datetime.now, blank=True)
    end = models.DateTimeField(default=datetime.now, blank=True)
    month = models.IntegerField(null=True)
    year = models.IntegerField(null=True)

    def __str__(self):
        return self.area.name + '_' + self.sat + '_' + str(self.month) + '_' + str(self.year)

#### Kpi Score ################################################################

class KpiScore(models.Model):
    month = models.IntegerField(null=True)
    year = models.IntegerField(null=True)
    area = models.ForeignKey(Area, on_delete=models.CASCADE)
    variable = models.ForeignKey(Variable, on_delete=models.CASCADE)
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    MSD_FCST12 = models.DecimalField(null=True, max_digits=30, decimal_places=20)
    MSD_HDCT = models.DecimalField(null=True, max_digits=30, decimal_places=20)
    MS_OBS = models.DecimalField(null=True, max_digits=30, decimal_places=20)
    MEAN_OBS = models.DecimalField(null=True, max_digits=30, decimal_places=20)
    NB_OBS = models.IntegerField(null=True) 
    MSD_CLIM = models.DecimalField(null=True, max_digits=30, decimal_places=20)

    def __str__(self):
        return self.area.name + '_' + str(self.month) + '_' + str(self.year)