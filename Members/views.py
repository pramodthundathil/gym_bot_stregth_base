from django.shortcuts import render, redirect
from .forms import MemberAddForm, SubscriptionAddForm, PaymentForm
from .models import MemberData, Subscription, Payment, AccessToGate, Discounts
from django.contrib import messages
from datetime import datetime, timedelta
from django.utils import timezone
from django.http import HttpResponse
import csv
from django.template.loader import get_template
from xhtml2pdf import pisa
from Index.models import ConfigarationDB
# import requests
import requests
import json
from django.contrib.auth.decorators import login_required
from Index.models import Logo
from Index.decorator import allowed_users



this_month = timezone.now().month
today = timezone.now()
start_date = today + timedelta(days=-5)
end_date = today + timedelta(days=5)
resign_date = today +timedelta(days = -30)

notification_payments = Payment.objects.filter(Payment_Date__gte = start_date,Payment_Date__lte = today,Payment_Date = today )


def ScheduledTask():
    try:
        confdata = ConfigarationDB.objects.get(id=1)
    except ConfigarationDB.DoesNotExist:
        confdata = {
            "JWT_IP": '0',
            "JWT_PORT": "0",
            "Call_Back_IP": '0',
            "Call_Back_Port": "0",
            "Admin_Username": "",
            "Admin_Password": ""
        }

    # Get JWT token on local host Ztehodevice
    url = f'http://http://127.0.0.1:80/jwt-api-token-auth/'
    print(url)
    header1 = {
        'Content-Type': 'application/json'
    }
    token = "nil"
    body = {
        "username": confdata.Admin_Username,
        "password": confdata.Admin_Password
    }
    json_payload = json.dumps(body)

    try:
        response = requests.post(url, headers=header1, data=json_payload)
        if response.status_code == 200:
            print('Request successful!')
            token_dict = response.json()
            token = token_dict['token']
            print(token_dict)
        else:
            print("No connection")
    except requests.RequestException:
        print("No connection........")
    
    urlforapi = 'http://http://127.0.0.1:80/api-token-auth/'
    header2 = {
        'Content-Type': 'application/json',
        'Authorization': f'{token}'
    }
    try:
        tokenresponse = requests.post(urlforapi, headers=header2,data=json_payload)
        if tokenresponse.status_code == 200:
            token_val = tokenresponse.json()
            mytoken = token_val['token']
    except:
        print("No connection...")
        mytoken = 0

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Token {mytoken}'
    }

    end_date = datetime.now()  # Assuming end_date is current datetime, adjust as necessary
    resign_date = datetime.now()  # Assuming resign_date is current datetime, adjust as necessary

    subscrib = Subscription.objects.filter(Subscription_End_Date__lte=end_date)
    subscriptions_to_update = []
    access_to_update = []

    for subscription in subscrib:
        subscription.Payment_Status = False
        subscriptions_to_update.append(subscription)
        subscription.Member.update_active_status()
        try:
            access = AccessToGate.objects.get(Subscription=subscription)
            access.Status = False
            access_to_update.append(access)
        except AccessToGate.DoesNotExist:
            continue

    Subscription.objects.bulk_update(subscriptions_to_update, ['Payment_Status'])
    AccessToGate.objects.bulk_update(access_to_update, ['Status'])

    acc = AccessToGate.objects.all()

    with requests.Session() as session:
        for access in acc:
            accessid = access.Member.Access_Token_Id
            if access.Status is False:
                url = f"http://127.0.0.1:80/personnel/api/resigns/"
                data = {
                    "employee": accessid,
                    "disableatt": True,
                    "resign_type": 1,
                    "resign_date": str(resign_date),
                    "reason": "Payment Pending",
                }
            else:
                url = f"http://127.0.0.1:80/personnel/api/reinstatement/"
                data = {
                    "resigns": [accessid]
                }

            json_payload = json.dumps(data)

            try:
                response = session.patch(url, headers=headers, data=json_payload)
                if response.status_code == 200:
                    print("Succeed...")
                else:
                    print("Failed.....")
            except requests.RequestException:
                print("No connection from resigns")
                break

    print("workinggggg.....")

            

    
    

# member configarations and subscription add on same method 
# one forign key field is prent in subscription Meber forign key, priod forign key, Batch forgin key

from Finance.models import Income, Expence

@login_required(login_url='SignIn')
def Member(request):
    form = MemberAddForm()
    sub_form = SubscriptionAddForm()
    Trainee = MemberData.objects.all().order_by('-id')[:8]
    subscribers = Subscription.objects.all().order_by('-id')[:8]
    notification_payments = Payment.objects.filter(Payment_Date__gte = start_date, Payment_Date__lte = today)

    if request.method == "POST":
        form = MemberAddForm(request.POST, request.FILES)
        sub_form = SubscriptionAddForm(request.POST)
        if form.is_valid() and sub_form.is_valid():
            member = form.save()
            member.Discount = 0
            member.save()
            
            sub_data = sub_form.save()
            start_dat = sub_data.Subscribed_Date
            
            # Calculate end date based on any category
            if sub_data.Period_Of_Subscription.Category == "Month":
                sub_data.Subscription_End_Date = start_dat + timedelta(days=(sub_data.Period_Of_Subscription.Period * 30))
            elif sub_data.Period_Of_Subscription.Category == "Year":
                sub_data.Subscription_End_Date = start_dat + timedelta(days=(sub_data.Period_Of_Subscription.Period * 365))
            elif sub_data.Period_Of_Subscription.Category == "Week":
                sub_data.Subscription_End_Date = start_dat + timedelta(days=(sub_data.Period_Of_Subscription.Period * 7))
            elif sub_data.Period_Of_Subscription.Category == "Day":
                sub_data.Subscription_End_Date = start_dat + timedelta(days=sub_data.Period_Of_Subscription.Period)
            else:
                # Default fallback - set to 30 days if category is unknown
                sub_data.Subscription_End_Date = start_dat + timedelta(days=30)
                
            sub_data.Member = member
            sub_data.save()
            
            # Now we're sure Subscription_End_Date has a value
            access_gate = AccessToGate.objects.create(
                Member=member,
                Subscription=sub_data,
                Validity_Date=sub_data.Subscription_End_Date
            )
            access_gate.save()
            
            messages.success(request, "New Member Was Added Successfully Please Make Payment")
            return redirect("Member")
        else:
            if not form.is_valid():
                messages.error(request, "Entered Personal Data is Not Validated Please try again")
            if not sub_form.is_valid():
                messages.error(request, "Entered Subscription Data is Not Validated Please try again")
            return redirect("Member")
            
    context = {
        "notification_payments": notification_payments,
        "form": form,
        "sub_form": sub_form,
        "Trainee": Trainee,
        "subscribers": subscribers,
        "notificationcount": notification_payments.count()
    }
    return render(request, "members.html", context)

