from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponseBadRequest
from .models import Device, DeviceData
from .forms import SearchDevice, RegisterDevice
from django.utils import timezone
from datetime import timedelta
from django.db.models import Avg
import json, ipcalc

def local(request): #bypass authentication if request is from local network
    localnetwork = ['10.0.0.0/8','172.16.0.0/12','192.168.0.0/16']
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR") # get original IP if running Nginx as reverse proxy
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0].strip()  
    else:
        ip = request.META.get("REMOTE_ADDR") # get IP if running Django as web server
    for subnet in localnetwork:
        if ip in ipcalc.Network(subnet):
            return True
    return False

def list_device(request,id=0):
    if request.user.is_authenticated != True:
        return redirect ('/login/?next=/device/')
    if Device.objects.all().count() == 0:
        return render (request, 'device.html',{'new': True,'user_auth': True})
    if request.method == 'POST':
        form = SearchDevice (request.POST)
        if form.is_valid():
            Name = form.cleaned_data['Name'] or ''
            Device_Type = form.cleaned_data['Device_Type']
            Is_Active = form.cleaned_data['Is_Active']
            query_results = Device.objects.all().order_by('Name')
            if Name != '':
                query_results = query_results.filter(Name = Name)
            if Device_Type != 'All':
                query_results = query_results.filter(Device_Type = Device_Type)
            if Is_Active == 'Active':
                query_results = query_results.filter(Is_Active = True)
            if Is_Active == 'Deactive':
                query_results = query_results.filter(Is_Active = False)
            if query_results.count() == 0:
                return render (request, 'device.html',{'error': 'No record found and try again!', 'user_auth': True})
            return render (request, 'device.html',{'devices': query_results,'user_auth': True})
    else:
        if id == 0:
            return render (request, 'device.html',{'search_form': SearchDevice(), 'user_auth': True})
        else:
            return render (request, 'device.html',{'device': Device.objects.get(id = id), 'user_auth': True})

def register_device(request):
    if request.user.is_authenticated != True:
        return redirect ('/login/?next=/device/')
    if request.method == 'POST':
        form = RegisterDevice(request.POST)
        if form.is_valid():
            Name = form.cleaned_data['Name']
            form.save()
            return render (request, 'device.html',{'device': Device.objects.get(Name = Name), 'user_auth': True})
        else:
            return render (request, 'device.html',{'error': 'Duplicate device name please try again!', 'user_auth': True})
    return render (request, 'device.html',{'register_device': RegisterDevice(), 'user_auth': True})

def delete_device(request, id):
    if request.user.is_authenticated != True:
        return redirect ('/login/?next=/device/')
    if request.method == 'POST' and id != 0:
        try:
            device = Device.objects.get(id=id)
            device.delete()
        except Exception as e:
            return render (request, 'device.html',{'error': 'Exception occurred: '+ e, 'user_auth': True})
        return redirect ('/device/')
    return redirect ('/device/')

def toggle_device_status(request, id):
    device = Device.objects.get(id=id)
    device.Is_Active = not device.Is_Active
    device.save()
    return redirect(request.META.get('HTTP_REFERER', '/'))

@csrf_exempt
def receive_temperature(request):
    if request.method != "POST":
        return HttpResponseBadRequest("Only POST allowed")
        return
    Name = request.headers.get("Device-Name")
    Api_Key = request.headers.get("Api-Key")

    if not Name or not Api_Key:
        return JsonResponse({"error": "Missing headers"}, status=400)
        return
    try:
        Sensor = Device.objects.get(Name=Name, Api_Key=Api_Key, Is_Active=True)
    except Exception as e:
        return JsonResponse({"error": "Unauthorized"}, status=401)
        pass
    try:
        Data = json.loads(request.body)
        Temp = Data.get("temperature")
        Humi = Data.get('humility')
        if Temp == 0 and Humi == 0: #both values are 0 indicated the Sensor is trying to setup itself 
            return JsonResponse({'status': 'ok', 'sensor-type': Sensor.Device_Type}) #return the device type to sensor
        else:
            Record = DeviceData(Sensor = Sensor, Temp = Temp, Humi = Humi)
            Record.save()
        return JsonResponse({'status': 'ok'})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)

def display_current(request):
    if request.user.is_authenticated != True:
        if not local(request):
            return redirect ('/login/?next=/display_current')
    sensor_data=[]
    if request.method == 'GET':
        five_minutes_ago = timezone.now() - timedelta(minutes=5)
        for sensor in Device.objects.filter(Is_Active = True):
            if 'Temperature' in sensor.Device_Type:
                current_temp = DeviceData.objects.filter(Sensor__Name = sensor.Name, Created_At__gte=five_minutes_ago).aggregate(avg_temp=Avg('Temp'))['avg_temp']
                if current_temp != None:
                    sensor_data.append([sensor.Name, f"{float(current_temp):.1f}", '0'])
                else:
                    sensor_data.append([sensor.Name, '0', '0'])
            elif 'Humility' in sensor.Device_Type:
                current_humi = DeviceData.objects.filter(Sensor__Name = sensor.Name, Created_At__gte=five_minutes_ago).aggregate(avg_humi=Avg('Humi'))['avg_humi']
                if current_humi != None:
                    sensor_data.append([sensor.Name, '0', f"{float(current_humi):.1f}"])
                else:
                    sensor_data.append([sensor.Name, '0', '0']) 
            elif 'Hygrometer' in sensor.Device_Type:
                current_temp = DeviceData.objects.filter(Sensor__Name = sensor.Name, Created_At__gte=five_minutes_ago).aggregate(avg_temp=Avg('Temp'))['avg_temp']
                current_humi = DeviceData.objects.filter(Sensor__Name = sensor.Name, Created_At__gte=five_minutes_ago).aggregate(avg_humi=Avg('Humi'))['avg_humi']
                if current_temp !=None and current_humi != None:
                    ensor_data.append([sensor.Name, f"{float(current_temp):.1f}", f"{float(current_humi):.1f}"])
                elif current_temp !=None and current_humi == None:
                    sensor_data.append([sensor.Name, f"{float(current_temp):.1f}", '0'])
                elif current_temp ==None and current_humi != None:
                    sensor_data.append([sensor.Name, '0', f"{float(current_humi):.1f}"])
                else:
                    sensor_data.append([sensor.Name, '0', '0'])
    return render (request, 'temperature.html',{'data': sensor_data, 'time':timezone.localtime(timezone.now())})

                