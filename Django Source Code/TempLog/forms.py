from django import forms
from.models import Device, Recipient, EmailSetting

class SearchDevice(forms.Form):
    DEVICE_CHOICES = [
        ('All', 'All'),
        ('Temperature Sensor', 'Temperature Sensor'),
        ('Humidity DHT11','Humidity DHT11'),
        ('Humidity DHT22','Humidity DHT22'),
    ]
    STATUS_CHOICES = [
        ('---', '---'),
        ('Active', 'Active'),
        ('Deactive', 'Deactive'),
    ]
    Name = forms.CharField(label = 'Device Name', required = False)
    Device_Type = forms.ChoiceField (label = 'Device Type', choices = DEVICE_CHOICES, initial = 'All')
    Is_Active = forms.ChoiceField (label ='Status', choices = STATUS_CHOICES, initial = '---', required = False)

class RegisterDevice(forms.ModelForm):
    class Meta:
        model = Device
        fields = ['Name', 'Device_Type', 'T_Comfort_Low', 'T_Comfort_High', 'H_Comfort_Low', 'H_Comfort_High', 'Is_Active']
        labels = {
            'Name': 'Sensor Name',
            'Device_Type': 'Sensor Type',
            'T_Comfort_Low': 'Lowest Comfort Temperature',
            'T_Comfort_High': 'Highest Comfert Temperature',
            'H_Comfort_Low': 'Lowest Comfort Humidity',
            'H_Comfort_High': 'Highest Comfort Humidity',
        }

class AddEmailRecipientForm(forms.ModelForm):
    class Meta:
        model = Recipient
        fields = ['Email','Sensor']
    def __init__ (self, *args, **kwargs):
        super(AddEmailRecipientForm, self).__init__(*args, **kwargs)
        try:
            default_sensor = Device.objects.get(Name='All')
            self.fields['Sensor'].initial = default_sensor
        except Sensor.DoesNotExist:
            pass
        self.fields['Sensor'].empty_label = None  # <- This removes "-------"

class UpdateSMTPForm(forms.ModelForm):
    class Meta:
        model = EmailSetting
        fields = ('EMAIL_HOST', 'EMAIL_USE_TLS', 'EMAIL_PORT', 'EMAIL_HOST_USER', 'EMAIL_HOST_PASSWORD')
    def __init__ (self, *args, **kwargs):
        super(UpdateSMTPForm, self).__init__(*args, **kwargs)
        self.fields['EMAIL_HOST'] = forms.CharField(label='SMTP Server Address')
        self.fields['EMAIL_USE_TLS'] = forms.BooleanField(label='Use TLS', required = False)
        self.fields['EMAIL_PORT'] = forms.IntegerField(label='SMTP Port')
        self.fields['EMAIL_HOST_USER'] = forms.CharField(label='Sender Address')
        self.fields['EMAIL_HOST_PASSWORD'] = forms.CharField(label='Password', required = False, widget = forms.PasswordInput)

class DataHistory(forms.Form):
    RANGE_CHOICES = [
        ('1 Week', '1 Week'),
        ('2 Weeks', '2 Weeks'),
        ('3 Weeks', '3 Weeks'),
        ('1 Month', '1 Month'),
        ('2 Months', '2 Months'),
        ('3 Months', '3 Months'),
        ('All', 'All')
    ]
    Range = forms.ChoiceField(label = 'Last', choices = RANGE_CHOICES, initial = '1 Week')
    Sensor = forms.ChoiceField (label = "Sensor")
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["Sensor"].choices = [
            (d.Name, d.Name)
            for d in Device.objects.filter(Is_Active=True).order_by("Name")
        ]