@login_required(login_url='SignIn')
def MembersSingleView(request,pk):
    member = MemberData.objects.get(id = pk)
    try:
        subscription = Subscription.objects.get(Member = member)
    except:
        subscription = None
    try:
        access = AccessToGate.objects.get(Member = member)
    except:
        access = AccessToGate.objects.create(Member = member,Subscription = subscription,Validity_Date = datetime.now()) 
        access.save()
    sub_form = SubscriptionAddForm()
    payments = Payment.objects.filter(Member = member)
    try:
        enrollment_form = member.enrolment_form.all().first()
    except:
        enrollment_form = None

    context = {
        "member":member,
        "subscription":subscription,
        'sub_form':sub_form,
        "access":access,
        "notification_payments":notification_payments,
        "payments":payments,
        "enrollment_form":enrollment_form

    }
    return render(request,"memberssingleview.html",context)

@login_required(login_url='SignIn')
def UpdateMember(request,pk):
    member = MemberData.objects.get(id = pk)
    if request.method == "POST":
        fname = request.POST.get("fname")
        lname = request.POST["lname"]
        email = request.POST["email"]
        phone = request.POST["phone"]
        # dob = request.POST.get("dob")
        address = request.POST["address"]
        medicahistory = request.POST["mhistory"]

        member.First_Name = fname
        member.Last_Name = lname
        # try:
        #     member.Date_Of_Birth = dob
        #     member.save()
        # except:
        member.Mobile_Number = phone
        member.Email = email
        member.Address = address
        member.Medical_History = medicahistory
        member.save()
        messages.success(request,"User Data Updated..")
        return redirect("MembersSingleView",pk)

    return redirect("MembersSingleView",pk)

@login_required(login_url='SignIn')
def ProfilephotoUpdate(request,pk):
    if request.method == "POST":
        file = request.FILES["photo"]
        member = MemberData.objects.get(id = pk)
        member.Photo.delete()
        member.Photo = file
        member.save()
        messages.success(request, "Photo Changed...")
        return redirect("MembersSingleView",pk)
    return redirect("MembersSingleView",pk)

@login_required(login_url='SignIn')
def IdphotoUpdate(request,pk):
    if request.method == "POST":
        file = request.FILES["photo"]
        member = MemberData.objects.get(id = pk)
        member.Id_Upload.delete()
        member.Id_Upload = file
        member.save()
        messages.success(request, "Id Proof updated...")
        return redirect("MembersSingleView",pk)
    return redirect("MembersSingleView",pk)
    

@login_required(login_url='SignIn')
def UpdateAccessToken(request,pk):
    if request.method == "POST":
        newtoken = request.POST['newtkn']
        member = MemberData.objects.get(id=pk)
        member.Access_Token_Id = newtoken
        member.save()
        messages.info(request,"Token Changed")
        return redirect("MembersSingleView",pk)

    return redirect("MembersSingleView",pk)

@login_required(login_url='SignIn')
def DeleteMember(request,pk):
    member = MemberData.objects.get(id=pk)
    member.Photo.delete()
    member.delete()
    messages.error(request,"Member Data Deleted Success")
    return redirect("Member")

@login_required(login_url='SignIn')
def MemberAccess(request):
    return render(request,"memberaccess.html")



@login_required(login_url='SignIn')
def ChangeSubscription(request,pk):
    print("function Started..................")
    sub_form = SubscriptionAddForm()
    member = MemberData.objects.get(id = pk )

    if request.method == "POST":
        sub_form = SubscriptionAddForm(request.POST)
        if sub_form.is_valid():
            member = MemberData.objects.get(id = pk )
         
            subscription = Subscription.objects.filter(Member = member)
            for i in subscription:
                i.delete()

            sub_data = sub_form.save()
            sub_data.Member = member
            start_dat = sub_data.Subscribed_Date
            if sub_data.Period_Of_Subscription.Category == "Day":
                sub_data.Subscription_End_Date = start_dat + timedelta(days=sub_data.Period_Of_Subscription.Period)
            elif sub_data.Period_Of_Subscription.Category == "Week":
                sub_data.Subscription_End_Date = start_dat + timedelta(weeks=sub_data.Period_Of_Subscription.Period)
            elif sub_data.Period_Of_Subscription.Category == "Month":
                sub_data.Subscription_End_Date = start_dat + timedelta(days=sub_data.Period_Of_Subscription.Period * 30)
            elif sub_data.Period_Of_Subscription.Category == "Year":
                sub_data.Subscription_End_Date = start_dat + timedelta(days=sub_data.Period_Of_Subscription.Period * 365)
            sub_data.save()



            access = AccessToGate.objects.filter(Member = member)

            for i in access:
                i.delete()

            access_gate = AccessToGate.objects.create(Member = member,Subscription = sub_data,Validity_Date = sub_data.Subscription_End_Date )
            access_gate.save()

            messages.success(request,"Subscription Changed Success..")
            return redirect(MembersSingleView,pk)
            
        messages.error(request,"Form Is not valid")
        return redirect(MembersSingleView,pk)

    context = {
        "sub_form":sub_form,
        "member":member
    }
    return render(request,'changesubscription.html',context)
        
            
@login_required(login_url='SignIn')
def Payments(request):
    form = PaymentForm()
    pay = Payment.objects.all().order_by("-id")[:8]
    sub_today = Subscription.objects.filter(Subscription_End_Date = today,Payment_Status = False)[:8][::-1]
    sub_past = Subscription.objects.filter(Subscription_End_Date__lte = today,Payment_Status = False)[:8][::-1]
    sub_Upcoming = Subscription.objects.filter(Subscription_End_Date__gte = today,Subscription_End_Date__lte = end_date, Payment_Status = False)[:8][::-1]
    member = MemberData.objects.all()
    
    if request.method == "POST":
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save()
            access = AccessToGate.objects.get(Member = payment.Member)
            sub = Subscription.objects.get(Member = payment.Member)

            payment.Subscription_ID = sub
            payment.Amount = sub.Amount
            payment.Payment_Status = True 
            payment.Access_status = True
            payment.save()
            sub.Payment_Status = True
            sub.save()
            user = payment.Member
            user.Access_status = True
            user.save()
           
            try:
                sub_date = request.POST["sub_extendate"]
                access.Validity_Date = sub_date
                access.save()

            except:
                sub_date = sub.Subscription_End_Date
                access.Validity_Date = sub_date
                access.save()
                
            sub.Subscription_End_Date = sub_date
            sub.save()
            
            if AccessToGate.objects.filter(Validity_Date__gte = today, Member = payment.Member ).exists():
                access.Status = True 
                access.Payment_status = True
            else:
                access.Status = False 
            access.save()
            ScheduledTask()
            messages.success(request,"Payment Updated for member {}".format(user))
            return redirect("Payments")
        else:
            messages.error(request,"Payment Not Updated")
            return redirect("Payments")


    context = {
        "form":form,
        "pay":pay,
        "notification_payments":notification_payments,
        "sub_today":sub_today,
        "sub_past":sub_past,
        "sub_Upcoming":sub_Upcoming,
        "member":member,
    }
    return render(request, "payments.html",context)


# Add this view to your views.py
from django.http import JsonResponse
from django.db.models import Q

def search_members(request):
    search_term = request.GET.get('term', '')
    
    if len(search_term) < 2:
        return JsonResponse([], safe=False)
    
    members = MemberData.objects.filter(
        Q(First_Name__icontains=search_term) | 
        Q(Last_Name__icontains=search_term)
    )
    
    results = []
    for member in members:
        results.append({
            'id': member.id,
            'name': f"{member.First_Name} {member.Last_Name}"
        })
    
    return JsonResponse(results, safe=False)

