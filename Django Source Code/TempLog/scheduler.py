from TempLog.models import EmailSetting, Recipient, Device, DeviceData, Notification
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Q
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from django.utils import timezone
from datetime import timedelta
from django.db.models import Avg

x_month_logs = 4 # Keeping 4 months records
logger = logging.getLogger('thermometer_log')

jobstores = {'default': SQLAlchemyJobStore(url='sqlite:///jobs.sqlite')}
scheduler = BackgroundScheduler(jobstores=jobstores)

def send_notification(sub, msg, receipients):
    if EmailSetting.objects.get(id=1).EMAIL_HOST == 'smtp.example.com':
        return False
    try:
        send_mail(sub, msg, settings.EMAIL_HOST_USER, receipients)
        return True
    except Exception as e:
        logger.debug('send_notification exception: '+str(e))
    return False

def alerting():
    five_minutes_ago = timezone.now() - timedelta(minutes=5)
    local_time = timezone.localtime(timezone.now())
    formatted_time = local_time.strftime('%Y-%m-%d %H:%M:%S')
    for sensor in Device.objects.filter(Is_Active = True):
        if not DeviceData.objects.filter(Sensor__Name = sensor.Name, Created_At__gte=five_minutes_ago).exists(): # no data received on the last 5 mins
            has_sent = False # assume notification has not sent
            for sent_notification in Notification.objects.filter(Sensor__Name = sensor.Name): #fletch notification database to confirm
                if 'Lost connection' in sent_notification.Message:
                    has_sent = True
                    break
            if not has_sent:
                receipients = Recipient.objects.filter(
                    Q(Sensor__Name = sensor.Name) | Q(Sensor__Name = 'All')
                    ).values_list('Email', flat=True).distinct()
                if receipients:
                    for receipient in receipients: # create records that notification will just send once per receipient
                        user = (Recipient.objects.filter(Email=receipient, Sensor=sensor).first() or Recipient.objects.filter(Email=receipient, Sensor__Name='All').first())
                        new_notification = Notification(User=user, Sensor=sensor, Message = 'Lost connection detected!')
                        new_notification.save()
                    sent = send_notification (
                        sub = 'Alert: Sensor lost connection to Internet', 
                        msg = sensor.Name + ' sensor lost connection to Internet on '+ formatted_time, 
                        receipients = receipients,
                        )
                    if sent:
                        logger.debug ('Sensor connection lost email sent succesfully!')
                    else:
                        logger.debug ('Failed to send notification about sensor lost connection!')
        else:
            for lost_connection_notification in Notification.objects.filter(Sensor__Name = sensor.Name, Message__contains='Lost connection'): # clear alerts that connection restored
                sent = send_notification (
                    sub = 'Clear: Lost connection alert', 
                    msg = 'Internet connection restored on sensor '+ sensor.Name + ' on '+ formatted_time, 
                    receipients = [lost_connection_notification.User.Email]
                    )
                if sent:
                    lost_connection_notification.delete()
                    logger.debug ('Lost-Connection-Clear email sent successfully!')
            if sensor.T_Comfort_Low != sensor.T_Comfort_High: # Temperature Comfert zone has set
                current_temp = DeviceData.objects.filter(Sensor__Name = sensor.Name, Created_At__gte=five_minutes_ago).aggregate(avg_temp=Avg('Temp'))['avg_temp']
                if current_temp < sensor.T_Comfort_Low: # Low temperature found
                    logger.debug ('Low temperature found on sensor '+ sensor.Name)
                    has_sent = False # assume notification has not sent
                    for sent_notification in Notification.objects.filter(Sensor__Name = sensor.Name): #fletch notification database to confirm
                        if 'Low temperature' in sent_notification.Message:
                            has_sent = True
                            break
                    if not has_sent:
                        receipients = Recipient.objects.filter(
                            Q(Sensor__Name = sensor.Name) | Q(Sensor__Name = 'All')
                            ).values_list('Email', flat=True).distinct()
                        if receipients:
                            for receipient in receipients: # create records that notification will just send once per receipient
                                user = (Recipient.objects.filter(Email=receipient, Sensor=sensor).first() or Recipient.objects.filter(Email=receipient, Sensor__Name='All').first())
                                new_notification = Notification(User=user, Sensor=sensor, Message = 'Low temperature detected!')
                                new_notification.save()
                            sent = send_notification (
                                sub = 'Alert: Low temperature', 
                                msg = 'Low temperature detected on sensor '+ sensor.Name + ' on '+ formatted_time + '\nCurrent temperature is ' + f"{current_temp:.1f}" +'°C', 
                                receipients = receipients,
                                )
                            if sent:
                                logger.debug ('Temperature notification email sent successfully!')
                            else:
                                logger.debug ('No Temperature notification!')
                elif current_temp > sensor.T_Comfort_High: # High temperature found
                    logger.debug ('High temperature found on sensor '+ sensor.Name)
                    has_sent = False # assume notification has not sent
                    for sent_notification in Notification.objects.filter(Sensor__Name = sensor.Name): #fletch notification database to confirm
                        if 'High temperature' in sent_notification.Message:
                            has_sent = True
                            break
                    if not has_sent:
                        receipients = Recipient.objects.filter(
                            Q(Sensor__Name = sensor.Name) | Q(Sensor__Name = 'All')
                            ).values_list('Email', flat=True).distinct()
                        if receipients:
                            for receipient in receipients: # create records that notification will just send once per receipient
                                user = (Recipient.objects.filter(Email=receipient, Sensor=sensor).first() or Recipient.objects.filter(Email=receipient, Sensor__Name='All').first())
                                new_notification = Notification(User=user, Sensor=sensor, Message = 'High temperature detected!')
                                new_notification.save()
                            sent = send_notification (
                                sub = 'Alert: High temperature', 
                                msg = 'High temperature detected on sensor '+ sensor.Name + ' on '+ formatted_time + '\nCurrent temperature is ' + f"{current_temp:.1f}" +'°C', 
                                receipients = receipients,
                                )
                            if sent:
                                logger.debug ('Temperature notification email sent successfully!')
                            else:
                                logger.debug ('No Temperature notification!')
                else: # clear alerts within comfort zone
                    for notification in Notification.objects.filter(Sensor__Name = sensor.Name):
                        if 'Low temperature' in notification.Message:
                            sent = send_notification (
                                sub = 'Clear: Low temperature alert', 
                                msg = 'Low temperature alert cleared on sensor '+ sensor.Name + ' on '+ formatted_time + '\nCurrent temperature is ' + f"{current_temp:.1f}" +'°C', 
                                receipients = [notification.User.Email]
                                )
                            if sent:
                                notification.delete()
                                logger.debug ('Temp-Alert-Clear email sent successfully!')
                        elif 'High temperature'in notification.Message:
                            sent = send_notification (
                                sub = 'Clear: High temperature alert', 
                                msg = 'High temperature alert cleared on sensor '+ sensor.Name + ' on '+ formatted_time + '\nCurrent temperature is ' + f"{current_temp:.1f}" +'°C', 
                                receipients = [notification.User.Email]
                                )
                            if sent:
                                notification.delete()
                                logger.debug ('Temp-Alert-Clear email sent successfully!')
            if sensor.H_Comfort_Low != sensor.H_Comfort_High: #Humidity comfort zone has set
                current_humi = DeviceData.objects.filter(Sensor__Name = sensor.Name, Created_At__gte=five_minutes_ago).aggregate(avg_humi=Avg('Humi'))['avg_humi']
                if current_humi < sensor.H_Comfort_Low: # Low humidity found
                    logger.debug ('Low humidity found on sensor '+ sensor.Name)
                    has_sent = False #assume notification has not sent
                    for sent_notification in Notification.objects.filter(Sensor__Name = sensor.Name): #fletch notification database to confirm
                        if 'Low humidity' in sent_notification.Message:
                            has_sent = True
                            break
                    if not has_sent:
                        receipients = Recipient.objects.filter(
                            Q(Sensor__Name = sensor.Name) | Q(Sensor__Name = 'All')
                            ).values_list('Email', flat=True).distinct()
                        if receipients:
                            for receipient in receipients: # create records that notification will just send once per receipient
                                user = (Recipient.objects.filter(Email=receipient, Sensor=sensor).first() or Recipient.objects.filter(Email=receipient, Sensor__Name='All').first())
                                new_notification = Notification(User=user, Sensor=sensor, Message = 'Low humidity detected!')
                                new_notification.save()
                            sent = send_notification (
                                sub = 'Alert: Low humidity', 
                                msg = 'Low humidity detected on sensor '+ sensor.Name + ' on '+ formatted_time + '\nCurrent humidity is ' + f"{current_humi:.1f}" +'%', 
                                receipients = receipients,
                                )
                            if sent:
                                logger.debug ('Humidity notification email sent successfully!')
                            else:
                                logger.debug ('No notification!')
                elif current_humi > sensor.H_Comfort_High: # High humidity found
                    logger.debug ('High humidity found on sensor '+ sensor.Name)
                    has_sent = False # assume notification has not sent
                    for sent_notification in Notification.objects.filter(Sensor__Name = sensor.Name): #fletch notification database to confirm
                        if 'High humidity' in sent_notification.Message:
                            has_sent = True
                            break
                    if not has_sent:
                        receipients = Recipient.objects.filter(
                            Q(Sensor__Name = sensor.Name) | Q(Sensor__Name = 'All')
                            ).values_list('Email', flat=True).distinct()
                        if receipients:
                            for receipient in receipients: # create records that notification will just send once per receipient
                                user = (Recipient.objects.filter(Email=receipient, Sensor=sensor).first() or Recipient.objects.filter(Email=receipient, Sensor__Name='All').first())
                                new_notification = Notification(User=user, Sensor=sensor, Message = 'High humidity detected!')
                                new_notification.save()
                            sent = send_notification (
                                sub = 'Alert: High humidity', 
                                msg = 'High humidity detected on sensor '+ sensor.Name + 'on '+ formatted_time + '\nCurrent humidity is ' + f"{current_humi:.1f}" +'%', 
                                receipients = receipients,
                                )
                            if sent:
                                logger.debug ('Humidity notification email sent successfully!')
                            else:
                                logger.debug ('No humidity notification!')
                else: # clear alerts within comfort zone
                    for notification in Notification.objects.filter(Sensor__Name = sensor.Name):
                        if 'Low humidity' in notification.Message:
                            sent = send_notification (
                                sub = 'Clear: Low humidity alert', 
                                msg = 'Low humidity alert cleared on sensor '+ sensor.Name + ' on '+ formatted_time + '\nCurrent humidity is ' + f"{current_temp:.1f}" +'°C', 
                                receipients = [notification.User.Email]
                                )
                            if sent:
                                notification.delete()
                                logger.debug ('Humi-Alert-Clear email sent successfully!')
                        elif 'High humidity'in notification.Message:
                            sent = send_notification (
                                sub = 'Clear: High humidity alert', 
                                msg = 'High humidity alert cleared on sensor '+ sensor.Name + ' on '+ formatted_time + '\nCurrent humidity is ' + f"{current_temp:.1f}" +'°C', 
                                receipients = [notification.User.Email]
                                )
                            if sent:
                                notification.delete()
                                logger.debug ('Humi-Alert-Clear email sent successfully!')
