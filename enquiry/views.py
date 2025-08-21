from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.shortcuts import render
from django.db.models import Count, Q
from django.utils import timezone
from datetime import datetime, timedelta

from .models import EnquiryData, EnquiryStatus
from django.core.paginator import Paginator
from .forms import EnquiryDataForm, EnquiryStatusForm, EnquiryFilterForm
from Members.models import MemberData




def enquiries(request):
    """Dashboard view with comprehensive statistics"""
    
    # Basic counts
    total_enquiries = EnquiryData.objects.count()
    converted_enquiries = EnquiryData.objects.filter(conversion=True).count()
    pending_enquiries = EnquiryData.objects.filter(conversion=False).count()
    
    # Status breakdown
    status_breakdown = EnquiryData.objects.values('status').annotate(
        count=Count('status')
    ).order_by('-count')
    
    # Recent enquiries (last 30 days)
    thirty_days_ago = timezone.now().date() - timedelta(days=30)
    recent_enquiries = EnquiryData.objects.filter(
        date_created__gte=thirty_days_ago
    ).count()
    
    # This month's enquiries
    current_month = timezone.now().replace(day=1).date()
    this_month_enquiries = EnquiryData.objects.filter(
        date_created__gte=current_month
    ).count()
    
    # Today's enquiries
    today = timezone.now().date()
    today_enquiries = EnquiryData.objects.filter(
        date_created=today
    ).count()
    
    # Conversion rate
    conversion_rate = (converted_enquiries / total_enquiries * 100) if total_enquiries > 0 else 0
    
    # Follow-up statistics
    total_followups = EnquiryStatus.objects.count()
    avg_followups = (total_followups / total_enquiries) if total_enquiries > 0 else 0
    
    # Enquiries needing follow-up (next_follow_up_date is today or past)
    needs_followup = EnquiryData.objects.filter(
        Q(next_follow_up_date__lte=today) & Q(conversion=False)
    ).exclude(status__in=['completed', 'rejected', 'not_required']).count()
    
    # Overdue follow-ups (past due)
    overdue_followups = EnquiryData.objects.filter(
        Q(next_follow_up_date__lt=today) & Q(conversion=False)
    ).exclude(status__in=['completed', 'rejected', 'not_required']).count()
    
    # Today's follow-ups (due today)
    today_followups = EnquiryData.objects.filter(
        Q(next_follow_up_date=today) & Q(conversion=False)
    ).exclude(status__in=['completed', 'rejected', 'not_required']).count()
    
    # Recent enquiries for display
    recent_enquiries_list = EnquiryData.objects.order_by('-date_created')[:5]
    
    # Recent follow-ups
    recent_followups = EnquiryStatus.objects.select_related('enquiry').order_by('-date_of_status')[:5]
    
    # Call status breakdown for recent follow-ups
    call_status_breakdown = EnquiryStatus.objects.values('call_status').annotate(
        count=Count('call_status')
    ).order_by('-count')
    
    # Today's pending follow-ups for quick display (top 5)
    todays_pending_followups = EnquiryData.objects.filter(
        Q(next_follow_up_date__lte=today) & Q(conversion=False)
    ).exclude(status__in=['completed', 'rejected', 'not_required']).order_by('next_follow_up_date')[:5]
    
    # Monthly trend data (last 6 months)
    monthly_data = []
    for i in range(5, -1, -1):
        month_start = (timezone.now().replace(day=1) - timedelta(days=32*i)).replace(day=1).date()
        next_month = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1)
        
        month_enquiries = EnquiryData.objects.filter(
            date_created__gte=month_start,
            date_created__lt=next_month
        ).count()
        
        month_conversions = EnquiryData.objects.filter(
            date_created__gte=month_start,
            date_created__lt=next_month,
            conversion=True
        ).count()
        
        monthly_data.append({
            'month': month_start.strftime('%b %Y'),
            'enquiries': month_enquiries,
            'conversions': month_conversions
        })
    
    context = {
        # Basic stats
        'total_enquiries': total_enquiries,
        'converted_enquiries': converted_enquiries,
        'pending_enquiries': pending_enquiries,
        'conversion_rate': round(conversion_rate, 1),
        
        # Time-based stats
        'recent_enquiries_count': recent_enquiries,
        'this_month_enquiries': this_month_enquiries,
        'today_enquiries': today_enquiries,
        
        # Follow-up stats
        'total_followups': total_followups,
        'avg_followups': round(avg_followups, 1),
        'needs_followup': needs_followup,
        'overdue_followups': overdue_followups,
        'today_followups': today_followups,
        
        # Breakdowns
        'status_breakdown': status_breakdown,
        'call_status_breakdown': call_status_breakdown,
        
        # Recent data
        'recent_enquiries_list': recent_enquiries_list,
        'recent_followups': recent_followups,
        'monthly_data': monthly_data,
        'todays_pending_followups': todays_pending_followups,
        
        # Current date for template
        'today': today,
    }
    
    return render(request, "enquiries/index.html", context)