@login_required(login_url='SignIn')
def AddNewPayment(request):
    if request.method == "POST":
        try:
            mid = request.POST["member"]
            member = MemberData.objects.get(id = mid)
            Sub = Subscription.objects.get(Member = member)

            context = {
                "member":member,
                "sub":Sub,
                "discounted":Sub.Amount - (Sub.Amount*member.Discount)/100
            }
            return render(request,"paymentscreen.html",context)
        except:
            try:
                mid = request.POST["member"]
                messages.error(request, "This member Has no subscription Please add subscription to make Payment ")
                return redirect(ChangeSubscription, pk = member.id)
            except:
                messages.error(request, "Member is not exists")
                return redirect("Payments")
    else:
        messages.info(request, "Please select member to continue...")
        return redirect("Payments")

    
@login_required(login_url='SignIn')
def AddNewPaymentFromMember(request,pk):

    member = MemberData.objects.get(id = pk)
    try:
        Sub = Subscription.objects.get(Member = member)

        context = {
            "member":member,
            "sub":Sub,
            "discounted":Sub.Amount - (Sub.Amount*member.Discount)/100
        }
        return render(request,"paymentscreen.html",context)
    except:
        messages.error(request, "This member Has no subscription Please add subscription to make Payment ")
        return redirect(ChangeSubscription, pk = pk)

        

@login_required(login_url='SignIn')
def PostNewPayment(request,pk):

    if request.method == "POST":

        mode = request.POST["mode"]
        date = request.POST["date"]
        member = MemberData.objects.get(id = pk)
        access = AccessToGate.objects.get(Member = member)
        sub = Subscription.objects.get(Member = member)
        payment = Payment.objects.create(Member = member, Subscription_ID = sub,Mode_of_Payment = mode,Payment_Date = date, Amount = sub.Amount - (sub.Amount*member.Discount)/100 )
        payment.save()

        payment.Payment_Status = True 
        payment.Access_status = True
        payment.save()
        sub.Payment_Status = True
        sub.save()
        user = payment.Member
        user.Access_status = True
        user.save()
        

        try:
            sub_date = request.POST.get("sub_extendate")
            if sub_date:
                access.Validity_Date = sub_date
                access.save()
            
                sub.Subscription_End_Date = sub_date
                sub.save()
            else:
                sub_date = sub.Subscription_End_Date
                access.Validity_Date = sub_date
                access.save()

        except:
            sub_date = sub.Subscription_End_Date
            access.Validity_Date = sub_date
            access.save()
           
        sub.Subscription_End_Date = sub_date
        sub.save()

        try:
             
            amount = request.POST.get("Custome_amount")
            if amount:
                payment.Amount = amount
                balance = float(sub.Amount) - float(amount)
                print(balance,"-------------------------------------------------")
                payment.Payment_Balance = balance
                payment.partial_payment  = True
                payment.Subscription_ID.partial_payment = True
                payment.save()
            
            
        except:
            a = 100
    
            
        if AccessToGate.objects.filter(Validity_Date__gte = today, Member = member ).exists():
            access.Status = True 
            access.Payment_status = True
        else:
            access.Status = False 
        access.save()
        ScheduledTask()
        print(payment.Amount,"------------------------------------")

        income = Income.objects.create(perticulers = f"Payment from {member} by {payment.Mode_of_Payment}",amount = payment.Amount,date = date)
        income.save()

        messages.success(request,"Payment Updated for member: {}".format(user))
        return redirect("Payments")

    return redirect("Payments")

from .models import BalancePayment

def make_balance_payment(request, pk):
    payment = Payment.objects.get(id=pk)
    balance = payment.Payment_Balance
    if request.method == "POST":
        date = request.POST.get("date_on_payment")
        amount = request.POST.get('balance')
        
        # payment.Payment_Balance = 0
        payment.save() 
        balance_bill = BalancePayment.objects.create(payment = payment,Amount = amount,Payment_Date = date)
        balance_bill.save()
        balance_bill.Payment_Date = date
        payment.Payment_Balance -= float(amount)
        if  payment.Payment_Balance > 0:
            payment.Payment_Status = False
        else:
            payment.Payment_Status = True
        payment.save() 
        balance_bill.save()

        income = Income.objects.create(perticulers = f"Payment from {payment.Member} by {payment.Mode_of_Payment}",amount = balance)
        income.save()
        messages.success(request,"Balance Payment Updated for member {}".format(payment.Member))
        return redirect("AllPayments")

@login_required(login_url='SignIn')
def AddPaymentFromMemberTab(request,pk):
    member = MemberData.objects.get(id = pk)
    if request.method == "POST":
        date = request.POST["pay_date"]
        access = AccessToGate.objects.get(Member = member)
        sub = Subscription.objects.get(Member = member)

        payment = Payment.objects.create(Member = member,Payment_Date = date, Subscription_ID = sub,Amount = sub.Amount,Payment_Status = True,Access_status = True )
        payment.save()
        sub.Payment_Status = True
        sub.save()
        user = member
        user.Access_status = True
        user.save()

        try:
            sub_date = request.POST.get("sub_extendate")
            if sub_date:
                access.Validity_Date = sub_date
                access.save()

        except:
            sub_date = sub.Subscription_End_Date
            access.Validity_Date = sub_date
            access.save()

        
            
        sub.Subscription_End_Date = sub_date
        sub.save()
        if AccessToGate.objects.filter(Validity_Date__gte = today, Member = payment.Member ).exists():
            access.Status = True 
            access.Payment_status = True
        else:
            access.Status = False 
        access.save()
        ScheduledTask()

        income = Income.objects.create(perticulers = f"Payment from {member}",amount = payment.Amount,date = date)
        income.save()
        messages.success(request,"Payment Updated for member {}".format(user))
        return redirect("MembersSingleView",pk)

    context ={
        "member":member
    }
    # messages.success(request, "Payment Added")
    return render(request,"paymentaddsingle.html",context)

# creating receipt for payment 

# @login_required(login_url='SignIn')
# def ReceiptGenerate(request,pk):
#     logo = Logo.objects.get(id = 1)
#     payment  = Payment.objects.get(id = pk)
#     member = payment.Member
#     amount  = payment.Amount
#     payid  = pk
#     payment_date = payment.Payment_Date
#     try:
#         sub_start = payment.Subscription_ID.Subscribed_Date
#         sub_end = payment.Subscription_ID.Subscription_End_Date
#         period = payment.Subscription_ID.Period_Of_Subscription
#     except:
#         sub_start = "Null"
#         sub_end = "Null"
#         period = "Null"
#     template_path = "receipt.html"

#     context = {
#        "member":member,
#        "amount":amount,
#        "payid":payid,
#        "payment_date":payment_date,
#        "sub_start":sub_start,
#        "sub_end":sub_end,
#        "period":period,
#        "pk":pk,
#        "logo":logo
#     }
#     response = HttpResponse(content_type = "application/pdf")
#     response['Content-Disposition'] = 'filename=f"payment_receipt_{member}.pdf"'
#     template = get_template(template_path)
#     html = template.render(context)

#     # create PDF
#     pisa_status = pisa.CreatePDF(html, dest = response)
#     if pisa_status.err:
#         return HttpResponse("we are some erros <pre>" + html + '</pre>')
#     return response


