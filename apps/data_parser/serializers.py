from rest_framework import serializers

from apps.data_parser.models import Area, Subarea, Universe, Variable, Dataset, Product, Depth, Stat, PlotType, Plot, Kpi


class PlotTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlotType
        fields = ['id', 'name']


class StatSerializer(serializers.ModelSerializer):
    plot_types = PlotTypeSerializer(many=True, read_only=True)
    class Meta:
        model = Stat
        fields = ['id', 'name', 'plot_types']


class DepthSerializer(serializers.ModelSerializer):
    stats = StatSerializer(many=True, read_only=True)
    class Meta:
        model = Depth
        fields = ['id', 'name', 'stats']

class FilteredListSerializer(serializers.ListSerializer):
    def to_representation(self, data):
        data = data.filter(subareas=self.context['id_subarea'])
        return super(FilteredListSerializer, self).to_representation(data)

class ProductSerializer(serializers.ModelSerializer):
    depths = DepthSerializer(many=True, read_only=True)
    class Meta:
        list_serializer_class = FilteredListSerializer
        model = Product
        fields = ['id', 'name', 'depths']


class DatasetSerializer(serializers.ModelSerializer):
    products = ProductSerializer(many=True, read_only=True)
    class Meta:
        model = Dataset
        fields = ['id', 'name', 'products']


class VariableSerializer(serializers.ModelSerializer):
    datasets = DatasetSerializer(many=True, read_only=True)
    class Meta:
        model = Variable
        fields = ['id', 'name', 'datasets']


class UniverseSerializer(serializers.ModelSerializer):
    variables = VariableSerializer(many=True, read_only=True)
    class Meta:
        model = Universe
        fields = ['id', 'name', 'variables']


class SubareaSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        self.context['id_subarea'] = instance.id
        return super().to_representation(instance)
        
    universes = UniverseSerializer(many=True, read_only=True)
    class Meta:
        model = Subarea
        fields = ['id', 'name', 'universes']


class AreaSerializer(serializers.ModelSerializer):
    subareas = SubareaSerializer(many=True, read_only=True)
    class Meta:
        model = Area
        fields = ['id', 'name', 'fullname', 'subareas']






#### Result ###################################################################
class PlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plot
        fields = ['id', 'name']

#### Kpis #####################################################################
class KpiSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlotType
        fields = ['id', 'what', 'content']