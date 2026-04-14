from django.urls import path
from dv_dathoa.views import views_admin

urlpatterns = [
    path('dashboard/', views_admin.admin_dashboard, name='admin_dashboard'),
    # Thêm các đường dẫn cho các hàm khác bạn đã viết trong views
    path('login/', views_admin.login_admin, name='login_admin'),
    path('logout/', views_admin.logout_admin, name='logout_admin'),
    path('users/', views_admin.user_management, name='admin_users'),
    path('users/<int:user_id>/toggle-active/', views_admin.toggle_user_active, name='toggle_user_active'),
    path('pending/<int:shop_id>/', views_admin.pending_detail, name='pending_detail'),
]