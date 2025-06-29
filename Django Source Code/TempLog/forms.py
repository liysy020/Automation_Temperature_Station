from django import forms
from.models import Device

class SearchDevice(forms.Form):
    DEVICE_CHOICES = [
        ('All', 'All'),
        ('Temperature Sensor', 'Temperature Sensor'),
        ('Humility Sensor','Humility Sensor'),
        ('Hygrometer Sensor','Hygrometer Sensor')
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
        fields = ['Name', 'Device_Type', 'Is_Active']
        labels = {
            'Name': 'Sensor Name',
            'Device_Type': 'Sensor Type',
        }