def get_balance_receipt(request, pk):
    """
    Generate a professional PDF receipt for a payment.
    Uses WeasyPrint for higher quality PDF generation with better CSS support.
    """
    # Get necessary data
    logo = Logo.objects.get(id=1)
    balance_ = BalancePayment.objects.get(id=pk)
    payment = balance_.payment
    member = payment.Member
    amount = balance_.Amount
    payid = pk
    payment_date = balance_.Payment_Date
    
    try:
        sub_start = payment.Subscription_ID.Subscribed_Date
        sub_end = payment.Subscription_ID.Subscription_End_Date
        period = payment.Subscription_ID.Period_Of_Subscription
    except:
        sub_start = "N/A"
        sub_end = "N/A"
        period = "N/A"
    
    # Generate barcode for receipt
    import barcode
    from barcode.writer import ImageWriter
    import base64
    from io import BytesIO
    
    # Create EAN13 barcode (you can use other formats too)
    ean = barcode.get_barcode_class('code128')
    ean_barcode = ean(f'EMPIRE{payid}', writer=ImageWriter())
    
    # Convert barcode to base64 for embedding in HTML
    buffer = BytesIO()
    ean_barcode.write(buffer)
    buffer.seek(0)
    barcode_image = base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    # Prepare context for template
    context = {
       "member": member,
       "amount": amount,
       "payid": payid,
       "payment_date": payment_date,
       "sub_start": sub_start,
       "sub_end": sub_end,
       "period": period,
       "barcode_image": barcode_image,
       "logo": logo,
       "balance":"balance"
    }
    
    # Render template to HTML
    template_path = "receipt.html"
    template = get_template(template_path)
    html = template.render(context)
    
    # Generate PDF using WeasyPrint for better CSS support
    try:
        from weasyprint import HTML, CSS
        from django.conf import settings
        import os
        
        # Create response object
        response = HttpResponse(content_type="application/pdf")
        response['Content-Disposition'] = f'attachment; filename="payment_receipt_{member}_{payid}.pdf"'
        
        # Generate PDF with WeasyPrint
        base_url = request.build_absolute_uri('/')
        pdf = HTML(string=html, base_url=base_url).write_pdf()
        
        # Write PDF to response
        response.write(pdf)
        return response
        
    except ImportError:
        # Fallback to xhtml2pdf if WeasyPrint is not available
        response = HttpResponse(content_type="application/pdf")
        response['Content-Disposition'] = f'attachment; filename="payment_receipt_{member}_{payid}.pdf"'
        pisa_status = pisa.CreatePDF(html, dest=response)
        
        if pisa_status.err:
            return HttpResponse("We encountered some errors <pre>" + html + '</pre>')
        return response

@login_required(login_url='SignIn')
def ReceiptGenerate(request, pk):
    """
    Generate a professional PDF receipt for a payment.
    Uses WeasyPrint for higher quality PDF generation with better CSS support.
    """
    # Get necessary data
    logo = Logo.objects.get(id=1)
    payment = Payment.objects.get(id=pk)
    member = payment.Member
    amount = payment.Amount
    payid = pk
    payment_date = payment.Payment_Date
    
    try:
        sub_start = payment.Subscription_ID.Subscribed_Date
        sub_end = payment.Subscription_ID.Subscription_End_Date
        period = payment.Subscription_ID.Period_Of_Subscription
    except:
        sub_start = "N/A"
        sub_end = "N/A"
        period = "N/A"
    
    # Generate barcode for receipt
    import barcode
    from barcode.writer import ImageWriter
    import base64
    from io import BytesIO
    
    # Create EAN13 barcode (you can use other formats too)
    ean = barcode.get_barcode_class('code128')
    ean_barcode = ean(f'EMPIRE{payid}', writer=ImageWriter())
    
    # Convert barcode to base64 for embedding in HTML
    buffer = BytesIO()
    ean_barcode.write(buffer)
    buffer.seek(0)
    barcode_image = base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    # Prepare context for template
    context = {
       "member": member,
       "amount": amount,
       "payid": payid,
       "payment_date": payment_date,
       "sub_start": sub_start,
       "sub_end": sub_end,
       "period": period,
       "barcode_image": barcode_image,
       "logo": logo,
       "balance":" "
    }
    
    # Render template to HTML
    template_path = "receipt.html"
    template = get_template(template_path)
    html = template.render(context)
    
    # Generate PDF using WeasyPrint for better CSS support
    try:
        from weasyprint import HTML, CSS
        from django.conf import settings
        import os
        
        # Create response object
        response = HttpResponse(content_type="application/pdf")
        response['Content-Disposition'] = f'attachment; filename="payment_receipt_{member}_{payid}.pdf"'
        
        # Generate PDF with WeasyPrint
        base_url = request.build_absolute_uri('/')
        pdf = HTML(string=html, base_url=base_url).write_pdf()
        
        # Write PDF to response
        response.write(pdf)
        return response
        
    except ImportError:
        # Fallback to xhtml2pdf if WeasyPrint is not available
        response = HttpResponse(content_type="application/pdf")
        response['Content-Disposition'] = f'attachment; filename="payment_receipt_{member}_{payid}.pdf"'
        pisa_status = pisa.CreatePDF(html, dest=response)
        
        if pisa_status.err:
            return HttpResponse("We encountered some errors <pre>" + html + '</pre>')
        return response

@login_required(login_url='SignIn')
def DeletePayment(request,pk):
    Pay = Payment.objects.get(id = pk).delete()
    messages.info(request,"Payment Deleted")
    return redirect("Payments")

@login_required(login_url='SignIn')
def ExtendAccessToGate(request,pk):
    member = MemberData.objects.get(id = pk)
    try:
        subscrib = Subscription.objects.get(Member = member)
    except:
        messages.error(request,"This member has no subscription to extend access please add subscription")
        return redirect(MembersSingleView, pk)
    if request.method == "POST":
        extention = request.POST['exend']
        access = AccessToGate.objects.get(Member = member)
        access.Validity_Date = extention
        access.Status = True
        access.save()
        subscrib.Subscription_End_Date = extention
        subscrib.save()
        messages.success(request, "Access Grandad Till {}".format(extention))
        return redirect(MembersSingleView, pk)
    context = {
        "member":member,
        "notification_payments":notification_payments
    }  
    return render(request,"grandaccessforgate.html",context)

@login_required(login_url='SignIn')
def BlockAccess(request,pk):
    member = MemberData.objects.get(id = pk)
    access = AccessToGate.objects.get(Member = member)
    access.Status = False
    access.save()
    messages.success(request,"Access Status Changed....")
    return redirect(MembersSingleView,pk)

@login_required(login_url='SignIn')
def AllMembers(request):
    members = MemberData.objects.all().order_by('-id')
    return render(request, "allmembers.html",{"member":members})

@login_required(login_url='SignIn')
def AllPayments(request):
    payments = Payment.objects.all()[::-1]
    return render(request,"allpayments.html",{"payments":payments})



@login_required(login_url='SignIn')
def FeePendingMembers(request):
    subscribers = Subscription.objects.all()

    return render(request,"feependingmembers.html",{"subscribers":subscribers})
# Reports generation

