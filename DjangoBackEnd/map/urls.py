from django.urls import path
from . import views
from .views import serve_geojson, serve_bus,busroute

urlpatterns = [
    path('map/', views.map, name='map'),
    path('api/filter-options/', views.get_filter_options, name='filter_options'),
    path('trip/', views.trip, name='trip'),
    path('api/serve_geojson/', serve_geojson, name='serve_geojson'),
    path('api/serve_bus/', serve_bus, name='serve_bus'),
    path('api/busroute/', busroute, name='busroute'),

]