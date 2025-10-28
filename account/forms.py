from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User

#REGİSTER FORM
class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, label="E-posta)")
    first_name= forms.CharField(required=False)
    last_name= forms.CharField(required=False)

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')
      
#LOGIN FORM
class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(label="Kullanıcı Adı")
    password = forms.CharField(widget=forms.PasswordInput, label="Şifre")
    
