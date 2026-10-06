# core_app/views.py

# --- Django Core Imports ---
from django.shortcuts import render, redirect
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.conf import settings  # To access MongoDB settings
from django.db import transaction  # ✅ ADDED

# --- Third-Party and Utility Imports ---
from pymongo import MongoClient
from bson.objectid import ObjectId  # To work with MongoDB's _id field
import datetime  # For timestamps

# --- Local Services ---
from .services import choose_best_volunteer  # ✅ ADDED


# --- HELPER FUNCTIONS ---
def get_mongo_collection(collection_name):
    """Helper function to connect to a specific MongoDB collection."""
    client = MongoClient(settings.MONGO_URI)
    db = client[settings.MONGO_DB_NAME]
    return db[collection_name]


# --- VIEW FUNCTIONS ---

def landing_page_view(request):
    """Renders the main landing page and fetches a critical alert if one exists."""
    alerts_collection = get_mongo_collection('alerts')
    emergency_alert = alerts_collection.find_one(
        {'is_active': True, 'severity': 'Critical'},
        sort=[('timestamp', -1)]  # -1 means descending order (newest first)
    )
    context = {
        'emergency_alert': emergency_alert
    }
    return render(request, 'core_app/landing_page.html', context)


# inside core_app/views.py

def signup_view(request):
    from .forms import CustomUserCreationForm

    role = request.GET.get("role", None)  # detect role from landing page buttons

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            role = form.cleaned_data.get("role")

            if role == 'volunteer':
                user.is_active = False  # must be approved
                user.is_staff = True

            user.save()
            form.save_m2m()  # just in case

            if role == 'victim':
                login(request, user)
                messages.success(request, "Account created successfully! You are now logged in.")
                return redirect('dashboard')
            else:
                messages.success(request, "Thank you for registering! Your volunteer account is pending admin approval.")
                return redirect('pending_approval')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Error in {field}: {error}")
    else:
        form = CustomUserCreationForm(initial={'role': role} if role else None)

    return render(request, 'core_app/signup.html', {'form': form, 'role': role})


def login_view(request):
    """Handles user login and redirects them based on their role (staff or victim)."""
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.info(request, f"Welcome back, {username}.")
                # SMART REDIRECT based on user role
                if user.is_staff:
                    return redirect('volunteer_dashboard')
                else:
                    return redirect('dashboard')
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Invalid username or password.")  # Error message for form-level errors
    else:
        form = AuthenticationForm()
    return render(request, 'core_app/login.html', {'form': form})


def logout_view(request):
    """Logs the user out and redirects to the login page."""
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('login')


def pending_approval_view(request):
    """Shows a simple page informing volunteers their account is pending review."""
    return render(request, 'core_app/pending_approval.html')


@login_required(login_url='login')
def dashboard_view(request):
    """Victim's dashboard for submitting and viewing their own requests."""
    # Local imports
    from .forms import ReliefRequestForm
    from .models import ReliefRequest

    if request.method == 'POST':
        form = ReliefRequestForm(request.POST)
        if form.is_valid():
            relief_request = form.save(commit=False)
            relief_request.requester = request.user
            relief_request.save()
            messages.success(request, "Your relief request has been submitted!")
            return redirect('dashboard')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Error in {field}: {error}")
    else:
        form = ReliefRequestForm()

    user_requests = request.user.submitted_requests.all().order_by('-created_at')
    alerts_collection = get_mongo_collection('alerts')
    global_alerts = list(alerts_collection.find({'is_active': True}).sort('timestamp', -1))

    context = {
        'form': form,
        'user_requests': user_requests,
        'global_alerts': global_alerts,
    }
    return render(request, 'core_app/dashboard.html', context)

@login_required(login_url='login')
def volunteer_dashboard_view(request):
    """Volunteer/Admin dashboard to view all active requests and show volunteer location info."""
    from .models import ReliefRequest

    if not request.user.is_staff:
        messages.error(request, "You do not have permission to view this page.")
        return redirect('dashboard')

    # Fetch requests and global alerts
    all_requests = ReliefRequest.objects.exclude(status='Completed').order_by('created_at')
    alerts_collection = get_mongo_collection('alerts')
    global_alerts = list(alerts_collection.find({'is_active': True}).sort('timestamp', -1))

    # fetch user's profile if it exists (signals should create it for new users,
    # but handle the case where it is missing)
    profile = getattr(request.user, 'profile', None)

    context = {
        'all_requests': all_requests,
        'global_alerts': global_alerts,
        'profile': profile,  
    }
    return render(request, 'core_app/volunteer_dashboard.html', context)


@login_required(login_url='login')
def assign_request_view(request, request_id):
    """Allows a staff member to assign a pending request to themselves."""
    # Local import
    from .models import ReliefRequest

    if not request.user.is_staff:
        messages.error(request, "You do not have permission to perform this action.")
        return redirect('dashboard')

    try:
        relief_request = ReliefRequest.objects.get(pk=request_id)
        if relief_request.status == 'Pending':
            relief_request.assigned_to_volunteer = request.user
            relief_request.status = 'Assigned'
            relief_request.save()
            messages.success(request, f"You have successfully assigned request #{relief_request.id} to yourself.")
        else:
            messages.warning(request, f"Request #{relief_request.id} has already been assigned.")
    except ReliefRequest.DoesNotExist:
        messages.error(request, "This request does not exist.")

    return redirect('volunteer_dashboard')


