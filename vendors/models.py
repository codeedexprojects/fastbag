from django.db import models
from datetime import datetime
from django.contrib.auth.hashers import make_password
import uuid
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from rest_framework.permissions import BasePermission
from django.utils import timezone


#Admin
class StoreType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True, null=True)


    def __str__(self):
        return self.name
    

class  Vendor(models.Model):
    store_id = models.CharField(max_length=255, unique=True, blank=True, editable=False)
    owner_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    business_name = models.CharField(max_length=255)
    business_location = models.CharField(max_length=100, null=True, blank=True)
    business_landmark = models.CharField(max_length=100, null=True, blank=True)
    contact_number = models.CharField(max_length=15, unique=True)
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)
    store_logo = models.ImageField(upload_to='store_logos/')
    license = models.ImageField(upload_to='license')
    display_image = models.ImageField(upload_to='display_image', null=True, blank=True)
    store_description = models.TextField()
    fssai_no = models.CharField(max_length=100, null=True, blank=True)
    fssai_certificate = models.ImageField(upload_to='fssai_certificate', null=True, blank=True)
    store_type = models.ForeignKey(StoreType, on_delete=models.SET_NULL, null=True, blank=True)
    otp = models.CharField(max_length=4, blank=True, null=True) 
    opening_time = models.TimeField(null=True, blank=True)
    closing_time = models.TimeField(null=True, blank=True) 
    is_active = models.BooleanField(default=True)
    is_approved = models.BooleanField(default=False)
    is_restaurent = models.BooleanField(default=False)
    is_Grocery = models.BooleanField(default=False)
    alternate_email = models.EmailField(null=True, blank=True, unique=True)
    otp_expiry = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    since = models.CharField(max_length=30 , null=True,blank=True)
    is_pending_update_approval = models.BooleanField(default=False)  # Tracks pending approval for updates
    pending_fssai_certificate = models.ImageField(upload_to='fssai_certificate_pending', null=True, blank=True)
    pending_license = models.ImageField(upload_to='license_pending', null=True, blank=True)
    pending_contact_number = models.CharField(max_length=15, null=True, blank=True)
    is_vendor = models.BooleanField(default=True)  
    is_staff = models.BooleanField(default=False) 
    is_favourite = models.BooleanField(default=False)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)  
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)  
    is_closed = models.BooleanField(default=False) 

    def __str__(self):
        return self.business_name

    def save(self, *args, **kwargs):
        if self.is_pending_update_approval:
            if self.pending_contact_number:
                self.contact_number = self.pending_contact_number
                self.pending_contact_number = None
            if self.pending_fssai_certificate:
                self.fssai_certificate = self.pending_fssai_certificate
                self.pending_fssai_certificate = None
            if self.pending_license:
                self.license = self.pending_license
                self.pending_license = None
            self.is_pending_update_approval = False

        if not self.store_id:
            self.store_id = 'STR' + str(uuid.uuid4().hex[:4].upper())

        super().save(*args, **kwargs)



    def save(self, *args, **kwargs):
        if not self.store_id:
            self.store_id = 'STR' + str(uuid.uuid4().hex[:4].upper())
        
        super().save(*args, **kwargs)

    def get_opening_time_str(self):
        if self.opening_time:
            return self.opening_time.strftime("%I:%M %p") 
        return None

    def get_closing_time_str(self):
        if self.closing_time:
            return self.closing_time.strftime("%I:%M %p")  
        return None
    
    @property
    def is_authenticated(self):
        return True

    @property
    def is_fully_active(self):
        return self.is_active and self.is_approved
    
    def save(self, *args, **kwargs):
        if not self.store_id:
            self.store_id = 'STR' + str(uuid.uuid4().hex[:4].upper())

        if self.closing_time:
            now = timezone.localtime().time()
            if now > self.closing_time:
                self.is_closed = True

        super().save(*args, **kwargs)

    @property
    def is_closed_now(self):
        now = timezone.localtime().time()
        if self.opening_time and self.closing_time:
            return not (self.opening_time <= now <= self.closing_time)
        elif self.closing_time:
            return now > self.closing_time
        return False
        
class Category(models.Model):
    name = models.CharField(max_length=255, unique=True) 
    store_type = models.ForeignKey(StoreType,on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    category_image = models.ImageField(upload_to='category',null=True,blank=True)

    def __str__(self):
        return self.name
    
class SubCategory(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='subcategories')
    name = models.CharField(max_length=255)
    sub_category_image = models.ImageField(upload_to='subcategories/', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('category', 'name')
        verbose_name = 'Sub Category'
        verbose_name_plural = 'Sub Categories'

    def __str__(self):
        return f"{self.name} - {self.category.name}"

class SubCategoryRequest(models.Model):
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='subcategory_requests')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='subcategory_requests')
    name = models.CharField(max_length=255)
    sub_category_image = models.ImageField(upload_to='subcategory_requests/', null=True, blank=True)
    status_choices = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]
    status = models.CharField(max_length=10, choices=status_choices, default='PENDING')
    admin_remark = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('category', 'name')

    def __str__(self):
        return f"{self.name} (by {self.vendor.business_name}) - {self.status}"
    
