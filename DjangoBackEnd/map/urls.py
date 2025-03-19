from django.urls import path
from . import views
from .views import location_geojson

urlpatterns = [
    path('map/', views.map, name='map'),
    path('api/locations/', location_geojson, name='location_geojson'),
    path('api/filter-options/', views.get_filter_options, name='filter_options'),
    path('trip/', views.trip, name='trip'),
]