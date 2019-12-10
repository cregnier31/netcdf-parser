from django.shortcuts import render, HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from apps.data_parser.services import extract_data, get_all_selectors, get_plot, autocomplete
import jsons,json

class ExtractorApiView(APIView):

    @swagger_auto_schema(
        operation_id ='data/extract',
        responses={
            200: openapi.Response(
               description='Will return a dictonnary giving you data extracted from filename.',
            ),
        },
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT, 
            properties={
                'filename': openapi.Schema(type=openapi.TYPE_STRING, example="global_global-analysis-forecast-phy-001-024_timeseries_salinity_antarctic-circumpolar_anomaly-correlation_0000-0005m.png"),
            }
        )
    )
    def post(self, request, *args, **kwargs):
        if len(request.body)<=2:
	        return HttpResponse("<p>JSON body is empty!<p>", status=400)
        else:
            payload = json.loads(request.body)
            result = extract_data(payload['filename'])
            json_to_send = jsons.dump(result)
            return Response(json_to_send)
            tet ='tet'
            return HttpResponse("Done", status=200) 

class GetFiltersApiView(APIView):

    @swagger_auto_schema(
        operation_id ='data/filters',
        responses={
            200: openapi.Response(
               description='Will return a dictonnary giving you avalaible filters and relations between them.',
            ),
        }
    )
    def post(self, request, *args, **kwargs):
        result = get_all_selectors()
        json_to_send = jsons.dump(result)
        return Response(json_to_send)

class FindPlotApiView(APIView):

    @swagger_auto_schema(
        operation_id ='data/plot',
        responses={
            200: openapi.Response(
               description='Will find plot matching criteria',
            ),
        },
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT, 
            properties={
                'area': openapi.Schema(type=openapi.TYPE_STRING, example="global"),
                'univers': openapi.Schema(type=openapi.TYPE_STRING, example="BLUE"),
                'variable': openapi.Schema(type=openapi.TYPE_STRING, example="Temperature"),
                'dataset': openapi.Schema(type=openapi.TYPE_STRING, example="temperature"),
                'product': openapi.Schema(type=openapi.TYPE_STRING, example="global-analysis-forecast-phy-001-024"),
                'depth': openapi.Schema(type=openapi.TYPE_STRING, example="2000-5000m"),
                'stat': openapi.Schema(type=openapi.TYPE_STRING, example="anomaly-correlation"),
                'plot_type': openapi.Schema(type=openapi.TYPE_STRING, example="timeseries")
            }
        )
    )
    def post(self, request, *args, **kwargs):
        if len(request.body)<=2:
	        return HttpResponse("<p>JSON body is empty!<p>", status=400)
        else:
            payload = json.loads(request.body)
            result = get_plot(payload)
            json_to_send = jsons.dump(result)
            return Response(json_to_send)

class AutocompleteApiView(APIView):
    
    @swagger_auto_schema(
        operation_id ='data/autocomplete',
        responses={
            200: openapi.Response(
               description='Autocomplete to find: product, variable and dataset',
            ),
        },
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={ 
                'slug': openapi.Schema(type=openapi.TYPE_STRING, example='001-02'),
            }
        )
    )
    def post(self, request, *args, **kwargs):
        if len(request.body)<=2:
	        return HttpResponse("<p>JSON body is empty!<p>", status=400)
        else:
            payload = json.loads(request.body)
            result = autocomplete(payload['slug'])
            json_to_send = jsons.dump(result)
            return Response(json_to_send)