def todays_followups(request):
    """View for today's and pending follow-ups"""
    today = timezone.now().date()
    
    # Get all enquiries that need follow-up (today or overdue)
    followup_enquiries = EnquiryData.objects.filter(
        Q(next_follow_up_date__lte=today) & Q(conversion=False)
    ).exclude(status__in=['completed', 'rejected', 'not_required']).order_by('next_follow_up_date', 'name')
    
    # Separate today's and overdue
    todays_followups = followup_enquiries.filter(next_follow_up_date=today)
    overdue_followups = followup_enquiries.filter(next_follow_up_date__lt=today)
    
    # Get upcoming follow-ups (next 7 days)
    next_week = today + timedelta(days=7)
    upcoming_followups = EnquiryData.objects.filter(
        Q(next_follow_up_date__gt=today) & 
        Q(next_follow_up_date__lte=next_week) & 
        Q(conversion=False)
    ).exclude(status__in=['completed', 'rejected', 'not_required']).order_by('next_follow_up_date', 'name')
    
    # Statistics
    total_due = followup_enquiries.count()
    today_count = todays_followups.count()
    overdue_count = overdue_followups.count()
    upcoming_count = upcoming_followups.count()
    
    # Handle quick status updates via AJAX/form submission
    if request.method == 'POST' and 'enquiry_id' in request.POST:
        enquiry_id = request.POST.get('enquiry_id')
        quick_status = request.POST.get('quick_status')
        quick_notes = request.POST.get('quick_notes', '')
        
        try:
            enquiry = EnquiryData.objects.get(id=enquiry_id)
            
            # Create new status update
            status_update = EnquiryStatus.objects.create(
                enquiry=enquiry,
                description=quick_notes or f"Quick update: {quick_status}",
                status=enquiry.status,  # Keep current status
                call_status=quick_status
            )
            
            # Update enquiry
            enquiry.number_of_followup += 1
            enquiry.last_follow_up_date = today
            
            # Set next follow-up based on status
            if quick_status == 'callback':
                enquiry.next_follow_up_date = today + timedelta(days=1)
            elif quick_status == 'follow_up':
                enquiry.next_follow_up_date = today + timedelta(days=3)
            elif quick_status == 'converted':
                enquiry.conversion = True
                enquiry.next_follow_up_date = None
                enquiry.status = 'completed'
            elif quick_status == 'not_interested':
                enquiry.status = 'rejected'
                enquiry.next_follow_up_date = None
            elif quick_status == 'closed':
                enquiry.status = 'not_required'
                enquiry.next_follow_up_date = None
            else:
                enquiry.next_follow_up_date = today + timedelta(days=2)
            
            enquiry.save()
            messages.success(request, f"Quick update added for {enquiry.name}")
            
        except EnquiryData.DoesNotExist:
            messages.error(request, "Enquiry not found")
        
        return redirect('todays_followups')
    
    context = {
        'todays_followups': todays_followups,
        'overdue_followups': overdue_followups,
        'upcoming_followups': upcoming_followups,
        'total_due': total_due,
        'today_count': today_count,
        'overdue_count': overdue_count,
        'upcoming_count': upcoming_count,
        'today': today,
    }
    
    return render(request, 'enquiries/todays_followups.html', context)


