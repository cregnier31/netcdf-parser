from django.db import models

from django.db import models

class Product(models.Model):
    name = models.CharField(max_length=30)
    filename = models.CharField(max_length=256)
    
class Area(models.Model):
    name = models.CharField(max_length=30)

class Univer(models.Model):
    name = models.CharField(max_length=30)
    area = models.ForeignKey(Area, on_delete=models.CASCADE)

class Dataset(models.Model):
    # TODO: rattacher au type green/white/blue (trouver un nom pour ca)
    name = models.CharField(max_length=30)
    univer = models.ForeignKey(Univer, on_delete=models.CASCADE)

class PlotType(models.Model):
    name = models.CharField(max_length=30)
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE)

class Variable(models.Model):
    name = models.CharField(max_length=30)
    plot_type = models.ForeignKey(PlotType, on_delete=models.CASCADE)

class Stat(models.Model):
    name = models.CharField(max_length=30)
    variable = models.ForeignKey(Variable, on_delete=models.CASCADE)

class Depths(models.Model):
    name = models.CharField(max_length=30)
    stat = models.ForeignKey(Stat, on_delete=models.CASCADE)

class Subarea(models.Model):
    name = models.CharField(max_length=30)
    depths = models.ForeignKey(Depths, on_delete=models.CASCADE)