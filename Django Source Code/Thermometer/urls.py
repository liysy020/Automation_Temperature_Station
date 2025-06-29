"""
URL configuration for Thermometer project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from Login.views import login_request as login, logout_request as logout
from TempLog.views import list_device, register_device, delete_device, toggle_device_status, receive_temperature, display_current

urlpatterns = [
    path('admin/', admin.site.urls),
    path ('', display_current, name = 'display_current'),
    path ('login/', login, name = 'login'),
    path ('logout/', logout, name = 'logout'),
    path ('device/', list_device, name = 'list_device'),
    path ('device/<int:id>', list_device, name = 'list_device_id'),
    path ('delete_device/<int:id>', delete_device, name = 'delete_device'),
    path ('device/<int:id>/toggle/', toggle_device_status, name='toggle_device_status'),
    path ('register_device/', register_device, name = 'register_device'),
    path ('api/temperature/', receive_temperature, name = 'receive_temperature'),
    path ('display_current/', display_current, name = 'display_current'),
]