def delete_old_logs():
    try:
        months_ago = timezone.now() - timedelta(days=x_month_logs * 30)
        DeviceData.objects.filter(Created_At__lt=months_ago).delete()
        logger.debug ('Successfully removed records older than '+ str(months_ago))
    except Exception as e:
        logger.debug ('Delete_old_logs exception: '+str(e))

def run():
    global scheduler
    if not job_exists('Temp_Humi_Alerting'):
        scheduler.add_job(alerting, 'interval', minutes = 5, max_instances = 1, misfire_grace_time=60, id = 'Temp_Humi_Alerting', replace_existing=True)
    if not job_exists('delete_records'):
        scheduler.add_job(delete_old_logs, CronTrigger(hour = 1, minute = 0, timezone = 'Australia/Sydney'), max_instances = 1, misfire_grace_time=60, id = 'delete_records', replace_existing=True)
    if not scheduler.running:
        scheduler.start()

def remove_old_jobs():
    global scheduler
    jobs = scheduler.get_jobs()
    for job in jobs:
        scheduler.remove_job(job.id) #clean up any old running jobs before it starts

def job_exists(job_id):
    global scheduler
    job = scheduler.get_job(job_id)
    if job:
        return True
    return False

def has_jobs():
    if len(scheduler.get_jobs()) == 0:
        return False
    return True