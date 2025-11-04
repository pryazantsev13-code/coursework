from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from bookings.models import Booking

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')  # Редирект на главную после регистрации
    else:
        form = UserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})

@login_required
def profile(request):
    user_bookings = Booking.objects.filter(user=request.user).order_by('-created_at')
    
    # Если AJAX запрос, возвращаем только список бронирований
    if request.GET.get('ajax') == 'true' or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render(request, 'accounts/_bookings_list.html', {'bookings': user_bookings})
    
    return render(request, 'accounts/profile.html', {'bookings': user_bookings})