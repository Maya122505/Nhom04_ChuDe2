from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('', RedirectView.as_view(url='/customer/', permanent=False)),

    # Phân luồng cho Admin hệ thống
    path('admin-sys/', include('dv_dathoa.urls.urls_admin')),

    # Phân luồng cho Khách hàng
    path('customer/', include('dv_dathoa.urls.urls_khach')),

    # Phân luồng cho Tiệm hoa
    path('shop/', include('dv_dathoa.urls.urls_tiem')),
]