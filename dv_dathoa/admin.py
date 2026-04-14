from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from dv_dathoa.models import (
    User, CustomerProfile, TiemHoaProfile,
    PhienChat, TinNhan, DonHang, ThanhToan, DanhGia,
)


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'is_staff')
    fieldsets = UserAdmin.fieldsets + (('Role', {'fields': ('role',)}),)


@admin.register(DonHang)
class DonHangAdmin(admin.ModelAdmin):
    list_display = ('maDonHang', 'User_id', 'tiemhoa_id', 'trangThaiDonHang', 'trangThai', 'ngayDat')
    list_filter = ('trangThaiDonHang', 'trangThai')
    search_fields = ('maDonHang',)


admin.site.register(CustomerProfile)
admin.site.register(TiemHoaProfile)
admin.site.register(PhienChat)
admin.site.register(TinNhan)
admin.site.register(ThanhToan)
admin.site.register(DanhGia)
