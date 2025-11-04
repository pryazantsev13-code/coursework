from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from datetime import date
from django.db import models
from .models import Category, Service, TimeSlot, Booking, Review
from .forms import BookingForm, ReviewForm
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import JsonResponse

# Функции проверки прав
def is_manager(user):
    return user.groups.filter(name='Managers').exists() or user.is_staff

def is_admin(user):
    return user.groups.filter(name='Admins').exists() or user.is_superuser

def home(request):
    categories = Category.objects.all()
    
    # Получаем популярные услуги
    popular_services = Service.objects.annotate(
        review_count=models.Count('booking__review'),
        booking_count=models.Count('booking')
    ).order_by('-booking_count', '-review_count')[:4]
    
    # Статистика для авторизованных пользователей
    user_stats = {}
    if request.user.is_authenticated:
        user_stats = {
            'total_bookings': Booking.objects.filter(user=request.user).count(),
            'pending_bookings': Booking.objects.filter(user=request.user, status='pending').count(),
            'confirmed_bookings': Booking.objects.filter(user=request.user, status='confirmed').count(),
            'total_reviews': Review.objects.filter(booking__user=request.user).count(),
        }
    
    context = {
        'categories': categories,
        'popular_services': popular_services,
        'user_stats': user_stats,
    }
    return render(request, 'bookings/home.html', context)

