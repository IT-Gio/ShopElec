from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

User = get_user_model()


def logout_view(request):
    logout(request)
    return redirect("home")


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            return redirect("home")
        else:
            messages.error(request, "Invalid username or password.")
            return render(request, "users/login.html")

    return render(request, "users/login.html")


def signup_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")

        if not all([username, email, password1, password2]):
            messages.error(request, "All fields are required.")
            return render(request, "users/signup.html")

        if password1 != password2:
            messages.error(request, "Passwords do not match.")
            return render(request, "users/signup.html")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
            return render(request, "users/signup.html")

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
            return render(request, "users/signup.html")

        # Validate password strength
        try:
            validate_password(password1)
        except ValidationError as e:
            for error in e:
                messages.error(request, error)
            return render(request, "users/signup.html")

        # Create user
        user = User.objects.create_user(username=username, email=email, password=password1)

        # Option 1: auto-login after signup
        # login(request, user)
        # messages.success(request, f"Welcome, {user.username}!")
        # return redirect("home")

        # Option 2: redirect to login page (current behavior)
        messages.success(request, f"Account created for {user.username}! You can now log in.")
        return redirect("login")

    return render(request, "users/signup.html")
