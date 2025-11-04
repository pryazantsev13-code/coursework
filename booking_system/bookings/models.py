from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название категории")
    description = models.TextField(blank=True, verbose_name="Описание")
    
    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"
    
    def __str__(self):
        return self.name

class Service(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name="Категория")
    name = models.CharField(max_length=100, verbose_name="Название услуги")
    description = models.TextField(verbose_name="Описание")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена")
    duration = models.IntegerField(default=60, verbose_name="Длительность (минуты)")
    
    class Meta:
        verbose_name = "Услуга"
        verbose_name_plural = "Услуги"
    
    def average_rating(self):
        """Средний рейтинг услуги"""
        reviews = Review.objects.filter(booking__service=self)
        if reviews.exists():
            return round(reviews.aggregate(models.Avg('rating'))['rating__avg'], 1)
        return 0
    
    def review_count(self):
        """Количество отзывов"""
        return Review.objects.filter(booking__service=self).count()
    
    def __str__(self):
        return f"{self.category.name} - {self.name}"

class TimeSlot(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE, verbose_name="Услуга")
    date = models.DateField(verbose_name="Дата")
    start_time = models.TimeField(verbose_name="Время начала")
    end_time = models.TimeField(verbose_name="Время окончания")
    is_available = models.BooleanField(default=True, verbose_name="Доступно")
    is_blocked = models.BooleanField(default=False, verbose_name="Заблокировано")
    block_reason = models.TextField(blank=True, verbose_name="Причина блокировки")  # Добавляем поле
    blocked_at = models.DateTimeField(null=True, blank=True, verbose_name="Когда заблокировано")  # Добавляем поле
    
    class Meta:
        verbose_name = "Временной слот"
        verbose_name_plural = "Временные слоты"
        ordering = ['date', 'start_time']
    
    def __str__(self):
        return f"{self.service.name} - {self.date} {self.start_time}-{self.end_time}"

class Booking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Ожидает подтверждения'),
        ('confirmed', 'Подтверждено'),
        ('cancelled', 'Отменено'),
        ('completed', 'Завершено'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    service = models.ForeignKey(Service, on_delete=models.CASCADE, verbose_name="Услуга")
    time_slot = models.ForeignKey(TimeSlot, on_delete=models.CASCADE, verbose_name="Временной слот")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Статус")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    notes = models.TextField(blank=True, verbose_name="Примечания")
    
    class Meta:
        verbose_name = "Бронирование"
        verbose_name_plural = "Бронирования"
        ordering = ['-created_at']

    @classmethod
    def cleanup_expired_pending(cls):
        """Автоматическая отмена бронирований, не подтвержденных в течение часа"""
        expired_time = timezone.now() - timedelta(hours=1)
        expired_bookings = cls.objects.filter(
            status='pending',
            created_at__lt=expired_time
        )
        
        cancelled_count = 0
        for booking in expired_bookings:
            booking.time_slot.is_available = True
            booking.time_slot.save()
            booking.status = 'cancelled'
            booking.save()
            cancelled_count += 1
        
        return cancelled_count
    
    @classmethod
    def complete_past_bookings(cls):
        """Автоматическое завершение прошедших бронирований"""
        today = timezone.now().date()
        past_bookings = cls.objects.filter(
            status='confirmed',
            time_slot__date__lt=today
        )
        
        completed_count = 0
        for booking in past_bookings:
            booking.status = 'completed'
            booking.save()
            completed_count += 1
        
        return completed_count
    
    def __str__(self):
        return f"{self.user.username} - {self.service.name} - {self.time_slot.date}"

class Review(models.Model):
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, verbose_name="Бронирование")
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)], verbose_name="Оценка")
    comment = models.TextField(blank=True, verbose_name="Комментарий")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата отзыва")
    
    class Meta:
        verbose_name = "Отзыв"
        verbose_name_plural = "Отзывы"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Отзыв {self.booking.user.username} - {self.rating} звезд"