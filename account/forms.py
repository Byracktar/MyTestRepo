from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import CustomUser

# REGISTER FORM
class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, label="E-posta")
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ('first_name', 'last_name', 'email')

# LOGIN FORM
class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(label="E-posta")
    password = forms.CharField(widget=forms.PasswordInput, label="Şifre")
