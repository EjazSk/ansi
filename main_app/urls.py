from django.urls import path

from .views import home, servers

urlpatterns = [path('', home, name='home'),
              path('servers/', servers, name='servers'),]
