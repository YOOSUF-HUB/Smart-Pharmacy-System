from django.contrib import messages
from django.shortcuts import render , redirect
from crudApp.models import Student
from crudApp.forms import StudentForm
# Create your views here.

def student_view(request):
    student = Student.objects.all()
    return render(request , 'crudApp/viewStudent.html' , {'student':student})


def create_student(request):
    if request.method == 'POST':
        form = StudentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Student added successfully!')
            return redirect('student_view')
    else:
        form = StudentForm()
    
    return render(request , 'crudApp/createStudent.html' , {'form':form})

def delete_student(request , id):
    student = Student.objects.get(id = id)
    student.delete()
    return redirect('student_view')

def update_student(request , id):
    student = Student.objects.get(id = id)
    if request.method == 'POST':
        student.sname = request.POST['sname']
        student.sage = request.POST['sage']
        student.sdob = request.POST['sdob']
        student.sclass = request.POST['sclass']
        student.saddress = request.POST['saddress']
        student.save()
        return redirect('student_view')  
    return render(request , 'crudApp/updateStudent.html' , {'student':student})

def home(request):
    return render(request, 'crudApp/home.html')
