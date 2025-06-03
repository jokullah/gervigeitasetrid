from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.auth.models import User
from django.db import IntegrityError

def login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        # Basic validation
        if not email:
            return render(request, 'login.html', {'error': 'Vinsamlegast sláðu inn netfang'})
            
        if not password:
            return render(request, 'login.html', {'error': 'Vinsamlegast sláðu inn lykilorð'})
            
        if email[-6:] != "@hi.is":
            return render(request, 'login.html', {'error': 'Vinsamlegast notaðu @hi.is tölvupóstfang'})
            
        try:
            user = User.objects.get(email=email)
            if user.check_password(password):
                auth_login(request, user)
                return redirect('/')
            else:
                return render(request, 'login.html', {'error': 'Rangt lykilorð'})
        except User.DoesNotExist:
            return render(request, 'login.html', {'error': 'Netfang er ekki skráð'})
    
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
            return redirect(reverse('auth'))  # Use reverse to get the correct URL
        except IntegrityError:
            # If username already exists, add a number to it
            base_username = username
            counter = 1
            while True:
                try:
                    username = f"{base_username}{counter}"
                    user = User.objects.create_user(username=username, email=email, password=password1)
                    auth_login(request, user)
                    return redirect(reverse('auth'))  # Use reverse to get the correct URL
                except IntegrityError:
                    counter += 1
                    
    return render(request, 'signup.html')

def logout(request):
    auth_logout(request)
    return redirect('/') 