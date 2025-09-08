from django.conf import settings
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponseBadRequest
from .models import Device, DeviceData, EmailSetting, Recipient, Notification
from .forms import SearchDevice, RegisterDevice, AddEmailRecipientForm, UpdateSMTPForm, DataHistory
from django.utils import timezone
from datetime import timedelta
from django.db.models import Avg
import json, ipcalc
from TempLog import scheduler
import pandas

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
            query_results = Device.objects.exclude(Name='All').order_by('Name')
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

def update_device(request, id):
    if request.user.is_authenticated != True:
        return redirect ('/login/?next=/device/')
    sensor = Device.objects.get(id=id)
    if request.method == 'GET':
        form = RegisterDevice (instance = sensor)
        return render (request, 'device.html',{'update': form, 'user_auth':True})
    elif request.method == 'POST':
        form = RegisterDevice (request.POST, instance = sensor)
        if form.is_valid():
            form.save()
            return render (request, 'device.html',{'device': sensor, 'user_auth': True})
    return render (request, 'device.html',{'error': 'Device update failed!', 'user_auth': True})


def delete_device(request, id):
    if request.user.is_authenticated != True:
        return redirect ('/login/?next=/device/')
    if request.method == 'POST' and id != 0:
        try:
            device = Device.objects.get(id=id)
            if device.Name == 'All':
                return render (request, 'device.html',{'error': 'invalid sensor ID. Failed to delete!', 'user_auth': True})
            device.delete()
        except Exception as e:
            return render (request, 'device.html',{'error': 'Exception occurred: '+ str(e), 'user_auth': True})
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
    try: # confirm if Device Name and API Key are matching with DB
        Sensor = Device.objects.get(Name=Name, Api_Key=Api_Key, Is_Active=True)
    except Exception as e: # invalid sensor ignore its data
        return JsonResponse({"error": "Unauthorized"}, status=401)
    try: # if the API call is the first call both Temp and Humi should be 0 otherwise it's trying to update data to the server
        Data = json.loads(request.body)
        Temp = Data.get("temperature")
        Humi = Data.get('humidity') if 'humidity' in Data else Data.get('humility')
        if Temp == 0 and Humi == 0: #both values are 0 indicated the Sensor is trying to setup itself 
            return JsonResponse({'status': 'ok', 
                'sensor-type': Sensor.Device_Type, 
                'T_Low': Sensor.T_Comfort_Low, 
                'T_High': Sensor.T_Comfort_High, 
                'H_Low': Sensor.H_Comfort_Low, 
                'H_High': Sensor.H_Comfort_High,
            }) #return the device type to sensor
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
            current_temp = DeviceData.objects.filter(Sensor__Name = sensor.Name, Created_At__gte=five_minutes_ago).aggregate(avg_temp=Avg('Temp'))['avg_temp']
            current_humi = DeviceData.objects.filter(Sensor__Name = sensor.Name, Created_At__gte=five_minutes_ago).aggregate(avg_humi=Avg('Humi'))['avg_humi']
            if current_temp !=None and current_humi != None:
                sensor_data.append([sensor.Name, f"{float(current_temp):.1f}", f"{float(current_humi):.1f}"])
            elif current_temp !=None and current_humi == None:
                sensor_data.append([sensor.Name, f"{float(current_temp):.1f}", '0'])
            elif current_temp ==None and current_humi != None:
                sensor_data.append([sensor.Name, '0', f"{float(current_humi):.1f}"])
            else:
                sensor_data.append([sensor.Name, '0', '0'])
    return render (request, 'temperature.html',{'data': sensor_data, 'time':timezone.localtime(timezone.now())})

def list_recipient(request, pk = 0):
    if request.user.is_authenticated != True:
        return redirect ('/login/?next=/view_recipients')
    if Recipient.objects.all().count() == 0:
        return render (request, 'recipient.html',{'new': True, 'user_auth': True})
    if request.method == 'GET' and pk == 0:
        query_results = Recipient.objects.all().order_by('Email')
        return render (request, 'recipient.html',{'Recipients': query_results, 'user_auth': True})
    elif request.method == 'GET' and pk != 0:
        return render (request,'recipient.html', {'Recipient': Recipient.objects.get(id=pk), 'user_auth': True})

def add_recipient(request):
    if request.user.is_authenticated != True:
        return redirect ('/login/?next=/view_recipients')
    if request.method == 'POST':
        form = AddEmailRecipientForm(request.POST)
        if form.is_valid():
            form.save()
        return redirect ('/view_recipients',{'user_auth': True})
    else:
        form = AddEmailRecipientForm()
        return render(request, 'recipient.html',{'AddNew': form,'user_auth': True})
        
def remove_recipient(request, pk):
    if request.user.is_authenticated != True:
        return redirect ('/login/?next=/view_recipients')
    if request.method == 'POST':
        if pk != 0:
            try:
                recipient = Recipient.objects.get(id=pk)
                recipient.delete()
            except Exception as e:
                return render (request, 'recipient.html',{'error': 'Exception occurred: '+ e, 'user_auth': True})
        return redirect ('/view_recipients',{'user_auth': True})

