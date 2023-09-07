from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from attendance_app.models import DailyHours, Punch, CustomUser, TimeclockBox, WeeklyHours
from datetime import timedelta
import datetime
from django.http import JsonResponse

def user_login(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            if user.user_type == 'ADMIN':
                return redirect('admin_panel')
            else:
                return redirect('employee_panel')
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'login.html')

def week_string_to_dates(week_string):
    if not week_string:
        # Default to the current week if week_string is empty
        today = datetime.datetime.today()
        start_date = today - datetime.timedelta(days=today.weekday())
        end_date = start_date + datetime.timedelta(days=6)
        return start_date, end_date

    parts = week_string.split("-W")
    if len(parts) != 2 or not parts[0] or not parts[1]:
        # If the string doesn't split correctly into two non-empty parts, default to the current week
        today = datetime.datetime.today()
        start_date = today - datetime.timedelta(days=today.weekday())
        end_date = start_date + datetime.timedelta(days=6)
        return start_date, end_date

    year, week = parts
    year = int(year)
    week = int(week)

    # Calculate start date (Monday) of the given week number
    start_date = datetime.datetime.strptime(f'{year}-W{week - 1}-1', "%Y-W%U-%w").date()

    end_date = start_date + datetime.timedelta(days=6)  # Add 6 days to get to Sunday

    return start_date, end_date

def get_weekly_data(request):
    week_string = request.GET.get('week')
    start_date, end_date = week_string_to_dates(week_string)

    users = CustomUser.objects.all()
    weekly_users_data = []

    for user in users:
        punches = Punch.objects.filter(user=user, timestamp__date__range=(start_date, end_date)).order_by('timestamp')
        
        daily_hours = {}
        for day in (start_date + datetime.timedelta(n) for n in range(7)):
            daily_hours[day] = timedelta()

        in_time = None
        for punch in punches:
            if punch.punch_type == 'IN':
                in_time = punch.timestamp
            elif punch.punch_type == 'OUT' and in_time:
                out_time = punch.timestamp
                duration = out_time - in_time
                daily_hours[punch.timestamp.date()] += duration
                in_time = None

        weekly_users_data.append({
            'user': user.username,
            'daily_hours': daily_hours
        })

    # Convert data to a format suitable for JsonResponse
    data = {
        'users_data': [
            {
                'username': item['user'],
                'hours': {str(date): str(hours) for date, hours in item['daily_hours'].items()}
            }
            for item in weekly_users_data
        ]
    }

    return JsonResponse(data)


def calculate_and_store_weekly_hours(user, start_date):
    # Get the end date of the week
    end_date = start_date + timedelta(days=6)
    
    # Fetch daily hours records for the week
    daily_records = DailyHours.objects.filter(user=user, date__range=[start_date, end_date])
    
    # Aggregate the total hours for the week
    total_weekly_hours = sum([record.total_hours for record in daily_records], timedelta())
    
    # Store the result in the WeeklyHours table
    weekly_hours_record, created = WeeklyHours.objects.get_or_create(
        user=user, 
        week_start_date=start_date, 
        defaults={'total_hours': timedelta(hours=0)}  # Provide a default value
    )
    weekly_hours_record.total_hours = total_weekly_hours
    weekly_hours_record.save()


def calculate_and_store_daily_hours(user, date):
    daily_punches = Punch.objects.filter(user=user, timestamp__date=date).order_by('timestamp')
    total_hours = timedelta()
    in_time = None
    for punch in daily_punches:
        if punch.punch_type == 'IN':
            in_time = punch.timestamp
        elif punch.punch_type == 'OUT' and in_time:
            out_time = punch.timestamp
            duration = out_time - in_time
            total_hours += duration
            in_time = None

    # When getting or creating the DailyHours record, provide a default value for total_hours
    daily_hours_record, created = DailyHours.objects.get_or_create(
        user=user, 
        date=date, 
        defaults={'total_hours': timedelta(hours=0)}  # Provide a default value
    )

def punch_in(request):
    # If employee_number is provided, use that. Otherwise, use the logged-in user's information.
    employee_number = request.GET.get('employee_number')
    if employee_number:
        user = CustomUser.objects.get(employee_number=employee_number)
    else:
        user = request.user
    
    # Check if the user is authenticated
    if not user.is_authenticated:
        return JsonResponse({'status': 'error', 'message': 'User not authenticated'})

    # Create a new punch in record
    Punch.objects.create(user=user, punch_type='IN')
    
    # Calculate and store daily and weekly hours
    today = datetime.datetime.today().date()
    start_date = today - datetime.timedelta(days=today.weekday())
    calculate_and_store_daily_hours(user, today)
    calculate_and_store_weekly_hours(user, start_date)
    
    return JsonResponse({'status': 'success', 'message': 'Punched In'})

