from django.shortcuts import render

def home(request):
    return render(request, 'home.html',{})

def servers(request):
    return render(request, 'servers.html',{})