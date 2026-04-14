from django.urls import path
from dv_dathoa.views import views_tiem

# URLs related only to tiệm (vendor)
urlpatterns = [
    # --- LUỒNG TIỆM HOA (VENDOR) ---
    path('vendor/login_shop/', views_tiem.login_shop, name='login_shop'),
    path('vendor/logout/', views_tiem.logout_shop, name='logout_shop'),
    path('register/tiem/', views_tiem.register_tiem, name='register_tiem'),
    path('register/tiem/shop/', views_tiem.register_shop, name='register_shop'),
    path('vendor/dashboard/', views_tiem.dashboard, name='vendor_dashboard'),
    path('vendor/pending/', views_tiem.vendor_pending, name='vendor_pending'),
    path('vendor/quan-ly-ho-so/', views_tiem.profile, name='vendor_profile'),
    path('vendor/cap-nhat-ho-so/', views_tiem.profile_edit, name='vendor_profile_edit'),
    path('vendor/chat/', views_tiem.chat, name='vendor_chat'),
    path('vendor/chat/unread.json', views_tiem.chat_unread_json, name='vendor_chat_unread'),
    path('vendor/chat/<str:chat_id>/messages.json', views_tiem.chat_messages_json, name='vendor_chat_messages'),
    path('vendor/chat/<str:chat_id>/send', views_tiem.chat_send, name='vendor_chat_send'),
    path('vendor/bao-gia/', views_tiem.quotes, name='vendor_quotes'),
    path('vendor/quan-ly-don/', views_tiem.manage_orders, name='vendor_orders'),
    path('vendor/thong-ke/', views_tiem.stats, name='vendor_stats'),
    path('vendor/quan-ly-don/update-status/', views_tiem.update_order_status, name='update_order_status'),
    path('vendor/bao-gia/chi-tiet/<str:order_id>/', views_tiem.order_detail, name='vendor_order_detail'),
    path('vendor/gui-bao-gia/<str:req_id>/', views_tiem.send_quote, name='send_quote'),
]