def punch_out(request):
    # If employee_number is provided, use that. Otherwise, use the logged-in user's information.
    employee_number = request.GET.get('employee_number')
    if employee_number:
        user = CustomUser.objects.get(employee_number=employee_number)
    else:
        user = request.user
    
    # Check if the user is authenticated
    if not user.is_authenticated:
        return JsonResponse({'status': 'error', 'message': 'User not authenticated'})

    # Create a new punch out record
    Punch.objects.create(user=user, punch_type='OUT')
    
    # Calculate and store daily and weekly hours
    today = datetime.datetime.today().date()
    start_date = today - datetime.timedelta(days=today.weekday())
    calculate_and_store_daily_hours(user, today)
    calculate_and_store_weekly_hours(user, start_date)
    
    return JsonResponse({'status': 'success', 'message': 'Punched Out'})




def register_box(request):
    if request.method == "POST":
        box_id = request.POST.get('boxId')
        location = request.POST.get('boxLocation')

        # Check if box with the same ID already exists
        if TimeclockBox.objects.filter(box_id=box_id).exists():
            return JsonResponse({'status': 'error', 'message': 'Box with this ID already exists.'})

        # Create a new box entry
        TimeclockBox.objects.create(box_id=box_id, location=location)
        return JsonResponse({'status': 'success', 'message': 'Box registered successfully!'})

@login_required
def admin_panel(request):
    punches = Punch.objects.all()
    users = CustomUser.objects.all()

    # Get the date from the request or default to today's date
    date_filter = request.GET.get('date') or datetime.datetime.today().strftime('%Y-%m-%d')
    week_filter = request.GET.get('week')  # Extract the week parameter

    # Daily data processing
    users_data = []
    for user in users:
        user_punches = Punch.objects.filter(user=user, timestamp__date=date_filter).order_by('timestamp')
        total_hours = timedelta()
        in_time = None

        user_data = {
            'user': user,
            'punches': [],
            'total_hours': None
        }

        for punch in user_punches:
            if punch.punch_type == 'IN':
                in_time = punch.timestamp
            elif punch.punch_type == 'OUT' and in_time:
                out_time = punch.timestamp
                duration = out_time - in_time
                total_hours += duration
                user_data['punches'].append((in_time, out_time))
                in_time = None

        user_data['total_hours'] = total_hours
        users_data.append(user_data)

    # Weekly data processing
    if week_filter:
        start_date, end_date = week_string_to_dates(week_filter)
        weekly_data = []  # This will store the weekly data for all users

        for user in users:
            weekly_hours = WeeklyHours.objects.filter(user=user, week_start_date=start_date).first()
            if weekly_hours:
                weekly_data.append({
                    'user': user,
                    'total_hours': weekly_hours.total_hours
                })

    context = {
        'punches': punches,
        'users': users,
        'users_data': users_data,
        'date_filter': date_filter,
        'weekly_data': weekly_data if week_filter else None,  # Pass the weekly data to the template
        'week_filter': week_filter
    }

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # If it's an AJAX request, return only the table content
        return render(request, 'daily_hours_table.html', context)
    else:
        # Otherwise, return the entire page content
        return render(request, 'admin_panel.html', context)



@login_required
def employee_panel(request):
    user = request.user
    is_remote = user.groups.filter(name='Remote Employee').exists()
    user_punches = Punch.objects.filter(user=user).order_by('-timestamp')
    
    # Get daily hours from the DailyHours table
    date_filter = request.GET.get('date') or datetime.datetime.today().strftime('%Y-%m-%d')
    daily_hours_record = DailyHours.objects.filter(user=user, date=date_filter).first()
    total_hours = daily_hours_record.total_hours if daily_hours_record else timedelta()

    # For weekly hours:
    week_filter = request.GET.get('week') or datetime.datetime.today().strftime('%Y-W')
    start_date, end_date = week_string_to_dates(week_filter)

    weekly_hours_records = DailyHours.objects.filter(user=user, date__range=[start_date, end_date])
    
    weekly_hours = {}
    for record in weekly_hours_records:
        weekly_hours[record.date.strftime('%A')] = record.total_hours
    # Calculate total weekly hours
    total_weekly_hours = sum(weekly_hours.values(), timedelta())

    return render(request, 'employee_panel.html', {
        'is_remote': is_remote, 
        'user_punches': user_punches,
        'date_filter': date_filter,
        'total_hours': total_hours,
        'weekly_hours': weekly_hours,
        'total_weekly_hours': total_weekly_hours,  # Pass the total weekly hours to the template
        'week_filter': week_filter
    })

@login_required
def remote_punch_clock(request):
    # Ensure the user is a remote employee
    if not request.user.groups.filter(name='Remote Employee').exists():
        return redirect('employee_panel')  # Redirect to a different page if not a remote employee