@login_required(login_url='SignIn')
def FullMemberReport(request):
    
    date = timezone.now().month
    date_year = timezone.now().year
    response = HttpResponse(content_type = 'text/csv')
    response['Content-Disposition'] = 'attachment; filename=Memberreportfull{}-{}.csv'.format(date,date_year)
    
    member = MemberData.objects.all().order_by("-Date_Added")
    def generate_serial_number():
        current_time = datetime.now()
        serial_number = current_time.strftime("%Y%m%d%H%M%S")
        return serial_number
    TokenU = generate_serial_number()
    writer = csv.writer(response)
    writer.writerow(["Sl No",'First_Name',"Last_Name","Date_Of_Birth","Gender","Mobile_Number","Email","Address","Registration_Date","Date_Added","Access_Token","Subscription","Batch"])
    counter = 0
    for i in member:
        sub = Subscription.objects.get(Member = i)
        batch = sub.Batch
        counter +=1
        writer.writerow([counter,i.First_Name,i.Last_Name,i.Date_Of_Birth,i.Gender,i.Mobile_Number,i.Email,i.Address,i.Registration_Date,i.Date_Added,i.Access_Token_Id,sub,batch])
    response.write('\n')  # Move to the next line after the first row
    response.write(f"Doc Number: {TokenU}")  # Write the unique report number to the next line
    return response


@login_required(login_url='SignIn')
def MonthMemberReport(request):
    
    date = timezone.now().month
    date_year = timezone.now().year
    response = HttpResponse(content_type = 'text/csv')
    response['Content-Disposition'] = 'attachment; filename=Memberreportmonth{}-{}.csv'.format(date,date_year)
    counter = 0
    
    member = MemberData.objects.filter(Date_Added__month = date).order_by("-Date_Added")
    
    writer = csv.writer(response)
    writer.writerow(["Sl No",'First_Name',"Last_Name","Date_Of_Birth","Gender","Mobile_Number","Email","Address","Medical_History","Registration_Date","Date_Added","Access_Token"])
    for i in member:
        counter +=1
        writer.writerow([counter,i.First_Name,i.Last_Name,i.Date_Of_Birth,i.Gender,i.Mobile_Number,i.Email,i.Address,i.Medical_History,i.Registration_Date,i.Date_Added,i.Access_Token_Id])

    def generate_serial_number():
        current_time = datetime.now()
        serial_number = current_time.strftime("%Y%m%d%H%M%S")
        return serial_number
    TokenU = generate_serial_number()

    response.write('\n')  # Move to the next line after the first row
    response.write(f"Doc Number: {TokenU}")  # Write the unique report number to the next line

    return response

@login_required(login_url='SignIn')
def DateWiseMemberReport(request):
    date = timezone.now().month
    date_year = timezone.now().year
    response = HttpResponse(content_type = 'text/csv')
    response['Content-Disposition'] = 'attachment; filename=MemberreportDate{}-{}.csv'.format(date,date_year)
    if request.method == "POST":
        sdate = request.POST["sdate"]
        edate = request.POST["enddate"]
        
    counter = 0
    member = MemberData.objects.filter(Date_Added__gte = sdate,Date_Added__lte = edate ).order_by("-Date_Added")
    
    writer = csv.writer(response)
    writer.writerow(["Slno",'First_Name',"Last_Name","Date_Of_Birth","Gender","Mobile_Number","Email","Address","Medical_History","Registration_Date","Date_Added","Access_Token"])
    for i in member:
        counter +=1
        writer.writerow([counter,i.First_Name,i.Last_Name,i.Date_Of_Birth,i.Gender,i.Mobile_Number,i.Email,i.Address,i.Medical_History,i.Registration_Date,i.Date_Added,i.Access_Token_Id])


    def generate_serial_number():
        current_time = datetime.now()
        serial_number = current_time.strftime("%Y%m%d%H%M%S")
        return serial_number
    TokenU = generate_serial_number()
    response.write('\n')  # Move to the next line after the first row
    response.write(f"Doc Number: {TokenU}")  # Write the unique report number to the next line
    
    return response


@login_required(login_url='SignIn')
def DateWisePaymentReport(request):
    date = timezone.now().month
    date_year = timezone.now().year
    response = HttpResponse(content_type = 'text/csv')
    response['Content-Disposition'] = 'attachment; filename=paymentreportDate{}-{}.csv'.format(date,date_year)
    if request.method == "POST":
        sdate = request.POST["sdate"]
        edate = request.POST["enddate"]
        counter = 0
    
        payment = Payment.objects.filter(Payment_Date__gte = sdate,Payment_Date__lte = edate ).order_by("-Payment_Date")
        
        writer = csv.writer(response)
        writer.writerow(["Slno","Member","Subscription_ID","Amount","Payment_Date"])
        for i in payment:
            counter +=1
            writer.writerow([counter,i.Member,i.Subscription_ID,i.Amount,i.Payment_Date])

        def generate_serial_number():
            current_time = datetime.now()
            serial_number = current_time.strftime("%Y%m%d%H%M%S")
            return serial_number
        TokenU = generate_serial_number()
        response.write('\n')  # Move to the next line after the first row
        response.write(f"Doc Number: {TokenU}") 
        return response
    return HttpResponse("No Valid Fiels")
    

def PaymentReport(request):
    date = timezone.now().month
    date_year = timezone.now().year
    response = HttpResponse(content_type = 'text/csv')
    response['Content-Disposition'] = 'attachment; filename=paymentreportfull{}-{}.csv'.format(date,date_year)
    counter = 0
        
    try:
        payment = Payment.objects.all().order_by("-Payment_Date")
        
        writer = csv.writer(response)
        writer.writerow(["Slno","Member","Subscription_ID","Amount","Payment_Date"])
        for i in payment:
            counter +=1
            writer.writerow([counter,i.Member,i.Subscription_ID,i.Amount,i.Payment_Date])

        
        def generate_serial_number():
            current_time = datetime.now()
            serial_number = current_time.strftime("%Y%m%d%H%M%S")
            return serial_number
        TokenU = generate_serial_number()
        response.write('\n')  # Move to the next line after the first row
        response.write(f"Doc Number: {TokenU}") 

        return response
    except:
        return HttpResponse("No Valid Fiels")
    

@login_required(login_url='SignIn')
def PaymentReportMonth(request):
    date = timezone.now().month
    date_year = timezone.now().year
    response = HttpResponse(content_type = 'text/csv')
    response['Content-Disposition'] = 'attachment; filename=paymentreportmonth{}-{}.csv'.format(date,date_year)
    counter = 0
        
    try:
        payment = Payment.objects.filter(Payment_Date__month = date ).order_by("-Payment_Date")
        
        writer = csv.writer(response)
        writer.writerow(["SlNo","Member","Subscription_ID","Amount","Payment_Date"])
        for i in payment:
            counter += 1
            writer.writerow([counter,i.Member,i.Subscription_ID,i.Amount,i.Payment_Date])

        
        def generate_serial_number():
            current_time = datetime.now()
            serial_number = current_time.strftime("%Y%m%d%H%M%S")
            return serial_number
        TokenU = generate_serial_number()
        response.write('\n')  # Move to the next line after the first row
        response.write(f"Doc Number: {TokenU}") 
        return response
    except:
        return HttpResponse("No Valid Fiels")


