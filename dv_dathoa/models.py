from django.db import models
from django.contrib.auth.models import AbstractUser

# Bảng chính: Auth_User (Custom từ AbstractUser để thêm trường role)
class User(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('customer', 'Customer'),
        ('shop', 'Shop'),
    ]
    # first_name, last_name, is_superuser... đã có sẵn trong AbstractUser
    phonenumber = models.CharField(max_length=20, blank=True, default='')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='customer')

    def __str__(self):
        return f"{self.username} - {self.get_role_display()}"

# Bảng: CustomerProfile
class CustomerProfile(models.Model):
    User_id = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, related_name='customer_profile')
    customer_id = models.CharField(max_length=50, unique=True) # Tên hiển thị riêng
    dia_chi_mac_dinh = models.TextField()

    def __str__(self):
        return self.User_id.username

# Bảng: TiemHoa_profile
class TiemHoaProfile(models.Model):
    User_id = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, related_name='shop_profile')
    tiemhoa_id = models.CharField(max_length=50, unique=True) # Tên hiển thị riêng
    diaChi = models.TextField()
    moTa = models.TextField(null=True, blank=True)
    maSoThue = models.CharField(max_length=50)
    hinhAnhSanPham = models.ImageField(upload_to='shop_products/', null=True, blank=True)
    hinhAnhSanPham_2 = models.ImageField(upload_to='shop_products/', null=True, blank=True)
    hinhAnhSanPham_3 = models.ImageField(upload_to='shop_products/', null=True, blank=True)
    hinhAnhSanPham_4 = models.ImageField(upload_to='shop_products/', null=True, blank=True)
    logoTiemHoa = models.ImageField(upload_to='shop_logos/', null=True, blank=True)
    DUYET_CHOICES = [
        (0, 'Chờ duyệt'),
        (1, 'Đã duyệt'),
        (2, 'Bị từ chối'),
    ]
    trangThaiDuyet = models.IntegerField(choices=DUYET_CHOICES, default=0)
    soTaiKhoan = models.CharField(max_length=50)
    tenNganHang = models.CharField(max_length=100)
    tenChuTaiKhoan = models.CharField(max_length=100)
    QR_thanh_toan = models.ImageField(upload_to='shop_qrs/', null=True, blank=True)
    bank_bin = models.CharField(max_length=20, blank=True, default='')
    anh_url = models.URLField(blank=True, default='')
    the_loai = models.CharField(max_length=50, blank=True, default='')
    soDanhGia = models.PositiveIntegerField(default=0)
    diemTrungBinh = models.DecimalField(max_digits=3, decimal_places=1, default=0)

    def __str__(self):
        return self.User_id.username

    @property
    def avatar_url(self):
        """Logo shop cho avatar. None nếu chưa có, template sẽ fallback sang chữ cái."""
        if self.logoTiemHoa:
            try:
                return self.logoTiemHoa.url
            except Exception:
                return None
        return None

    @property
    def display_name(self):
        return self.User_id.first_name or self.User_id.username

    @property
    def avatar_initial(self):
        return (self.display_name[:1] or '?').upper()

    @property
    def card_image_url(self):
        """Ảnh đại diện cho card shop: logo → hinhAnhSanPham → ảnh gallery → anh_url → placeholder."""
        if self.logoTiemHoa:
            try:
                return self.logoTiemHoa.url
            except Exception:
                pass
        if self.hinhAnhSanPham:
            try:
                return self.hinhAnhSanPham.url
            except Exception:
                pass
        first = self.gallery.first() if self.pk else None
        if first and first.image:
            try:
                return first.image.url
            except Exception:
                pass
        if self.anh_url:
            return self.anh_url
        # Placeholder: mỗi shop một ảnh hoa khác nhau, stable theo pk
        fallbacks = [
            'https://images.unsplash.com/photo-1490750967868-88aa4486c946?w=800&auto=format&fit=crop',
            'https://images.unsplash.com/photo-1508610048659-a06b669e3321?w=800&auto=format&fit=crop',
            'https://images.unsplash.com/photo-1487070183336-b863922373d4?w=800&auto=format&fit=crop',
            'https://images.unsplash.com/photo-1518895949257-7621c3c786d7?w=800&auto=format&fit=crop',
            'https://images.unsplash.com/photo-1501004318641-b39e6451bec6?w=800&auto=format&fit=crop',
            'https://images.unsplash.com/photo-1455659817273-f96807779a8a?w=800&auto=format&fit=crop',
        ]
        return fallbacks[(self.pk or 0) % len(fallbacks)]


