from django import forms
from .models import Booking, Review

class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['notes']
        widgets = {
            'notes': forms.Textarea(attrs={
                'rows': 4, 
                'placeholder': 'Дополнительные пожелания или комментарии...',
                'class': 'form-control'
            }),
        }
        labels = {
            'notes': 'Комментарий к бронированию',
        }

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'comment': forms.Textarea(attrs={
                'rows': 4, 
                'placeholder': 'Поделитесь вашими впечатлениями...',
                'class': 'form-control'
            }),
            'rating': forms.RadioSelect(choices=[(i, i) for i in range(1, 6)])
        }
        labels = {
            'rating': 'Оценка',
            'comment': 'Комментарий',
        }