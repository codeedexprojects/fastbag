from django.db import models

# Create your models here.
from django.db import models

# Gender choices
GENDER_CHOICES = [
    ('M', 'Male'),
    ('F', 'Female'),
    ('O', 'Other'),
]

class DeliveryBoy(models.Model):
    name = models.CharField(max_length=255)
    mobile_number = models.CharField(max_length=15, unique=True)
    email = models.EmailField(max_length=255, unique=True, blank=True, null=True)
    password = models.CharField(max_length=128)
    photo = models.ImageField(upload_to='delivery_boys/', blank=True, null=True)
    address = models.TextField(blank=True, null=True)    
    vehicle_type = models.CharField(max_length=50, blank=True, null=True)
    vehicle_number = models.CharField(max_length=50, unique=True, blank=True, null=True)    
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True, null=True)
    dob = models.DateField(null=True, blank=True)    
    is_active = models.BooleanField(default=True)    
    aadhar_card_image = models.ImageField(upload_to='delivery_boys/aadhar_cards/', blank=True, null=True)
    driving_license_image = models.ImageField(upload_to='delivery_boys/driving_licenses/', blank=True, null=True)    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    @property
    def age(self):
        from datetime import date
        if self.dob:
            today = date.today()
            age = today.year - self.dob.year - ((today.month, today.day) < (self.dob.month, self.dob.day))
            return age
        return None