@login_required(login_url='SignIn')
def PDFprintFullMemberReport(request):
    date = timezone.now().month
    date_year = timezone.now().year
    member = MemberData.objects.all()
    template_path = "reportpdf_fulldata.html"
    def generate_serial_number():
        current_time = datetime.now()
        serial_number = current_time.strftime("%Y%m%d%H%M%S")
        return serial_number
    TokenU = generate_serial_number()
    context = {
       "member":member,
       "Token":TokenU
    }
    response = HttpResponse(content_type = "application/pdf")
    response['Content-Disposition'] = "filename=Memberreportfull{}-{}.pdf".format(date,date_year)
    template = get_template(template_path)
    html = template.render(context)

    # create PDF
    pisa_status = pisa.CreatePDF(html, dest = response)
    if pisa_status.err:
        return HttpResponse("we are some erros <pre>" + html + '</pre>')
    return response


@login_required(login_url='SignIn')
def PDFprintFullPaymentReport(request):
    date = timezone.now().month
    date_year = timezone.now().year
    payment = Payment.objects.all()
    template_path = "reportpdf_fulldata_payment.html"
    def generate_serial_number():
        current_time = datetime.now()
        serial_number = current_time.strftime("%Y%m%d%H%M%S")
        return serial_number
    TokenU = generate_serial_number()

    context = {
       "payment":payment,
       "Token":TokenU
    }
    response = HttpResponse(content_type = "application/pdf")
    response['Content-Disposition'] = "filename=Paymentreportfull{}-{}.pdf".format(date,date_year)
    template = get_template(template_path)
    html = template.render(context)

    # create PDF
    pisa_status = pisa.CreatePDF(html, dest = response)
    if pisa_status.err:
        return HttpResponse("we are some erros <pre>" + html + '</pre>')
    return response

@login_required(login_url='SignIn')
def PDFmonthMember(request):
    date = timezone.now().month
    date_year = timezone.now().year
    member = MemberData.objects.filter(Date_Added__month = date)
    template_path = "reportPDFmonthMember.html"
    def generate_serial_number():
        current_time = datetime.now()
        serial_number = current_time.strftime("%Y%m%d%H%M%S")
        return serial_number
    TokenU = generate_serial_number()

    context = {
       "member":member,
       "date":date,
       "Token":TokenU
    }
    response = HttpResponse(content_type = "application/pdf")
    response['Content-Disposition'] = "filename=Memberreportmonth{}-{}.pdf".format(date,date_year)
    template = get_template(template_path)
    html = template.render(context)

    # create PDF
    pisa_status = pisa.CreatePDF(html, dest = response)
    if pisa_status.err:
        return HttpResponse("we are some erros <pre>" + html + '</pre>')
    return response


@login_required(login_url='SignIn')
def PDFmonthpayment(request):
    date = timezone.now().month
    date_year = timezone.now().year
    payment = Payment.objects.filter(Payment_Date__month = date)
    template_path = "reportPDFmonthpayment.html"
    def generate_serial_number():
        current_time = datetime.now()
        serial_number = current_time.strftime("%Y%m%d%H%M%S")
        return serial_number
    TokenU = generate_serial_number()

    context = {
       "payment":payment,
       "date":date,
       "Token":TokenU
    }
    response = HttpResponse(content_type = "application/pdf")
    response['Content-Disposition'] = "filename=Paymentreportmonth{}-{}.pdf".format(date,date_year)
    template = get_template(template_path)
    html = template.render(context)

    # create PDF
    pisa_status = pisa.CreatePDF(html, dest = response)
    if pisa_status.err:
        return HttpResponse("we are some erros <pre>" + html + '</pre>')
    return response

    

# Payments and now updates after deploy


@allowed_users(allowed_roles=["admin",])
@login_required(login_url='SignIn')
def EditPayment(request,pk):
    mypay = Payment.objects.get(id = pk)
    sub = mypay.Subscription_ID
    print("sub----------------------------",sub)
    if request.method == "POST":
        mode = request.POST["Mode"]
        Amount = request.POST["amount"]
        date = request.POST["date"]

        mypay.Amount = Amount
        print(mypay.Amount)
        try:
            balance = float(sub.Amount) - float(Amount)
            mypay.Payment_Balance = balance
        except:
            pass
        mypay.Mode_of_Payment = mode 
        mypay.Payment_Date = date
        mypay.save()
        messages.success(request,"Payment Data Updated")
        return redirect("Payments")

    context = {
        "mypay":mypay
    }
    return render(request,"editpayment.html",context)


# discounts to members 
@allowed_users(allowed_roles=["admin",])
@login_required(login_url='SignIn')
def Discount(request):
    member = MemberData.objects.all()
    discount = Discounts.objects.all()
    context = {
        "member":member,
        "discount":discount
    }
    return render(request,"discounts.html",context)


@allowed_users(allowed_roles=["admin",])
@login_required(login_url='SignIn')
def DiscountAllAdd(request):
    if request.method == "POST":
        dateend = request.POST["dateend"]
        disper  = request.POST["disper"]
        member  = MemberData.objects.filter(Special_Discount = False)
        dis = Discounts.objects.create(Discount_Percentage = disper,Till_Date = dateend)
        dis.save()
        member.update(Discount = disper)
        # member.save()
        messages.success(request,"Discount Applied for all members")
        return redirect("Discount")

    return redirect("Discounts")

@allowed_users(allowed_roles=["admin",])
@login_required(login_url='SignIn')
def DiscountSingleAdd(request):
    if request.method == "POST":
        member = MemberData.objects.get(id = request.POST["member"])
        dis = request.POST["disper"]
        member.Discount = dis
        member.Special_Discount = True
        member.save()
        messages.success(request,"Special Discount Applied Members")
        return redirect("Discount")


@allowed_users(allowed_roles=["admin",])
@login_required(login_url='SignIn')
def DeleteAllDiscounts(request,pk):
    Discounts.objects.get(id = pk).delete()
    member = MemberData.objects.filter(Special_Discount = False)
    member.update(Discount = 0)
    # member.save()
    messages.success(request,"Discount Deleted")
    return redirect("Discount")

@allowed_users(allowed_roles=["admin",])
@login_required(login_url='SignIn')
def DeletespecialDiscount(request,pk):
    member = MemberData.objects.get(id = pk)
    member.Discount = 0
    member.Special_Discount = False
    member.save()
    messages.success(request,"Discount Deleted")
    return redirect("Discount")


##########------------------  add new monthly payment details  ------------------#######################
import calendar
from calendar import monthrange

from django.utils import timezone
from datetime import datetime
from collections import defaultdict

@login_required(login_url='SignIn')
def monthwise_calculation_of_payment(request):
    

    return render(request,"payment_status_year.html")



# bulk update 
import pandas as pd
from django.contrib import messages
from django.shortcuts import render, redirect
from django.views import View
from datetime import datetime
from .models import MemberData
from .forms import MemberBulkUploadForm