# ✅ NEW: Auto-assign to the best volunteer (atomic + race-safe)
@login_required(login_url='login')
@transaction.atomic
def auto_assign_request_view(request, request_id):
    """
    Atomically assign a pending request to the best volunteer chosen by services.choose_best_volunteer.
    Only superuser (NGO/admin) can perform this action (button is shown only to superusers).
    """
    from .models import ReliefRequest

    if not request.user.is_superuser:
        messages.error(request, "Only NGO/admin can auto-assign volunteers.")
        return redirect('dashboard')

    try:
        # Lock the row to avoid double assignment under concurrent clicks
        relief_request = ReliefRequest.objects.select_for_update().get(pk=request_id)
    except ReliefRequest.DoesNotExist:
        messages.error(request, "This request does not exist.")
        return redirect('volunteer_dashboard')

    if relief_request.status != 'Pending':
        messages.warning(request, f"Request #{relief_request.id} is already {relief_request.status}.")
        return redirect('volunteer_dashboard')

    # <-- IMPORTANT: pass the relief_request object to the service function -->
    volunteer = choose_best_volunteer(relief_request, max_active_tasks=1)

    if volunteer is None:
        messages.warning(request, "No eligible volunteers are available right now.")
        return redirect('volunteer_dashboard')

    relief_request.assigned_to_volunteer = volunteer
    relief_request.status = 'Assigned'
    relief_request.save(update_fields=['assigned_to_volunteer', 'status', 'updated_at'])

    messages.success(request, f"Request #{relief_request.id} assigned to {volunteer.username}.")
    return redirect('volunteer_dashboard')


@login_required(login_url='login')
def request_detail_view(request, request_id):
    """Displays details of a single request and allows status updates by staff."""
    # Local imports
    from .forms import ReliefStatusUpdateForm
    from .models import ReliefRequest

    if not request.user.is_staff:
        messages.error(request, "You do not have permission to view this page.")
        return redirect('dashboard')

    try:
        relief_request = ReliefRequest.objects.get(pk=request_id)
    except ReliefRequest.DoesNotExist:
        messages.error(request, "The requested relief request does not exist.")
        return redirect('volunteer_dashboard')

    if request.method == 'POST':
        form = ReliefStatusUpdateForm(request.POST, instance=relief_request)
        if form.is_valid():
            form.save()
            messages.success(request, f"Status for request #{relief_request.id} updated to '{relief_request.get_status_display()}'.")
            return redirect('request_detail', request_id=relief_request.id)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Error in {field}: {error}")
    else:
        form = ReliefStatusUpdateForm(instance=relief_request)

    context = {
        'relief_request': relief_request,
        'form': form,
    }
    return render(request, 'core_app/request_detail.html', context)


@login_required(login_url='login')
def create_alert_view(request):
    """Allows staff to create new global alerts stored in MongoDB."""
    # Local import
    from .forms import AlertForm

    if not request.user.is_superuser:
        messages.error(request, "You do not have permission to post alerts.")
        return redirect('dashboard')

    alerts_collection = get_mongo_collection('alerts')

    if request.method == 'POST':
        form = AlertForm(request.POST)
        if form.is_valid():
            alert_data = form.cleaned_data
            alert_data['posted_by'] = request.user.username
            alert_data['timestamp'] = datetime.datetime.now()
            alerts_collection.insert_one(alert_data)
            messages.success(request, "New alert posted successfully!")
            return redirect('create_alert')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Error in {field}: {error}")
    else:
        form = AlertForm()

    active_alerts = list(alerts_collection.find({'is_active': True}).sort('timestamp', -1))

    context = {
        'form': form,
        'active_alerts': active_alerts,
    }
    return render(request, 'core_app/create_alert.html', context)

from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from core_app.models import Profile
from django.utils import timezone

@csrf_exempt  # allows JS fetch post without csrf token complexity
@login_required
def update_location(request):
    """
    Updates volunteer's latitude and longitude via frontend 'Set My Location' button.
    """
    if request.method == "POST":
        try:
            lat_raw = request.POST.get("latitude")
            lon_raw = request.POST.get("longitude")
            if lat_raw is None or lon_raw is None:
                return JsonResponse({"status": "error", "message": "Missing latitude/longitude"}, status=400)

            lat = float(lat_raw)
            lon = float(lon_raw)

            profile = request.user.profile  # created automatically if you set up the signal
            profile.latitude = lat
            profile.longitude = lon
            profile.location_updated_at = timezone.now()
            profile.save()

            return JsonResponse({"status": "success", "message": "Location updated successfully!"})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)

    return JsonResponse({"status": "error", "message": "Invalid request"}, status=400)
