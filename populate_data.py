import os
import django
from faker import Faker
import random

# Configure Django settings
# The project name is 'crudDemo' as seen in your folder structure
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crudDemo.settings') 
django.setup()

from crudApp.models import Student # This import is correct, as crudApp is your app

fake = Faker()

def create_fake_students(num_students):
    for _ in range(num_students):
        sno = fake.unique.random_int(min=1000, max=99999) 
        sname = fake.name()
        sclass = random.randint(1, 12) 
        saddress = fake.address()[:100]

        Student.objects.create(
            sno=sno,
            sname=sname,
            sclass=sclass,
            saddress=saddress
        )
    print(f"Created {num_students} fake students successfully!")

if __name__ == '__main__':
    num_students_to_create = 20 
    create_fake_students(num_students_to_create)