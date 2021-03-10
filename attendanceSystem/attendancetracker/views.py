from django.http import HttpRequest
from django.shortcuts import render, redirect
from .models import AttendanceTracker
from datetime import datetime, date, timedelta
from django.contrib.auth.models import User
from django.contrib.auth import logout
from .models import AttendanceTracker
from django.http import JsonResponse
from django.db.models import Count
from calendar import monthrange
# Create your views here.


def home(request):
    if request.user.is_authenticated:
        employee = request.user
        if User.objects.filter(username=employee, is_superuser=1).count() == 1:
            return render(request, 'admin/dashboard.html')
        else:
            if AttendanceTracker.objects.filter(user=employee,
                                                logout_time=None, working_hours_per_day=None).count() == 0:
                entry = AttendanceTracker(user=employee, current_date=date.today(),
                                          login_time=datetime.now().time(),)
                entry.save()
            name = User.objects.get(username=employee)
            query_res = AttendanceTracker.objects.filter(user=employee).exclude(current_date=date.today())
            hrs = 0
            minute = 0
            sec = 0
            for i in query_res:
                working_hours = i.working_hours_per_day
                h = working_hours.strftime("%H")
                m = working_hours.strftime("%M")
                s = working_hours.strftime("%S")
                hrs = hrs + int(h)
                minute = minute + int(m)
                sec = sec + int(s)

            minutes = (hrs * 60) + (sec % 60) + minute

            month = datetime.now()
            current_month = month.strftime("%m")
            last_date = monthrange(2021, int(current_month))[1]
            working_days = AttendanceTracker.objects.filter(user=employee,
                current_date__range=["2021-" + current_month + "-01", "2021-" + current_month + "-" + str(last_date)]).\
                count()

            return render(request, 'registration/logout.html', {
                'minutes': minutes,
                'working_days': working_days,
                'absent_days': last_date-working_days,
                'username': name.username
            })

    else:
        return redirect('login')


def list_of_employees(request):
    current_date_users = AttendanceTracker.objects.filter(current_date=date.today())

    current_date_users_list = list()
    for i in current_date_users:
        current_date_users_list.append(i.user)

    total_employees = User.objects.filter(is_superuser=0)
    employee_list = list()

    for i in total_employees:
        temp = list()
        if i in current_date_users_list:
            temp.append(i.username)
            temp.append("Present")
            employee = AttendanceTracker.objects.filter(user=i, current_date=date.today())
            total_working_hours = timedelta(days=0, seconds=0, microseconds=0, milliseconds=0, minutes=0, hours=0, weeks=0)
            for j in employee:
                if j.logout_time:
                    working_hours = datetime.combine(date.today(), j.logout_time) - datetime.combine(date.today(),
                                                                                                     j.login_time)
                else:
                    working_hours = datetime.combine(date.today(), datetime.now().time()) - \
                                datetime.combine(date.today(), j.login_time)
                total_working_hours = total_working_hours + working_hours
            temp.append(total_working_hours)
        else:
            temp.append(i.username)
            temp.append("Absent")
            temp.append("-")
        employee_list.append(temp)
    return render(request, "admin/list_of_employees.html", {'employee_list': employee_list})


def employee_monthly_report(request):
    return render(request, 'admin/monthly_report.html')


def monthly_report(request):
    total_employees = User.objects.filter(is_superuser=0)
    employee_name = []
    employee_working_minutes = []
    month = datetime.now()
    current_month = month.strftime("%m")
    last_date = monthrange(2021, int(current_month))[1]

    for employee in total_employees:
        employee_name.append(employee.username)
        query_res = AttendanceTracker.objects.filter(
            user=employee.pk, current_date__range=["2021-"+current_month+"-01",
                                                   "2021-"+current_month+"-"+str(last_date)])
        hrs = 0
        minute = 0
        sec = 0
        for i in query_res:
            if i.working_hours_per_day:
                working_hours = i.working_hours_per_day
                h = working_hours.strftime("%H")
                m = working_hours.strftime("%M")
                s = working_hours.strftime("%S")
                hrs = hrs+int(h)
                minute = minute+int(m)
                sec = sec+int(s)
        minutes = (hrs*60)+(sec / 60)+minute
        employee_working_minutes.append(minutes)

    chart = {
        'chart': {'type': 'column'},
        'title': {'text': ' Total working minutes of Employee for current month'},
        'xAxis': {'categories': employee_name},
        'series': [{
            'name': 'Total working minutes',
            'data': employee_working_minutes
        }]
    }
    return JsonResponse(chart)


def employee_attendance(request):
    return render(request, 'admin/monthly_attendance.html')


def attendance(request):
    employee_name = []
    present_days = []
    absent_days = []
    month = datetime.now()
    current_month = month.strftime("%m")
    last_date = monthrange(2021, int(current_month))[1]
    '''total_employees = AttendanceTracker.objects.values('user__username', 'current_date').filter(
        current_date__range=["2021-"+current_month+"-01", "2021-"+current_month+"-"+str(last_date)]).\
        annotate(Count('user')).order_by()
    total_employees1 = AttendanceTracker.objects.filter(
        current_date__range=["2021-"+current_month+"-01", "2021-"+current_month+"-"+str(last_date)]).\
        values('user__username').annotate(Count('user'))'''
    total_employees = AttendanceTracker.objects.values('user__username').filter(
        current_date__range=["2021-"+current_month+"-01", "2021-"+current_month+"-"+str(last_date)]).\
        annotate(Count('user')).order_by('user__username')
    print(total_employees)
    for i in total_employees:
        employee_name.append(i['user__username'])
        present_days.append(i['user__count'])
        absent_days.append(last_date-i['user__count'])
    chart = {
        'chart': {'type': 'column'},
        'title': {'text': ' Graphical representation of Present-Absent Days'},
        'xAxis': {'categories': employee_name},
        'series': [{
            'name': 'Present days',
            'data': present_days
        }, {
            'name': 'Absent Days',
            'data': absent_days
        }
        ]
    }
    return JsonResponse(chart)


def home_exit(request, employee):
    if User.objects.filter(pk=employee, is_superuser=1).count() == 1:
        pass
    else:
        employee_id = User.objects.get(pk=employee).pk
        AttendanceTracker.objects.filter(user=employee_id, current_date=date.today(), logout_time=None).update(
            logout_time=datetime.now().time())
        employee = AttendanceTracker.objects.get(user=employee_id, current_date=date.today(), working_hours_per_day=None)
        working_hours = datetime.combine(date.today(), employee.logout_time)-datetime.combine(date.today(),
                                                                                              employee.login_time)
        working_hours = datetime.strptime(str(working_hours), '%H:%M:%S.%f')
        AttendanceTracker.objects.filter(user=employee_id, current_date=date.today(), working_hours_per_day=None).\
            update(working_hours_per_day=working_hours)
    logout(request)
    return redirect('login')


