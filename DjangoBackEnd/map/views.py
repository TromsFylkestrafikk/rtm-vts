from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader

def map(request):
    template = loader.get_template('map.html')
    return HttpResponse(template.render())