from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Avg, Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
import json
from Members.models import MemberData
from .models import DailyLog, WeightGoal, MealEntry

def member_food_dashboard_log(request):
    """Member login view"""
    if request.method == "POST":
        mid = request.POST['mid']
        access = request.POST["accessid"]

        if MemberData.objects.filter(id=mid, Access_Token_Id=access, Active_status=True).exists():
            request.session["accessvalue"] = f'{mid}{access}'
            return redirect('member_dashboard', member_id=mid)
        else:
            messages.error(request, "Invalid access credentials or inactive account")
            return redirect("member_food_dashboard_log")
        
    return render(request, 'food_log/member_logon.html')

def member_dashboard(request, member_id):
    """Main member dashboard with overview"""
    try:
        member = get_object_or_404(MemberData, id=member_id, Active_status=True)
        accessvalue = request.session.get("accessvalue")
        match = f"{member.id}{member.Access_Token_Id}" 
        
        if not accessvalue or accessvalue != match:
            messages.error(request, "Please login to continue")
            return redirect("member_food_dashboard_log")
            
    except Exception as e:
        messages.error(request, "Session expired. Please login again")
        return redirect("member_food_dashboard_log")

    # Dashboard statistics
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    # Recent logs with meal counts
    recent_logs = DailyLog.objects.filter(
        member=member, 
        date__gte=week_ago
    ).prefetch_related('meals').order_by('-date')
    
    # Weight progress
    weight_logs = DailyLog.objects.filter(
        member=member, 
        weight__isnull=False,
        date__gte=month_ago
    ).order_by('date')
    
    # Today's meals
    today_log = DailyLog.objects.filter(member=member, date=today).first()
    today_meals = []
    if today_log:
        today_meals = today_log.meals.all().order_by('time_consumed', 'created_at')
    
    # Statistics
    total_logs = DailyLog.objects.filter(member=member).count()
    total_meals = MealEntry.objects.filter(daily_log__member=member).count()
    avg_daily_meals = MealEntry.objects.filter(
        daily_log__member=member,
        daily_log__date__gte=week_ago
    ).values('daily_log__date').annotate(meal_count=Count('id')).aggregate(
        avg_meals=Avg('meal_count')
    )['avg_meals'] or 0
    
    # Pending admin comments
    pending_comments = MealEntry.objects.filter(
        daily_log__member=member,
        admin_comment__isnull=False,
        admin_comment__gt=''
    ).order_by('-comment_date')[:5]
    
    context = {
        'member': member,
        'recent_logs': recent_logs,
        'weight_logs': weight_logs,
        'today_meals': today_meals,
        'today_log': today_log,
        'today': today,
        'total_logs': total_logs,
        'total_meals': total_meals,
        'avg_daily_meals': round(avg_daily_meals, 1),
        'pending_comments': pending_comments,
    }
    
    return render(request, 'food_log/member_dashboard.html', context)

def add_meal_entry(request, member_id):
    """Add new meal entry"""
    try:
        member = get_object_or_404(MemberData, id=member_id, Active_status=True)
        accessvalue = request.session.get("accessvalue")
        match = f"{member.id}{member.Access_Token_Id}"
        
        if not accessvalue or accessvalue != match:
            return JsonResponse({'success': False, 'error': 'Unauthorized access'})
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': 'Invalid member'})
    
    if request.method == 'POST':
        date_str = request.POST.get('date')
        meal_type = request.POST.get('meal_type')
        meal_description = request.POST.get('meal_description')
        custom_meal_name = request.POST.get('custom_meal_name')
        time_consumed = request.POST.get('time_consumed')
        calories_estimate = request.POST.get('calories_estimate')
        weight = request.POST.get('weight')
        daily_notes = request.POST.get('daily_notes')
        food_image = request.FILES.get('food_image')
        
        try:
            # Parse date with multiple formats
            log_date = None
            if date_str:
                for fmt in ('%Y-%m-%d', '%b. %d, %Y', '%B %d, %Y'):
                    try:
                        log_date = datetime.strptime(date_str, fmt).date()
                        break
                    except ValueError:
                        continue
                if log_date is None:
                    raise ValueError(f"Date '{date_str}' does not match expected formats.")
            else:
                log_date = timezone.now().date()
            
            # Get or create daily log
            daily_log, created = DailyLog.objects.get_or_create(
                member=member,
                date=log_date,
                defaults={'notes': daily_notes or ''}
            )
            
            # Update weight if provided
            if weight:
                daily_log.weight = float(weight)
            
            # Update notes if provided
            if daily_notes:
                daily_log.notes = daily_notes
            
            daily_log.save()
            
            # Create meal entry
            meal_entry = MealEntry.objects.create(
                daily_log=daily_log,
                meal_type=meal_type,
                meal_description=meal_description,
                custom_meal_name=custom_meal_name if meal_type == 'other' else None,
                time_consumed=time_consumed if time_consumed else None,
                calories_estimate=int(calories_estimate) if calories_estimate else None,
                food_image=food_image
            )
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True, 
                    'message': f'{meal_entry.get_meal_display_name()} added successfully!'
                })
            else:
                messages.success(request, f'{meal_entry.get_meal_display_name()} added successfully!')
                return redirect('member_dashboard', member_id=member_id)
                
        except Exception as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': str(e)})
            else:
                messages.error(request, f'Error adding meal: {str(e)}')
                return redirect('member_dashboard', member_id=member_id)
    
    # GET request - show form
    context = {
        'member': member,
        'meal_choices': MealEntry.MEAL_CHOICES,
        'today': timezone.now().date(),
    }
    
    return render(request, 'food_log/add_meal.html', context)