class MemberBulkUploadView(View):
    template_name = 'bulk_upload.html'

    def get(self, request):
        form = MemberBulkUploadForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = MemberBulkUploadForm(request.POST, request.FILES)
        if form.is_valid():
            excel_file = request.FILES['excel_file']
            
            # Check if file is Excel
            if not excel_file.name.endswith(('.xlsx', '.xls')):
                messages.error(request, 'Please upload a valid Excel file (.xlsx or .xls)')
                return render(request, self.template_name, {'form': form})
            
            try:
                # Read Excel file
                df = pd.read_excel(excel_file)
                
                # Convert DataFrame column names to match model field names
                df.columns = [col.strip().replace(' ', '_') for col in df.columns]
                
                # Track results
                success_count = 0
                error_records = []
                
                # Process each row
                for index, row in df.iterrows():
                    # Convert row to dict and handle NaN values
                    data = {}
                    for col in df.columns:
                        if pd.isna(row[col]):
                            data[col] = None
                        else:
                            data[col] = row[col]
                    
                    # Validate mandatory fields
                    mandatory_fields = ['First_Name', 'Mobile_Number', 'Registration_Date']
                    missing_fields = [field for field in mandatory_fields if field not in data or data[field] is None]
                    
                    if missing_fields:
                        row_number = index + 2  # +2 for 0-indexing and header row
                        error_records.append(f"Row {row_number}: Missing mandatory fields: {', '.join(missing_fields)}")
                        continue
                    
                    try:
                        # Handle date fields
                        if 'Date_Of_Birth' in data and data['Date_Of_Birth'] is not None:
                            if isinstance(data['Date_Of_Birth'], str):
                                try:
                                    data['Date_Of_Birth'] = datetime.strptime(data['Date_Of_Birth'], '%Y-%m-%d').date()
                                except ValueError:
                                    # Try another common format
                                    try:
                                        data['Date_Of_Birth'] = datetime.strptime(data['Date_Of_Birth'], '%d/%m/%Y').date()
                                    except ValueError:
                                        error_records.append(f"Row {index + 2}: Invalid date format for Date_Of_Birth")
                                        continue
                                        
                        if 'Registration_Date' in data and data['Registration_Date'] is not None:
                            if isinstance(data['Registration_Date'], str):
                                try:
                                    data['Registration_Date'] = datetime.strptime(data['Registration_Date'], '%Y-%m-%d').date()
                                except ValueError:
                                    # Try another common format
                                    try:
                                        data['Registration_Date'] = datetime.strptime(data['Registration_Date'], '%d/%m/%Y').date()
                                    except ValueError:
                                        error_records.append(f"Row {index + 2}: Invalid date format for Registration_Date")
                                        continue
                        
                        # Create member
                        member = MemberData(
                            First_Name=data.get('First_Name'),
                            Last_Name=data.get('Last_Name'),
                            Date_Of_Birth=data.get('Date_Of_Birth'),
                            Gender=data.get('Gender', 'Male'),
                            Mobile_Number=data.get('Mobile_Number'),
                            Discount=data.get('Discount'),
                            Special_Discount=bool(data.get('Special_Discount', False)),
                            Email=data.get('Email'),
                            Address=data.get('Address'),
                            Medical_History=data.get('Medical_History'),
                            Registration_Date=data.get('Registration_Date'),
                            Active_status=bool(data.get('Active_status', True)),
                            Access_status=bool(data.get('Access_status', False)),
                            Access_Token_Id=data.get('Access_Token_Id')
                        )
                        member.save()
                        success_count += 1
                    
                    except Exception as e:
                        error_records.append(f"Row {index + 2}: {str(e)}")
                
                # Show results
                if success_count > 0:
                    messages.success(request, f"Successfully imported {success_count} members")
                
                if error_records:
                    for error in error_records:
                        messages.warning(request, error)
                
                return redirect('Member')  # Redirect to member list view
            
            except Exception as e:
                messages.error(request, f"Error processing file: {str(e)}")
        
        return render(request, self.template_name, {'form': form})



# new reports 


# views.py
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.db.models import Q
from django.template.loader import render_to_string
import csv
from io import StringIO
from .models import MemberData, Subscription

def unpaid_members_report(request):
    """
    Display members with unpaid subscriptions
    """
    # Get members who have at least one unpaid subscription
    unpaid_members = MemberData.objects.filter(
        Member_subscription__Payment_Status=False
    ).distinct().select_related().prefetch_related('Member_subscription')
    
    # Add subscription details to each member
    members_data = []
    for member in unpaid_members:
        unpaid_subscriptions = member.Member_subscription.filter(Payment_Status=False)
        total_unpaid_amount = sum(sub.Amount for sub in unpaid_subscriptions)
        
        members_data.append({
            'member': member,
            'unpaid_subscriptions': unpaid_subscriptions,
            'total_unpaid_amount': total_unpaid_amount,
            'unpaid_count': unpaid_subscriptions.count()
        })
    
    context = {
        'members_data': members_data,
        'total_members': len(members_data),
        'total_unpaid_amount': sum(data['total_unpaid_amount'] for data in members_data)
    }
    
    return render(request, 'unpaid_members_report.html', context)

def member_detail_ajax(request, member_id):
    """
    Get detailed member information via AJAX
    """
    try:
        member = MemberData.objects.get(id=member_id)
        unpaid_subscriptions = member.Member_subscription.filter(Payment_Status=False)
        all_subscriptions = member.Member_subscription.all()
        
        data = {
            'success': True,
            'member': {
                'id': member.id,
                'first_name': member.First_Name,
                'last_name': member.Last_Name or '',
                'mobile_number': member.Mobile_Number,
                'email': member.Email or '',
                'address': member.Address or '',
                'registration_date': member.Registration_Date.strftime('%Y-%m-%d') if member.Registration_Date else '',
                'active_status': member.Active_status,
                'access_status': member.Access_status,
            },
            'unpaid_subscriptions': [
                {
                    'id': sub.id,
                    'type': str(sub.Type_Of_Subscription),
                    'period': str(sub.Period_Of_Subscription),
                    'amount': sub.Amount,
                    'subscribed_date': sub.Subscribed_Date.strftime('%Y-%m-%d'),
                    'end_date': sub.Subscription_End_Date.strftime('%Y-%m-%d') if sub.Subscription_End_Date else '',
                    'batch': str(sub.Batch) if sub.Batch else '',
                    'partial_payment': sub.partial_payment
                }
                for sub in unpaid_subscriptions
            ],
            'total_unpaid': sum(sub.Amount for sub in unpaid_subscriptions),
            'total_subscriptions': all_subscriptions.count(),
            'paid_subscriptions': all_subscriptions.filter(Payment_Status=True).count()
        }
        
        return JsonResponse(data)
    
    except MemberData.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Member not found'})

def export_unpaid_members_csv(request):
    """
    Export unpaid members report to CSV
    """
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="unpaid_members_report.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Member ID', 'First Name', 'Last Name', 'Mobile Number', 'Email',
        'Total Unpaid Amount', 'Unpaid Subscriptions Count', 'Registration Date',
        'Active Status', 'Access Status'
    ])
    
    unpaid_members = MemberData.objects.filter(
        Member_subscription__Payment_Status=False
    ).distinct()
    
    for member in unpaid_members:
        unpaid_subscriptions = member.Member_subscription.filter(Payment_Status=False)
        total_unpaid = sum(sub.Amount for sub in unpaid_subscriptions)
        
        writer.writerow([
            member.id,
            member.First_Name,
            member.Last_Name or '',
            member.Mobile_Number,
            member.Email or '',
            total_unpaid,
            unpaid_subscriptions.count(),
            member.Registration_Date.strftime('%Y-%m-%d') if member.Registration_Date else '',
            'Active' if member.Active_status else 'Inactive',
            'Has Access' if member.Access_status else 'No Access'
        ])
    
    return response

