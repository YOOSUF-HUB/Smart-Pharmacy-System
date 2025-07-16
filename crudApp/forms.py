from django import forms
from crudApp.models import Student
          
class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['sno', 'sage' ,'sname', 'sclass', 'saddress']
        widgets = {
            'sno': forms.TextInput(attrs={'class': 'form-control', 'placeholder': ' '}),
            'sage': forms.TextInput(attrs={'class': 'form-control', 'placeholder': ' '}),
            'sdob': forms.DateInput(attrs={'class': 'form-control', 'placeholder': 'YYYY-MM-DD', 'type': 'date'}),
            'sname': forms.TextInput(attrs={'class': 'form-control', 'placeholder': ' '}),
            'sclass': forms.TextInput(attrs={'class': 'form-control', 'placeholder': ' '}),
            'saddress': forms.TextInput(attrs={'class': 'form-control', 'placeholder': ' '}),
        }