# ... existing views (enquiry_list, enquiry_detail, etc.) ...



def enquiry_list(request):
    """View to list all enquiries with filtering options"""
    enquiries = EnquiryData.objects.all().order_by('-date_created')
    filter_form = EnquiryFilterForm(request.GET or None)
    
    # Apply filters
    if filter_form.is_valid():
        conversion = filter_form.cleaned_data.get('conversion')
        status = filter_form.cleaned_data.get('status')
        search = filter_form.cleaned_data.get('search')
        
        # Filter by conversion status
        if conversion:
            conversion_bool = conversion == 'True'
            enquiries = enquiries.filter(conversion=conversion_bool)
        
        # Filter by status
        if status:
            enquiries = enquiries.filter(status=status)
        
        # Search filter
        if search:
            enquiries = enquiries.filter(
                Q(name__icontains=search) |
                Q(phone_number__icontains=search) |
                Q(email__icontains=search)
            )
    
    # Default filter: show only non-converted enquiries if no filter is applied
    if not request.GET:
        enquiries = enquiries.filter(conversion=False)
    
    # Pagination
    paginator = Paginator(enquiries, 10)  # Show 10 enquiries per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'filter_form': filter_form,
        'total_enquiries': enquiries.count()
    }
    
    return render(request, 'enquiries/enquiry_list.html', context)


def enquiry_detail(request, pk):
    """View to display single enquiry details with all follow-up statuses"""
    enquiry = get_object_or_404(EnquiryData, pk=pk)
    statuses = EnquiryStatus.objects.filter(enquiry=enquiry).order_by('-date_of_status')
    
    context = {
        'enquiry': enquiry,
        'statuses': statuses,
    }
    
    return render(request, 'enquiries/enquiry_detail.html', context)


def enquiry_update(request, pk):
    """View to update enquiry details"""
    enquiry = get_object_or_404(EnquiryData, pk=pk)
    
    if request.method == 'POST':
        form = EnquiryDataForm(request.POST, instance=enquiry)
        if form.is_valid():
            form.save()
            messages.success(request, 'Enquiry updated successfully!')
            return redirect('enquiry_detail', pk=pk)
    else:
        form = EnquiryDataForm(instance=enquiry)
    
    context = {
        'form': form,
        'enquiry': enquiry,
    }
    
    return render(request, 'enquiries/enquiry_update.html', context)


def add_status_update(request, pk):
    """View to add new status update to an enquiry"""
    enquiry = get_object_or_404(EnquiryData, pk=pk)
    
    if request.method == 'POST':
        form = EnquiryStatusForm(request.POST)
        next_followup = request.POST.get('next_followup',None)
        if form.is_valid():
            status = form.save(commit=False)
            status.enquiry = enquiry
            status.save()
            
            # Update enquiry's status and follow-up count
            enquiry.status = status.status
            enquiry.number_of_followup += 1
            enquiry.last_follow_up_date = timezone.now().date()
            
            # Update conversion status if call_status is 'converted'
            if status.call_status == 'converted':
                enquiry.conversion = True
                member = MemberData.objects.create(First_Name = enquiry.name,  Mobile_Number = enquiry.phone_number, Email = enquiry.email, Registration_Date = timezone.now())
                member.save()

            if next_followup:
                enquiry.next_follow_up_date = next_followup
            enquiry.save()
            
            messages.success(request, 'Status update added successfully!')
            return redirect('enquiry_detail', pk=pk)
    else:
        form = EnquiryStatusForm()
    
    context = {
        'form': form,
        'enquiry': enquiry,
    }
    
    return render(request, 'enquiries/add_status_update.html', context)


def enquiry_create(request):
    """View to create new enquiry"""
    if request.method == 'POST':
        form = EnquiryDataForm(request.POST)
        if form.is_valid():
            enquiry = form.save()
            messages.success(request, 'New enquiry created successfully!')
            return redirect('enquiry_detail', pk=enquiry.pk)
    else:
        form = EnquiryDataForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'enquiries/enquiry_create.html', context)