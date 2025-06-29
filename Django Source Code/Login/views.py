from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from .forms import login_form
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages

def login_request(request):
    if request.method == 'POST':
        form = login_form(request.POST)
        if form.is_valid():
            name = form.cleaned_data['username_form_textinput']
            pwd = form.cleaned_data['password_form_password']
            valuenext= request.POST.get('next')
            user= authenticate(username=name, password=pwd)
            if user is not None:
                login(request, user)
                if valuenext:
                    messages.success(request, "You have successfully logged in")
                    return redirect(valuenext)
                else:
                    return render(request, 'welcome.html', {'user_auth': True})
            else:
                return render(request, 'login.html', {'form': form, 'error': 'The username or password is incorrect'})
    else:
        form = login_form()
        return render(request, 'login.html', {'form': form})

def logout_request(request):
    logout (request)
    return redirect('/')