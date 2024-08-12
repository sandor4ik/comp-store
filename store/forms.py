from typing import Any
from django.forms import ModelForm
from django.contrib.auth.forms import UserCreationForm
from .models import Customer

class CustomerCreationForm(UserCreationForm):
    class Meta:
        model = Customer
        fields = ['name', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)