class ShopGalleryImage(models.Model):
    shop = models.ForeignKey(TiemHoaProfile, on_delete=models.CASCADE, related_name='gallery')
    image = models.ImageField(upload_to='shop_gallery/')
    category = models.CharField(max_length=50, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


# Bảng: PhienChat (Kết nối đến CustomerProfile và TiemHoaProfile)
class PhienChat(models.Model):
    maPhienChat = models.CharField(max_length=50, primary_key=True)
    CHAT_STATUS = [
        ('mo', 'Mở'),
        ('dong', 'Đóng'),
        ('da_xu_ly', 'Đã xử lý'),
    ]
    trangThai = models.CharField(max_length=20, choices=CHAT_STATUS, default='mo')
    thoiGianTao = models.DateTimeField(auto_now_add=True)
    last_read_kh = models.DateTimeField(null=True, blank=True)
    last_read_tiem = models.DateTimeField(null=True, blank=True)
    maKhachHang = models.ForeignKey(CustomerProfile, on_delete=models.CASCADE, related_name='chats')
    maTiemHoa = models.ForeignKey(TiemHoaProfile, on_delete=models.CASCADE, related_name='chats')

    def __str__(self):
        return f"Chat {self.maPhienChat}"

# Bảng: TinNhan
class TinNhan(models.Model):
    maTinNhan = models.AutoField(primary_key=True)
    maTaiKhoan = models.ForeignKey(User, on_delete=models.CASCADE, related_name='messages') # Người gửi
    noiDung = models.TextField()
    hinhAnh = models.ImageField(upload_to='chat_images/', null=True, blank=True)
    thoiGian = models.DateTimeField(auto_now_add=True)
    maPhienChat = models.ForeignKey(PhienChat, on_delete=models.CASCADE, related_name='messages')

    def __str__(self):
        return f"MSG {self.maTinNhan} in {self.maPhienChat.maPhienChat}"

# Bảng: DonHang (Chứa toàn bộ thông tin chi tiết đơn hàng)
class DonHang(models.Model):
    maDonHang = models.CharField(max_length=50, primary_key=True)
    ngayDat = models.DateTimeField(auto_now_add=True)
    anhSanPhamThucTe = models.ImageField(upload_to='order_products/', null=True, blank=True)
    DON_HANG_STATUS = [
        ('chon_hoa', 'Chọn hoa'),
        ('cho_thanh_toan', 'Chờ thanh toán'),
        ('dang_thuc_hien', 'Đang thực hiện'),
        ('hoan_thanh', 'Hoàn thành'),
    ]
    trangThaiDonHang = models.CharField(max_length=20, choices=DON_HANG_STATUS, default='chon_hoa')
    ngayGiaoDuKien = models.DateTimeField()
    phiVanChuyen = models.DecimalField(max_digits=15, decimal_places=0)
    anhMauDeXuat = models.ImageField(upload_to='order_proposals/', null=True, blank=True)
    noiDungTuVan = models.TextField(null=True, blank=True)
    YEU_CAU_CHOICES = [
        (1, 'Chờ'),
        (2, 'Xác nhận'),
        (0, 'Từ chối'),
    ]
    trangThai = models.IntegerField(choices=YEU_CAU_CHOICES, default=1)
    dipSuDung = models.CharField(max_length=255)
    nganSach = models.DecimalField(max_digits=15, decimal_places=0)
    mauSac = models.CharField(max_length=100)
    thoiGianHoanThanh = models.DateTimeField()
    phongCach = models.CharField(max_length=255)
    ghiChu = models.TextField(null=True, blank=True)
    dia_chi_nhan_hang = models.TextField()
    User_id = models.ForeignKey(CustomerProfile, on_delete=models.CASCADE, related_name='orders')
    tiemhoa_id = models.ForeignKey(TiemHoaProfile, on_delete=models.CASCADE, related_name='orders')

    def __str__(self):
        return self.maDonHang

# Bảng: ThanhToan
class ThanhToan(models.Model):
    maThanhToan = models.CharField(max_length=50, primary_key=True)
    tongTien = models.DecimalField(max_digits=15, decimal_places=0)
    noiDung = models.TextField()
    hinhAnhBienLai = models.ImageField(upload_to='payment_receipts/')
    maDonHang = models.ForeignKey(DonHang, on_delete=models.CASCADE, related_name='payments')

    def __str__(self):
        return self.maThanhToan

# Bảng: DanhGia
class DanhGia(models.Model):
    maDanhGia = models.AutoField(primary_key=True)
    soSao = models.IntegerField()
    noiDung = models.TextField()
    hinhAnhThucTe = models.ImageField(upload_to='review_images/', null=True, blank=True)
    ngayDanhGia = models.DateTimeField(auto_now_add=True)
    maDonHang = models.ForeignKey(DonHang, on_delete=models.CASCADE, related_name='reviews')

    def __str__(self):
        return f"Review {self.maDanhGia} for {self.maDonHang.maDonHang}"