def view_daily_log(request, member_id, date_str):
    """View detailed daily log with all meals"""
    try:
        member = get_object_or_404(MemberData, id=member_id, Active_status=True)
        accessvalue = request.session.get("accessvalue")
        match = f"{member.id}{member.Access_Token_Id}"
        
        if not accessvalue or accessvalue != match:
            messages.error(request, "Please login to continue")
            return redirect("member_food_dashboard_log")
            
    except Exception as e:
        messages.error(request, "Invalid access")
        return redirect("member_food_dashboard_log")
    
    try:
        log_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except:
        messages.error(request, "Invalid date format")
        return redirect('member_dashboard', member_id=member_id)
    
    daily_log = get_object_or_404(DailyLog, member=member, date=log_date)
    meals = daily_log.meals.all().order_by('time_consumed', 'created_at')
    
    context = {
        'member': member,
        'daily_log': daily_log,
        'meals': meals,
        'log_date': log_date,
    }
    
    return render(request, 'food_log/daily_log_detail.html', context)


def member_history(request, member_id):
    """View member's complete history with pagination"""
    try:
        member = get_object_or_404(MemberData, id=member_id, Active_status=True)
        accessvalue = request.session.get("accessvalue")
        match = f"{member.id}{member.Access_Token_Id}"
        
        if not accessvalue or accessvalue != match:
            messages.error(request, "Please login to continue")
            return redirect("member_food_dashboard_log")
            
    except Exception as e:
        messages.error(request, "Invalid access")
        return redirect("member_food_dashboard_log")
    
    # Get filter parameters
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    meal_type = request.GET.get('meal_type')
    
    # Build query
    logs_query = DailyLog.objects.filter(member=member)
    
    if date_from:
        try:
            date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
            logs_query = logs_query.filter(date__gte=date_from)
        except:
            pass
    
    if date_to:
        try:
            date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
            logs_query = logs_query.filter(date__lte=date_to)
        except:
            pass
    
    logs = logs_query.prefetch_related('meals').order_by('-date')
    
    # Filter meals if meal_type is specified
    if meal_type:
        for log in logs:
            log.filtered_meals = log.meals.filter(meal_type=meal_type)
    
    # Pagination
    paginator = Paginator(logs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'member': member,
        'page_obj': page_obj,
        'meal_choices': MealEntry.MEAL_CHOICES,
        'filters': {
            'date_from': date_from.strftime('%Y-%m-%d') if date_from else '',
            'date_to': date_to.strftime('%Y-%m-%d') if date_to else '',
            'meal_type': meal_type or '',
        }
    }
    
    return render(request, 'food_log/member_history.html', context)

