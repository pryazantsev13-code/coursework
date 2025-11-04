from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('category/<int:category_id>/', views.category_services, name='category_services'),
    path('service/<int:service_id>/', views.service_detail, name='service_detail'),
    path('booking/create/<int:service_id>/<int:slot_id>/', views.create_booking, name='create_booking'),
    path('booking/cancel/<int:booking_id>/', views.cancel_booking, name='cancel_booking'),
    path('search/', views.service_search, name='service_search'),
    path('review/create/<int:booking_id>/', views.create_review, name='create_review'),
    path('reviews/', views.user_reviews, name='user_reviews'),
    path('api/categories/', views.get_categories_json, name='get_categories_json'),
    
    # Менеджер-панель
    path('manager/', views.manager_dashboard, name='manager_dashboard'),
    path('manager/booking/<int:booking_id>/update/', views.update_booking_status, name='update_booking_status'),
    path('manager/blocked-slots/', views.blocked_slots_list, name='blocked_slots_list'),
    path('manager/block-slots/', views.block_time_slots, name='block_time_slots'),
    path('manager/block-slots/bulk/', views.bulk_block_slots, name='bulk_block_slots'),
    path('manager/unblock-slots/', views.unblock_time_slots, name='unblock_time_slots'),
    
    # Админ-панель
    path('admin-panel/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-panel/services/', views.manage_services, name='manage_services'),
    path('admin-panel/categories/', views.manage_categories, name='manage_categories'),
]