def smtp_setting (request, pk=0):
    if request.user.is_authenticated != True:
        return redirect ('/login/?next=/smtp_setting')
    if request.method == 'GET' and pk == 0:
        return render (request, 'smtp_setting.html',{'Setting': EmailSetting.objects.get(id=1), 'user_auth': True})
    elif request.method == 'GET' and pk != 0:
        smtp_setting = EmailSetting.objects.get(id=1)
        update = UpdateSMTPForm(request.POST or None, instance = smtp_setting)
        return render (request, 'smtp_setting.html',{'update': update, 'user_auth': True})
    elif request.method == 'POST':
        smtp_setting = EmailSetting.objects.get(id=1)
        update  = UpdateSMTPForm(request.POST, instance = smtp_setting)
        if update.is_valid():
            update.save()
            new_setting = EmailSetting.objects.get(id=1)
            settings.EMAIL_HOST = new_setting.EMAIL_HOST
            settings.EMAIL_USE_TLS = new_setting.EMAIL_USE_TLS
            settings.EMAIL_PORT = new_setting.EMAIL_PORT
            settings.EMAIL_HOST_USER = new_setting.EMAIL_HOST_USER
            if new_setting.EMAIL_HOST_PASSWORD is not None:
                settings.EMAIL_HOST_PASSWORD = new_setting.EMAIL_HOST_PASSWORD
            return redirect ('/smtp_setting',{'user_auth': True})
    return render (request, 'smtp_setting.html',{'error': [('Update SMTP setting failed!')], 'user_auth': True})

def system_on_off(request,action = 'None'):
    if request.user.is_authenticated != True:
        return redirect ('/login/?next=/system')
    if action =='None' and scheduler.has_jobs():
        return render (request,'system_on_off.html', {'status_on': True, 'user_auth': True})
    elif action =='None' and not scheduler.has_jobs():
        return render (request,'system_on_off.html', {'status_on': False, 'user_auth': True})
    elif action == 'reset':
        scheduler.remove_old_jobs()
        if not scheduler.has_jobs():
            return render (request,'system_on_off.html', {'status_on': False, 'user_auth': True})
        else:
            return render (request,'system_on_off.html', {'error': [("Job is still running. Please go back and retry!")], 'user_auth': True})
    elif action == 'start':
        if not scheduler.has_jobs():
            scheduler.run()
            if scheduler.has_jobs():
                return render (request,'system_on_off.html', {'status_on': True, 'user_auth': True})
            else:
                return render (request,'system_on_off.html', {'error': [("Falsed to start. Please go back and retry!")], 'user_auth': True})

def history (request):
    if request.user.is_authenticated != True:
        return redirect ('/login/?next=/history')
    if request.method == 'GET' and 'sensor' in request.GET:
        Sensor_Name = request.GET.get('sensor')
        Range = request.GET.get('range')

        history_range = None # obtain all records
        if 'today' in Range:
            now = timezone.localtime(timezone.now())
            history_range = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif '2 days' in Range:
            history_range = timezone.now() - timedelta(days=2)
        elif '3 days' in Range:
            history_range = timezone.now() - timedelta(days=3)
        elif '4 days' in Range:
            history_range = timezone.now() - timedelta(days=4)
        elif '5 days' in Range:
            history_range = timezone.now() - timedelta(days=5)
        elif '6 days' in Range:
            history_range = timezone.now() - timedelta(days=6)
        elif '1 Week' in Range: # obtain the last 7 days records
            history_range = timezone.now() - timedelta(days=7)
        elif '2 Weeks' in Range:
            history_range = timezone.now() - timedelta(days=14)
        elif '3 Weeks' in Range:
            history_range = timezone.now() - timedelta(days=21)
        elif '1 Month' in Range:
            history_range = timezone.now() - timedelta(days=30)
        elif '2 Months' in Range:
            history_range = timezone.now() - timedelta(days=60)
        elif '3 Months' in Range:
            history_range = timezone.now() - timedelta(days=90)
        
        if history_range:
            history_data = DeviceData.objects.filter(Sensor__Name = Sensor_Name, Created_At__gte = history_range).order_by('Created_At')
        else:
            history_data = DeviceData.objects.filter(Sensor__Name = Sensor_Name).order_by('Created_At')
        
        data_frame = pandas.DataFrame.from_records(history_data.values('Sensor__Name', 'Temp', 'Humi', 'Created_At'))
        if not data_frame.empty:
            data_frame["Created_At"] = data_frame['Created_At'].apply(lambda dt: timezone.localtime(dt))
            return JsonResponse({
                'Sensor_name': Sensor_Name,
                'Created_At': data_frame['Created_At'].dt.strftime('%Y-%m-%d %H:%M').tolist(),
                'temp': data_frame['Temp'].tolist(),
                'humi': data_frame['Humi'].tolist(),
            })
        else:
            return JsonResponse({'error': 'No data found for this selection.'}, status=404)
    return render (request, 'history.html', {'history_form': DataHistory(), 'user_auth': True})