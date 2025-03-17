from django.db import models
from django.contrib.auth.models import AbstractUser
import os
from datetime import datetime

def user_directory_path(instance, filename):
    # Получаем текущую дату и время
    now = datetime.now()
    
    # Расширение файла
    extension = filename.split('.')[-1]
    
    # Формируем новое имя файла: Часы-Минуты-Секунды.расширение
    new_filename = f"{now.hour}-{now.minute}-{now.second}.{extension}"
    
    # Путь будет вида: media/photos/2024/11/Часы-Минуты-Секунды.jpg
    return os.path.join("Photo", str(now.year), str(now.month), new_filename)


class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('user', 'User'),
        ('manager', 'Manager'),
        ('master', 'Master')
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')
    fio = models.CharField(max_length=64, default='No name', blank=True)
    photo = models.ImageField(upload_to=user_directory_path, null=True, blank=True)
    def __str__(self):
        return f"{self.username} ({self.role})"

class Requests(models.Model):
    id = models.AutoField(primary_key=True)
    user_id = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    phone = models.CharField(max_length=255)
    address = models.CharField(max_length=256)
    status = models.CharField(max_length=64, default='Not accepted', blank=True)
    width = models.IntegerField(default=0)
    height = models.IntegerField(default=0)
    window_type = models.CharField(max_length=255, default=None, null=True)
    window_image = models.CharField(max_length=255, default=None, null=True)
    price = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True, blank=True, default=None)

class Details(models.Model):
    id = models.AutoField(primary_key=True)
    request_id = models.ForeignKey(Requests, on_delete=models.CASCADE)
    worker_id = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)
    measurement_date = models.DateField(null=True, blank=True, default=None)
    status = models.CharField(max_length=64, default='Waiting', blank=True)

class Reviews(models.Model):
    id = models.AutoField(primary_key=True)
    user_id = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    request_id = models.ForeignKey(Requests, on_delete=models.SET_NULL, null=True)
    text = models.TextField()
    rating = models.IntegerField(default=0)

class Items(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=256)
    image = models.ImageField(upload_to=user_directory_path, null=True, blank=True)
    characteristics = models.JSONField(blank=True, null=True, default=None)
    category = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True ,default=None)
    count = models.IntegerField(default=1)

class RequestsItems(models.Model):
    id = models.AutoField(primary_key=True)
    detail_id = models.ForeignKey(Details, on_delete=models.SET_NULL, null=True)
    item_id = models.ForeignKey(Items, on_delete=models.SET_NULL, null=True)
    installation_date = models.DateField()
    count = models.IntegerField(default=0)

class Features(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=256)
    description = models.TextField()