def update_member_status(request, member_id):
    """
    Update member active status and payment status
    """
    if request.method == 'POST':
        try:
            member = MemberData.objects.get(id=member_id)
            action = request.POST.get('action')
            
            if action == 'update_status':
                member.update_active_status()
                return JsonResponse({
                    'success': True, 
                    'message': 'Member status updated successfully',
                    'new_status': member.Active_status
                })
            
            elif action == 'mark_paid':
                subscription_id = request.POST.get('subscription_id')
                if subscription_id:
                    subscription = Subscription.objects.get(id=subscription_id, Member=member)
                    subscription.Payment_Status = True
                    subscription.save()
                    member.update_active_status()  # Update member status after payment
                    
                    return JsonResponse({
                        'success': True,
                        'message': 'Subscription marked as paid',
                        'member_status': member.Active_status
                    })
            
            return JsonResponse({'success': False, 'error': 'Invalid action'})
            
        except (MemberData.DoesNotExist, Subscription.DoesNotExist):
            return JsonResponse({'success': False, 'error': 'Record not found'})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})



# new update for strgethbase gym membershipforms and others 


from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.urls import reverse
from .models import GymMembership, TermsAndConditions
from .forms import GymMembershipForm
import json
import base64
from datetime import datetime
from django.core.mail import send_mail
from django.conf import settings

def enrollment_form(request):
    """Display the gym membership enrollment form"""
    if request.method == 'POST':
        form = GymMembershipForm(request.POST, request.FILES)
        if form.is_valid():
            membership = form.save(commit=False)
            
            # Set the latest terms version
            latest_terms = TermsAndConditions.objects.filter(is_active=True).first()
            if latest_terms:
                membership.terms_version = latest_terms
            
            membership.save()
            
            # Send confirmation email (optional)
            try:
                send_confirmation_email(membership)
            except:
                pass  # Email sending is optional
            
            messages.success(request, f'Enrollment successful! Your unique ID is: {membership.unique_link}')
            return redirect('enrollment_success', unique_link=membership.unique_link)
    else:
        form = GymMembershipForm()
    
    # Get latest terms and conditions
    terms = TermsAndConditions.objects.filter(is_active=True).first()
    
    context = {
        'form': form,
        'terms': terms,
    }
    return render(request, 'gym/enrollment_form.html', context)

def enrollment_success(request, unique_link):
    """Display enrollment success page"""
    membership = get_object_or_404(GymMembership, unique_link=unique_link)
    return render(request, 'gym/enrollment_success.html', {'membership': membership})

def membership_detail(request, unique_link):
    """Display membership details"""
    membership = get_object_or_404(GymMembership, unique_link=unique_link)
    return render(request, 'gym/membership_detail.html', {'membership': membership})


def membership_detail_admin(request, unique_link):
    """Display membership details"""
    membership = get_object_or_404(GymMembership, unique_link=unique_link)
    return render(request, 'gym/membership_detail_admin.html', {'membership': membership})

def membership_detail_delete(request,pk):
    member_ship = get_object_or_404(GymMembership, id = pk)
    member_ship.delete()
    messages.success(request,"membership entrolment deleted")
    return redirect(new_enrolment) 

@csrf_exempt
def save_signature(request):
    """Save digital signature via AJAX"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            unique_link = data.get('unique_link')
            signature_data = data.get('signature')
            
            if not unique_link or not signature_data:
                return JsonResponse({'success': False, 'error': 'Missing data'})
            
            membership = GymMembership.objects.get(unique_link=unique_link)
            membership.digital_signature = signature_data
            membership.signature_timestamp = datetime.now()
            membership.save()
            
            return JsonResponse({'success': True})
        except GymMembership.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Membership not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

def terms_and_conditions(request):
    """Display terms and conditions"""
    terms = get_object_or_404(TermsAndConditions, is_active=True)
    return render(request, 'gym/terms_and_conditions.html', {'terms': terms})


def send_confirmation_email(membership):
    """Send confirmation email to member"""
    subject = 'Gym Membership Enrollment Confirmation'
    message = f"""
    Dear {membership.full_name},
    
    Thank you for enrolling at Strength Base Gym!
    
    Your enrollment details:
    - Unique ID: {membership.unique_link}
    - Plan: {membership.get_plan_chosen_display()}
    - Email: {membership.email_id}
    
    You can view your membership details at: {settings.SITE_URL}{membership.get_absolute_url()}
    
    Welcome to Strength Base Gym!
    
    Best regards,
    Strength Base Gym Team
    """
    
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [membership.email_id],
        fail_silently=False,
    )

# entrollment status and all 

@login_required(login_url='SignIn')
def new_enrolment(request):
    enrolment_data = GymMembership.objects.filter(is_member = False)
    context = {
        "enrolment_data": enrolment_data
    }
    return render(request,"new_entrolments.html",context)


@login_required(login_url='SignIn')
def convert_member_form_enrolment(request, pk):
    enroll = get_object_or_404(GymMembership, id = pk)
    member = enroll.convert_to_member()
    enroll.save()
  
    return redirect("MembersSingleView", pk = member.id)


def enrollment_form_existing_member(request, pk):
    """Display the gym membership enrollment form for existing member"""
    member = get_object_or_404(MemberData, id=pk)
    
    if request.method == 'POST':
        form = GymMembershipForm(request.POST, request.FILES)
        if form.is_valid():
            membership = form.save(commit=False)
            
            # Set the latest terms version
            latest_terms = TermsAndConditions.objects.filter(is_active=True).first()
            if latest_terms:
                membership.terms_version = latest_terms
            
            membership.member = member
            membership.is_member = True
            membership.save()
            
            # Send confirmation email (optional)
            try:
                send_confirmation_email(membership)
            except:
                pass  # Email sending is optional
            
            messages.success(request, f'Enrollment successful! Your unique ID is: {membership.unique_link}')
            return redirect('enrollment_success', unique_link=membership.unique_link)
    else:
        # Pre-populate form with existing member data
        initial_data = {
            'full_name': f"{member.First_Name} {member.Last_Name or ''}".strip(),
            'date_of_birth': member.Date_Of_Birth,
            'gender': member.Gender.lower() if member.Gender else None,  # Convert to lowercase to match form choices
            'mobile_number': member.Mobile_Number,
            'email_id': member.Email,
            'address': member.Address,
            'medical_condition_details': member.Medical_History,
        }
        
        # Calculate age if date of birth is available
        if member.Date_Of_Birth:
            from datetime import date
            today = date.today()
            age = today.year - member.Date_Of_Birth.year - ((today.month, today.day) < (member.Date_Of_Birth.month, member.Date_Of_Birth.day))
            initial_data['age'] = age
        
        # Create form with initial data
        form = GymMembershipForm(initial=initial_data)
    
    # Get latest terms and conditions
    terms = TermsAndConditions.objects.filter(is_active=True).first()
    
    context = {
        'form': form,
        'terms': terms,
        'member': member
    }
    return render(request, 'gym/enrollment_form.html', context)
