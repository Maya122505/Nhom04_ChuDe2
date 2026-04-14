from django.urls import path
from dv_dathoa.views import views_khach, views_tiem, views_admin

urlpatterns = [
    # --- LUỒNG KHÁCH HÀNG ---
    path('', views_khach.home_view, name='home'),
    path('after-login/', views_khach.after_login_view, name='after_login'),
    path('after_login/', views_khach.after_login_view, name='after_login_alias'),
    path('search-landing/', views_khach.search_landing_view, name='search_landing'),
    path('search-results/', views_khach.search_results_view, name='search_results'),
    path('detail-logged/<int:id>/', views_khach.detail_logged_view, name='detail_logged'),
    path('request/<int:id>/', views_khach.request_create_view, name='request_create'),
    path('request-pending/<str:id>/', views_khach.request_pending_view, name='request_pending'),
    path('orders/<str:id>/status.json', views_khach.order_status_json_view, name='order_status_json'),
    path('chat/<int:id>/', views_khach.chat_kh_view, name='chat_kh'),
    path('chat/<int:id>/messages.json', views_khach.chat_messages_json_view, name='chat_messages_json'),
    path('notifications.json', views_khach.notifications_json_view, name='notifications_json'),
    path('quotes/', views_khach.quote_list_view, name='quote_list'),
    path('quote/<str:id>/', views_khach.quote_confirm_view, name='quote_confirm'),
    path('payment/<str:id>/', views_khach.payment_view, name='payment'),
    path('orders/', views_khach.order_status_view, name='order_status'),
    path('orders/<str:id>/', views_khach.order_status_detail_view, name='order_status_detail'),
    path('orders/<str:id>/done/', views_khach.order_status_detail_done_view, name='order_status_detail_done'),
    path('orders/<str:id>/review/', views_khach.review_service_view, name='review_service'),
    path('orders/<str:id>/review/done/', views_khach.review_service_done_view, name='review_service_done'),
    path('search/', views_khach.search_view, name='search'),
    path('search/suggest/', views_khach.search_suggest_view, name='search_suggest'),
    path('detail/<int:id>/', views_khach.detail_view, name='detail'),

    # --- AUTHENTICATION ---
    path('login/', views_khach.login_view, name='login'),
    path('logout/', views_khach.logout_view, name='logout'),
    path('register/', views_khach.register_view, name='register'),
    path('success/', views_khach.success_view, name='success'),
]
