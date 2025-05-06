from django.urls import path, include
from . import views
from .views import serve_geojson, serve_bus,busroute, location_geojson
from rest_framework.routers import DefaultRouter
router = DefaultRouter()
router.register(r'collisions', views.CollisionViewSet, basename='collision')
urlpatterns = [
    path('', views.map, name='map'),
    path('map/', views.map, name='map'),
    path('api/filter-options/', views.get_filter_options, name='filter_options'),
    path('trip/', views.trip, name='trip'),
    path('api/serve_geojson/', serve_geojson, name='serve_geojson'),
    path('api/location_geojson/', location_geojson, name='serve_geojson'),
    path('api/serve_bus/', serve_bus, name='serve_bus'),
    path('api/busroute/', busroute, name='busroute'),
    path('api/stored_collisions/', views.get_stored_collisions_view, name='api_get_collisions'),
    path('api/', include(router.urls)),
    

]