def category_services(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    services = Service.objects.filter(category=category)
    return render(request, 'bookings/category_services.html', {
        'category': category,
        'services': services
    })

def service_detail(request, service_id):
    service = get_object_or_404(Service, id=service_id)
    
    # Получаем доступные временные слоты (только будущие даты)
    available_slots = TimeSlot.objects.filter(
        service=service,
        date__gte=date.today(),
        is_available=True,
        is_blocked=False
    ).order_by('date', 'start_time')
    
    return render(request, 'bookings/service_detail.html', {
        'service': service,
        'available_slots': available_slots
    })

@login_required
def create_booking(request, service_id, slot_id):
    service = get_object_or_404(Service, id=service_id)
    time_slot = get_object_or_404(TimeSlot, id=slot_id, is_available=True, is_blocked=False)
    
    # Проверяем, что пользователь не имеет активных бронирований на это время
    existing_booking = Booking.objects.filter(
        user=request.user,
        time_slot=time_slot,
        status__in=['pending', 'confirmed']
    ).exists()
    
    if existing_booking:
        messages.error(request, 'У вас уже есть активное бронирование на это время.')
        return redirect('service_detail', service_id=service_id)
    
    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.user = request.user
            booking.service = service
            booking.time_slot = time_slot
            booking.status = 'pending'
            booking.save()
            
            # Помечаем слот как занятый
            time_slot.is_available = False
            time_slot.save()
            
            messages.success(request, 'Бронирование успешно создано! Ожидайте подтверждения.')
            return redirect('profile')
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
    else:
        form = BookingForm()
    
    return render(request, 'bookings/create_booking.html', {
        'form': form,
        'service': service,
        'time_slot': time_slot
    })

@login_required
def cancel_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    
    if booking.status in ['pending', 'confirmed']:
        # Освобождаем временной слот
        time_slot = booking.time_slot
        time_slot.is_available = True
        time_slot.save()
        
        # Отменяем бронирование
        booking.status = 'cancelled'
        booking.save()
        
        # Если AJAX запрос, возвращаем JSON
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            from django.http import JsonResponse
            return JsonResponse({
                'success': True,
                'message': 'Бронирование успешно отменено.'
            })
        else:
            messages.success(request, 'Бронирование успешно отменено.')
    else:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            from django.http import JsonResponse
            return JsonResponse({
                'success': False,
                'message': 'Невозможно отменить это бронирование.'
            }, status=400)
        else:
            messages.error(request, 'Невозможно отменить это бронирование.')
    
    return redirect('profile')

# Функции менеджера
@login_required
@user_passes_test(is_manager)
def manager_dashboard(request):
    """Панель менеджера с AJAX поддержкой"""
    tab = request.GET.get('tab', 'today')
    
    # Все бронирования
    all_bookings = Booking.objects.all().order_by('-created_at')
    
    # Бронирования, ожидающие подтверждения
    pending_bookings = Booking.objects.filter(status='pending').order_by('time_slot__date', 'time_slot__start_time')
    
    # Сегодняшние бронирования
    today = timezone.now().date()
    today_bookings = Booking.objects.filter(
        time_slot__date=today,
        status__in=['pending', 'confirmed']
    ).order_by('time_slot__start_time')
    
    context = {
        'all_bookings': all_bookings,
        'pending_bookings': pending_bookings,
        'today_bookings': today_bookings,
        'today': today,
    }
    
    # Если AJAX запрос, возвращаем частичный шаблон
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        if tab == 'today':
            return render(request, 'bookings/_today_bookings.html', context)
        elif tab == 'pending':
            return render(request, 'bookings/_pending_bookings.html', context)
        elif tab == 'all':
            return render(request, 'bookings/_all_bookings.html', context)
    
    return render(request, 'bookings/manager_dashboard.html', context)

@login_required
@user_passes_test(is_manager)
def update_booking_status(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        manager_notes = request.POST.get('manager_notes', '')
        
        if new_status in dict(Booking.STATUS_CHOICES):
            booking.status = new_status
            booking.manager = request.user
            booking.manager_notes = manager_notes
            booking.save()
            
            # Если AJAX запрос, возвращаем JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                from django.http import JsonResponse
                return JsonResponse({
                    'success': True,
                    'message': f'Статус бронирования обновлен на "{booking.get_status_display()}"'
                })
            else:
                messages.success(request, f'Статус бронирования обновлен на "{booking.get_status_display()}"')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                from django.http import JsonResponse
                return JsonResponse({
                    'success': False,
                    'message': 'Неверный статус'
                }, status=400)
            else:
                messages.error(request, 'Неверный статус')
    
    # Для не-AJAX запросов
    return redirect('manager_dashboard')

@login_required
@user_passes_test(is_manager)
def block_time_slots(request):
    """Блокировка слотов на конкретную дату"""
    if request.method == 'POST':
        date_str = request.POST.get('date')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        reason = request.POST.get('reason', '')
        
        try:
            # Блокируем все слоты на эту дату в указанном временном диапазоне
            time_slots = TimeSlot.objects.filter(
                date=date_str,
                start_time__gte=start_time,
                end_time__lte=end_time
            )
            
            blocked_count = 0
            for slot in time_slots:
                slot.is_blocked = True
                slot.is_available = False
                slot.block_reason = reason
                slot.blocked_at = timezone.now()  # Добавляем время блокировки
                slot.save()
                blocked_count += 1
            
            messages.success(request, f'Заблокировано {blocked_count} временных слотов. {reason}')
            return redirect('blocked_slots_list')  # Перенаправляем на список блокировок
        except Exception as e:
            messages.error(request, f'Ошибка при блокировке: {e}')
    
    today = timezone.now().date()
    return render(request, 'bookings/block_slots.html', {'today': today})

@login_required
@user_passes_test(is_manager)
def blocked_slots_list(request):
    """Список заблокированных слотов"""
    # Заблокированные слоты (будущие даты)
    blocked_slots = TimeSlot.objects.filter(
        is_blocked=True,
        date__gte=date.today()
    ).order_by('date', 'start_time')
    
    # Сгруппируем по дате для удобства
    blocked_by_date = {}
    for slot in blocked_slots:
        date_str = slot.date.strftime('%Y-%m-%d')
        if date_str not in blocked_by_date:
            blocked_by_date[date_str] = []
        blocked_by_date[date_str].append(slot)
    
    context = {
        'blocked_slots': blocked_slots,
        'blocked_by_date': blocked_by_date,
    }
    return render(request, 'bookings/blocked_slots_list.html', context)

@login_required
@user_passes_test(is_manager)
def unblock_time_slots(request):
    """Разблокировка временных слотов"""
    if request.method == 'POST':
        slot_ids = request.POST.getlist('slot_ids')
        
        if slot_ids:
            # Разблокируем выбранные слоты
            unblocked_count = 0
            for slot_id in slot_ids:
                try:
                    slot = TimeSlot.objects.get(id=slot_id, is_blocked=True)
                    slot.is_blocked = False
                    slot.is_available = True
                    slot.block_reason = ''
                    slot.blocked_at = None
                    slot.save()
                    unblocked_count += 1
                except TimeSlot.DoesNotExist:
                    continue
            
            messages.success(request, f'Разблокировано {unblocked_count} временных слотов.')
        else:
            messages.error(request, 'Выберите слоты для разблокировки.')
        
        return redirect('blocked_slots_list')
    
    # GET запрос - показываем форму выбора слотов для разблокировки
    blocked_slots = TimeSlot.objects.filter(
        is_blocked=True,
        date__gte=date.today()
    ).order_by('date', 'start_time')
    
    return render(request, 'bookings/unblock_slots.html', {
        'blocked_slots': blocked_slots
    })

@login_required
@user_passes_test(is_manager)
def bulk_block_slots(request):
    """Массовая блокировка слотов по диапазону дат"""
    if request.method == 'POST':
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        reason = request.POST.get('reason', '')
        
        try:
            # Блокируем слоты в диапазоне дат
            time_slots = TimeSlot.objects.filter(
                date__gte=start_date,
                date__lte=end_date,
                start_time__gte=start_time,
                end_time__lte=end_time
            )
            
            blocked_count = 0
            for slot in time_slots:
                slot.is_blocked = True
                slot.is_available = False
                slot.block_reason = reason
                slot.blocked_at = timezone.now()
                slot.save()
                blocked_count += 1
            
            messages.success(request, f'Заблокировано {blocked_count} временных слотов с {start_date} по {end_date}. {reason}')
            return redirect('blocked_slots_list')
        except Exception as e:
            messages.error(request, f'Ошибка при блокировке: {e}')
    
    today = timezone.now().date()
    return render(request, 'bookings/bulk_block_slots.html', {'today': today})

# Функции администратора
@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    """Панель администратора с AJAX поддержкой"""
    section = request.GET.get('section', 'all')
    
    stats = {
        'total_users': User.objects.count(),
        'total_bookings': Booking.objects.count(),
        'pending_bookings': Booking.objects.filter(status='pending').count(),
        'total_services': Service.objects.count(),
        'total_categories': Category.objects.count(),
    }
    
    # Недавние действия
    recent_bookings = Booking.objects.all().order_by('-created_at')[:10]
    recent_users = User.objects.all().order_by('-date_joined')[:5]
    
    context = {
        'stats': stats,
        'recent_bookings': recent_bookings,
        'recent_users': recent_users,
    }
    
    # Если AJAX запрос, возвращаем частичный шаблон
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.GET.get('section'):
        if section == 'stats':
            return render(request, 'bookings/_admin_stats.html', context)
        elif section == 'bookings':
            return render(request, 'bookings/_recent_bookings.html', context)
        elif section == 'users':
            return render(request, 'bookings/_recent_users.html', context)
    
    return render(request, 'bookings/admin_dashboard.html', context)

@login_required
@user_passes_test(is_admin)
def manage_categories(request):
    """Управление категориями с AJAX поддержкой"""
    if request.method == 'POST':
        # Всегда обрабатываем добавление категории
        name = request.POST.get('name')
        description = request.POST.get('description')
        
        if name:  # Проверяем, что имя не пустое
            try:
                Category.objects.create(name=name, description=description)
                # Обновляем список категорий
                categories = Category.objects.all()
                
                # Для AJAX возвращаем обновленный список
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return render(request, 'bookings/_categories_list.html', {
                        'categories': categories
                    })
                messages.success(request, 'Категория успешно добавлена')
            except Exception as e:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    from django.http import JsonResponse
                    return JsonResponse({'error': str(e)}, status=400)
                messages.error(request, f'Ошибка при добавлении категории: {e}')
        
        # Обработка удаления категории
        category_id = request.POST.get('category_id')
        if category_id:
            try:
                Category.objects.filter(id=category_id).delete()
                categories = Category.objects.all()
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return render(request, 'bookings/_categories_list.html', {
                        'categories': categories
                    })
                messages.success(request, 'Категория удалена')
            except Exception as e:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    from django.http import JsonResponse
                    return JsonResponse({'error': str(e)}, status=400)
                messages.error(request, f'Ошибка при удалении категории: {e}')
    
    # GET запрос - отображаем страницу или список
    categories = Category.objects.all()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.GET.get('ajax'):
        return render(request, 'bookings/_categories_list.html', {
            'categories': categories
        })
    
    return render(request, 'bookings/manage_categories.html', {
        'categories': categories
    })

@login_required
@user_passes_test(is_admin)
def manage_services(request):
    """Управление услугами с AJAX поддержкой"""
    if request.method == 'POST':
        # Обработка добавления услуги
        name = request.POST.get('name')
        category_id = request.POST.get('category')
        price = request.POST.get('price')
        duration = request.POST.get('duration')
        description = request.POST.get('description')
        
        if name and category_id and price and duration:  # Проверяем обязательные поля
            try:
                category = Category.objects.get(id=category_id)
                Service.objects.create(
                    name=name,
                    category=category,
                    price=price,
                    duration=duration,
                    description=description
                )
                # Обновляем списки
                services = Service.objects.all().select_related('category')
                categories = Category.objects.all()
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return render(request, 'bookings/_services_list.html', {
                        'services': services,
                        'categories': categories
                    })
                messages.success(request, 'Услуга успешно добавлена')
            except Exception as e:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    from django.http import JsonResponse
                    return JsonResponse({'error': str(e)}, status=400)
                messages.error(request, f'Ошибка при добавлении услуги: {e}')
        
        # Обработка удаления услуги
        service_id = request.POST.get('service_id')
        if service_id:
            try:
                Service.objects.filter(id=service_id).delete()
                services = Service.objects.all().select_related('category')
                categories = Category.objects.all()
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return render(request, 'bookings/_services_list.html', {
                        'services': services,
                        'categories': categories
                    })
                messages.success(request, 'Услуга удалена')
            except Exception as e:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    from django.http import JsonResponse
                    return JsonResponse({'error': str(e)}, status=400)
                messages.error(request, f'Ошибка при удалении услуги: {e}')
    
    # GET запрос
    services = Service.objects.all().select_related('category')
    categories = Category.objects.all()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.GET.get('ajax'):
        return render(request, 'bookings/_services_list.html', {
            'services': services,
            'categories': categories
        })
    
    return render(request, 'bookings/manage_services.html', {
        'services': services,
        'categories': categories
    })

def service_search(request):
    """Поиск услуг"""
    query = request.GET.get('q', '')
    category_id = request.GET.get('category', '')
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')
    
    services = Service.objects.all()
    
    # Поиск по названию и описанию
    if query:
        services = services.filter(
            Q(name__icontains=query) | 
            Q(description__icontains=query) |
            Q(category__name__icontains=query)
        )
    
    # Фильтр по категории
    if category_id:
        services = services.filter(category_id=category_id)
    
    # Фильтр по цене
    if min_price:
        services = services.filter(price__gte=min_price)
    if max_price:
        services = services.filter(price__lte=max_price)
    
    categories = Category.objects.all()
    
    context = {
        'services': services,
        'categories': categories,
        'query': query,
        'selected_category': category_id,
        'min_price': min_price,
        'max_price': max_price,
    }
    
    # Если AJAX запрос, возвращаем только частичный шаблон
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render(request, 'bookings/_service_results.html', context)
    
    return render(request, 'bookings/service_search.html', context)

@login_required
def create_review(request, booking_id):
    """Создание отзыва"""
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    
    # Проверяем, что бронирование завершено и отзыва еще нет
    if booking.status != 'completed':
        messages.error(request, 'Можно оставить отзыв только для завершенных бронирований.')
        return redirect('profile')
    
    if Review.objects.filter(booking=booking).exists():
        messages.error(request, 'Вы уже оставили отзыв для этого бронирования.')
        return redirect('profile')
    
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.booking = booking
            review.save()
            messages.success(request, 'Отзыв успешно добавлен!')
            return redirect('profile')
    else:
        form = ReviewForm()
    
    return render(request, 'bookings/create_review.html', {
        'form': form,
        'booking': booking
    })

@login_required
def user_reviews(request):
    """Отзывы пользователя"""
    reviews = Review.objects.filter(booking__user=request.user).select_related('booking__service')
    return render(request, 'bookings/user_reviews.html', {'reviews': reviews})

@login_required
@user_passes_test(is_admin)
def get_categories_json(request):
    """API для получения списка категорий в JSON формате"""
    categories = Category.objects.all().values('id', 'name')
    return JsonResponse(list(categories), safe=False)