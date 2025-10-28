from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import CustomUserCreationForm 
from .forms import CustomAuthenticationForm
from django.contrib.auth import authenticate, login, logout

def login_view(request):
    if request.method=="POST":
        form=CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user=form.get_user()
            login(request,user)
            return redirect('home')
    else:
        form=CustomAuthenticationForm()    
    return render(request, 'account/login.html', {'form': form})

def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)#otomatik giriş yapma
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'account/register.html', {'form': form})

def logout_view(request):
    return redirect('login')

def home_view(request):
    return render(request,"account/home.html")