def delete_meal_entry(request, member_id, meal_id):
    """Delete a meal entry"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'})
    
    try:
        member = get_object_or_404(MemberData, id=member_id, Active_status=True)
        accessvalue = request.session.get("accessvalue")
        match = f"{member.id}{member.Access_Token_Id}"
        
        if not accessvalue or accessvalue != match:
            return JsonResponse({'success': False, 'error': 'Unauthorized access'})
        
        meal = get_object_or_404(MealEntry, id=meal_id, daily_log__member=member)
        meal_name = meal.get_meal_display_name()
        meal.delete()
        
        return JsonResponse({
            'success': True, 
            'message': f'{meal_name} deleted successfully!'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

def member_logout(request):
    """Logout member"""
    if 'accessvalue' in request.session:
        del request.session['accessvalue']
    messages.info(request, "Logged out successfully")
    return redirect('member_food_dashboard_log')

# Admin Views for managing member logs


# Member Daily Logging Views (Single Page Interface)
def daily_log_entry(request, member_id=None):
    """Simple single-page view for members to enter daily weight and food data"""
    if member_id:
        member = get_object_or_404(MemberData, id=member_id, Active_status=True)
    else:
        # For URL without member_id, you might want to show a member selection page
        return redirect('member_selection_for_logging')
    
    today = timezone.now().date()
    
    # Check if log already exists for today
    existing_log = DailyLog.objects.filter(member=member, date=today).first()
    
    if request.method == 'POST':
        weight = request.POST.get('weight')
        meals = request.POST.get('meals_consumed')
        notes = request.POST.get('notes', '')
        food_image = request.FILES.get('food_image')
        
        if weight and meals:
            if existing_log:
                # Update existing log
                existing_log.weight = float(weight)
                existing_log.meals_consumed = meals
                existing_log.notes = notes
                if food_image:
                    existing_log.food_image = food_image
                existing_log.save()
                success_message = 'Your daily log has been updated successfully! 🎉'
            else:
                # Create new log
                DailyLog.objects.create(
                    member=member,
                    date=today,
                    weight=float(weight),
                    meals_consumed=meals,
                    notes=notes,
                    food_image=food_image
                )
                success_message = 'Your daily log has been saved successfully! 🎉'
            
            # Return success page instead of redirect
            context = {
                'member': member,
                'success': True,
                'message': success_message,
                'show_form': False
            }
            return render(request, 'food_log/daily_log_simple.html', context)
        else:
            error_message = 'Please fill in your weight and describe your meals.'
    
    # Get recent logs for reference (last 7 days)
    recent_logs = DailyLog.objects.filter(member=member).order_by('-date')[:7]
    
    context = {
        'member': member,
        'existing_log': existing_log,
        'recent_logs': recent_logs,
        'today': today,
        'show_form': True
    }
    
    return render(request, 'food_log/daily_log_simple.html', context)

def member_selection_for_logging(request):
    """Simple view to select member for daily logging"""
    search_query = request.GET.get('search', '')
    
    members = MemberData.objects.filter(Active_status=True)
    
    if search_query:
        members = members.filter(
            Q(First_Name__icontains=search_query) |
            Q(Last_Name__icontains=search_query) |
            Q(Mobile_Number__icontains=search_query)
        )
    
    context = {
        'members': members[:50],  # Limit to 50 for simple interface
        'search_query': search_query,
    }
    
    return render(request, 'food_log/member_selection_simple.html', context)



# views.py - Add these views to your existing views.py file

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Count, Avg, Q
from django.utils import timezone
from django.http import JsonResponse
from django.core.paginator import Paginator
from datetime import datetime, timedelta
from .models import DailyLog, MealEntry, WeightGoal, MemberData
from django.contrib.auth.models import User

def is_admin(user):
    return user.is_staff or user.is_superuser 

@login_required
#@user_passes_test(is_admin)
def admin_monitoring_dashboard(request):
    """Main admin dashboard for monitoring member food logs and weight"""
    
    # Get date range (last 7 days by default)
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=7)
    
    # Statistics
    total_members = MemberData.objects.filter(Active_status=True).count()
    total_logs_today = DailyLog.objects.filter(date=end_date).count()
    total_meals_today = MealEntry.objects.filter(daily_log__date=end_date).count()
    
    # Recent activity
    recent_logs = DailyLog.objects.select_related('member').prefetch_related('meals').filter(
        date__gte=start_date
    ).order_by('-date', '-created_at')[:10]
    
    # Members with logs today
    members_logged_today = DailyLog.objects.filter(date=end_date).values_list('member__id', flat=True)
    active_members = MemberData.objects.filter(Active_status=True)
    members_not_logged = active_members.exclude(id__in=members_logged_today)
    
    # Weight progress tracking
    weight_goals = WeightGoal.objects.filter(is_active=True).select_related('member')
    
    context = {
        'total_members': total_members,
        'total_logs_today': total_logs_today,
        'total_meals_today': total_meals_today,
        'recent_logs': recent_logs,
        'members_not_logged': members_not_logged[:5],
        'weight_goals': weight_goals[:5],
        'start_date': start_date,
        'end_date': end_date,
    }
    
    return render(request, 'food_log/admin_monitoring_dashboard.html', context)

@login_required
#@user_passes_test(is_admin)
def admin_daily_logs_review(request):
    """Detailed review of daily logs with filtering options"""
    
    # Get filter parameters
    date_filter = request.GET.get('date', timezone.now().date().strftime('%Y-%m-%d'))
    member_filter = request.GET.get('member', '')
    meal_type_filter = request.GET.get('meal_type', '')
    
    # Base queryset
    logs = DailyLog.objects.select_related('member').prefetch_related('meals')
    
    # Apply filters
    if date_filter:
        try:
            filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
            logs = logs.filter(date=filter_date)
        except ValueError:
            logs = logs.filter(date=timezone.now().date())
    
    if member_filter:
        logs = logs.filter(member__id=member_filter)
    
    # Get meals with filtering
    meals = MealEntry.objects.select_related('daily_log__member', 'commented_by')
    
    if date_filter:
        try:
            filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
            meals = meals.filter(daily_log__date=filter_date)
        except ValueError:
            meals = meals.filter(daily_log__date=timezone.now().date())
    
    if member_filter:
        meals = meals.filter(daily_log__member__id=member_filter)
    
    if meal_type_filter:
        meals = meals.filter(meal_type=meal_type_filter)
    
    # Pagination
    logs = logs.order_by('-date', '-created_at')
    meals = meals.order_by('-daily_log__date', 'time_consumed')
    
    logs_paginator = Paginator(logs, 10)
    meals_paginator = Paginator(meals, 20)
    
    logs_page = request.GET.get('logs_page', 1)
    meals_page = request.GET.get('meals_page', 1)
    
    logs_obj = logs_paginator.get_page(logs_page)
    meals_obj = meals_paginator.get_page(meals_page)
    
    # Get members for filter dropdown
    members = MemberData.objects.filter(Active_status=True).order_by('First_Name')
    
    # Meal type choices for filter
    meal_choices = MealEntry.MEAL_CHOICES
    
    context = {
        'logs': logs_obj,
        'meals': meals_obj,
        'members': members,
        'meal_choices': meal_choices,
        'date_filter': date_filter,
        'member_filter': member_filter,
        'meal_type_filter': meal_type_filter,
    }
    
    return render(request, 'food_log/admin_daily_logs_review.html', context)

@login_required
#@user_passes_test(is_admin)
def admin_member_list(request):
    """List of all members with their logging activity"""
    
    # Get search parameters
    search = request.GET.get('search', '')
    status_filter = request.GET.get('status', 'active')
    
    # Base queryset
    members = MemberData.objects.annotate(
        total_logs=Count('daily_logs'),
        recent_logs=Count('daily_logs', filter=Q(daily_logs__date__gte=timezone.now().date() - timedelta(days=7)))
    )
    
    # Apply filters
    if status_filter == 'active':
        members = members.filter(Active_status=True)
    elif status_filter == 'inactive':
        members = members.filter(Active_status=False)
    
    if search:
        members = members.filter(
            Q(First_Name__icontains=search) |
            Q(Last_Name__icontains=search) |
            Q(Mobile_Number__icontains=search) |
            Q(Email__icontains=search)
        )
    
    # Pagination
    members = members.order_by('First_Name')
    paginator = Paginator(members, 20)
    page = request.GET.get('page', 1)
    members_obj = paginator.get_page(page)
    
    context = {
        'members': members_obj,
        'search': search,
        'status_filter': status_filter,
    }
    
    return render(request, 'food_log/admin_member_list.html', context)

@login_required
#@user_passes_test(is_admin)
def add_meal_comment(request):
    """Add admin comment to a meal entry"""
    
    if request.method == 'POST':
        meal_id = request.POST.get('meal_id')
        comment = request.POST.get('comment')
        
        if meal_id and comment:
            try:
                meal = MealEntry.objects.get(id=meal_id)
                meal.admin_comment = comment
                meal.commented_by = request.user
                meal.comment_date = timezone.now()
                meal.save()
                
                messages.success(request, 'Comment added successfully!')
                return JsonResponse({'status': 'success', 'message': 'Comment added successfully!'})
            except MealEntry.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Meal entry not found!'})
        else:
            return JsonResponse({'status': 'error', 'message': 'Missing required fields!'})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method!'})

@login_required
#@user_passes_test(is_admin)
def member_detail_logs(request, member_id):
    """Detailed view of a specific member's logs"""
    
    member = get_object_or_404(MemberData, id=member_id)
    
    # Get date range
    days = int(request.GET.get('days', 30))
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days)
    
    # Get logs
    logs = DailyLog.objects.filter(
        member=member,
        date__gte=start_date
    ).prefetch_related('meals').order_by('-date')
    
    # Get weight goals
    weight_goals = WeightGoal.objects.filter(member=member, is_active=True)
    
    context = {
        'member': member,
        'logs': logs,
        'weight_goals': weight_goals,
        'days': days,
        'start_date': start_date,
        'end_date': end_date,
    }
    
    return render(request, 'food_log/member_detail_logs.html', context)