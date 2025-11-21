from django.db import models
import secrets

def generate_api_key():
    return secrets.token_hex(32) # 64-character hex string

class Device(models.Model):
    DEVICE_CHOICES = [
        ('Temperature Sensor', 'Temperature Sensor'),
        ('Humidity DHT11','Humidity DHT11'),
        ('Humidity DHT22','Humidity DHT22'),
    ]
    id = models.AutoField(primary_key=True)
    Name = models.CharField(max_length=50, unique=True)
    Device_Type = models.CharField (choices = DEVICE_CHOICES, max_length=50, default = 'Temperature Sensor')
    T_Comfort_Low = models.DecimalField(max_digits=5, decimal_places=1, default=0)
    T_Comfort_High = models.DecimalField(max_digits=5, decimal_places=1, default=0)
    H_Comfort_Low = models.DecimalField(max_digits=5, decimal_places=1, default=0)
    H_Comfort_High = models.DecimalField(max_digits=5, decimal_places=1, default=0)
    Api_Key = models.CharField(max_length=128, blank=True, editable=False)
    Is_Active = models.BooleanField(default=True)
    Created_At = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.Api_Key:
            self.Api_Key = generate_api_key()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.Name

class DeviceData(models.Model):
    id = models.AutoField(primary_key=True)
    Sensor = models.ForeignKey(Device, on_delete=models.CASCADE)
    Temp = models.DecimalField(max_digits=5, decimal_places=1, blank=True)
    Humi = models.DecimalField(max_digits=5, decimal_places=1, blank=True)
    Created_At = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"Sensor: {self.Sensor}, Temp: {self.Temp}, Humi: {self.Humi} at {self.Created_At}"

class EmailSetting(models.Model):
    id = models.AutoField(primary_key=True)
    EMAIL_HOST = models.CharField(max_length=255,default = 'smtp.example.com')
    EMAIL_USE_TLS = models.BooleanField(default=False)
    EMAIL_PORT = models.IntegerField(default = 25)
    EMAIL_HOST_USER = models.CharField(max_length=255,default = 'user@example.com')
    EMAIL_HOST_PASSWORD = models.CharField(max_length=255, null = True)
    def __str__(self):
        return 'SMTP server settings for '+ EMAIL_HOST

class Recipient (models.Model):
    id = models.AutoField(primary_key=True)
    Email = models.CharField(max_length=100)
    Sensor = models.ForeignKey(Device, on_delete=models.CASCADE)
    Created_At = models.DateTimeField(auto_now=True)
    def __str__(self):
        return self.Email

class Notification (models.Model):
    id = models.AutoField(primary_key=True)
    User = models.ForeignKey(Recipient, on_delete=models.CASCADE)
    Sensor = models.ForeignKey(Device, on_delete=models.CASCADE)
    Message = models.CharField(max_length=255)
