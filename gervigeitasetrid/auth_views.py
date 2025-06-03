from django.contrib.auth import authenticate, login as auth_login
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.auth.models import User
from django.db import IntegrityError

def login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        try:
            user = User.objects.get(email=email)
            if user.check_password(password):
                auth_login(request, user)
                return redirect('/')  # Redirect to home page after login
        except User.DoesNotExist:
            pass
        return render(request, 'login.html', {'error': 'Invalid credentials'})
    
    return render(request, 'login.html')

def signup(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        
        # Basic validation
        if password1 != password2:
            return render(request, 'signup.html', {'error': 'Lykilorðin eru ekki eins'})
        
        if len(password1) < 8:
            return render(request, 'signup.html', {'error': 'Lykilorðið þarf að vera að minnsta kosti 8 stafir'})
        
        if email[-6:] != "@hi.is":
            return render(request, 'signup.html', {'error': 'Vinsamlegast notaðu @hi.is tölvupóstfang'})
            
        try:
            # Check if email already exists
            if User.objects.filter(email=email).exists():
                return render(request, 'signup.html', {'error': 'Netfang er nú þegar skráð'})
                
            # Create new user with email as username
            username = email.split('@')[0]  # Use part before @ as username
            user = User.objects.create_user(username=username, email=email, password=password1)
            # Log the user in
            auth_login(request, user)
            return redirect('/')  # Redirect to home page after signup
        except IntegrityError:
            # If username already exists, add a number to it
            base_username = username
            counter = 1
            while True:
                try:
                    username = f"{base_username}{counter}"
                    user = User.objects.create_user(username=username, email=email, password=password1)
                    auth_login(request, user)
                    return redirect('/')
                except IntegrityError:
                    counter += 1
                    
    return render(request, 'signup.html') 