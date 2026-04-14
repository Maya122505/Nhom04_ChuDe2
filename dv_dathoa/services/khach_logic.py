import uuid
from django.utils import timezone
from dv_dathoa.models import (
    User, CustomerProfile, TiemHoaProfile, DonHang, ThanhToan,
    DanhGia, PhienChat, TinNhan,
)


def _short_id(prefix):
    return f"{prefix}-{uuid.uuid4().hex[:8].upper()}"


def register_customer(username, email, password, first_name='', last_name='', phonenumber=''):
    user = User.objects.create_user(
        username=username, email=email, password=password, role='customer',
        first_name=first_name, last_name=last_name,
    )
    user.phonenumber = phonenumber
    user.save()
    CustomerProfile.objects.create(
        User_id=user,
        customer_id=f"KH-{user.pk}",
        dia_chi_mac_dinh='',
    )
    return user


def get_or_create_customer_profile(user):
    try:
        return user.customer_profile
    except CustomerProfile.DoesNotExist:
        return CustomerProfile.objects.create(
            User_id=user,
            customer_id=f"KH-{user.pk}",
            dia_chi_mac_dinh='',
        )


DEMO_SHOPS = [
    {
        'username': 'lavender_studio', 'display': 'Lavender Studio',
        'tiemhoa_id': 'lavender-studio', 'the_loai': 'Vintage',
        'moTa': 'Chuyên thiết kế hoa cưới và sự kiện cao cấp với phong cách cổ điển Pháp.',
        'anh_url': 'https://shophoasunny.vn/wp-content/uploads/2022/07/shop-hoa-tuoi-quan-1-3.jpg',
        'diaChi': '123 Đường Hoa, Hà Nội',
        'soDanhGia': 128, 'diemTrungBinh': 4.9,
    },
    {
        'username': 'moon_studio', 'display': 'Moon Studio',
        'tiemhoa_id': 'moon-studio', 'the_loai': 'Hiện đại',
        'moTa': 'Nổi tiếng với mẫu hoa hộp quà tinh tế và sang trọng bậc nhất.',
        'anh_url': 'https://vitiflower.com.vn/wp-content/uploads/2024/08/z3628914252507_0b255ff541d1c4a40ee513f92bb8e954.jpg',
        'diaChi': '45 Nguyễn Văn Linh, Đà Nẵng',
        'soDanhGia': 86, 'diemTrungBinh': 4.8,
    },
    {
        'username': 'coco_studio', 'display': 'Coco Studio',
        'tiemhoa_id': 'coco-studio', 'the_loai': 'Tối giản',
        'moTa': 'Cắm hoa ngẫu hứng, mang lại cảm giác bình yên và mộc mạc.',
        'anh_url': 'https://dienhoahiendai.com/wp-content/uploads/2019/08/cua-hang-hoa-ha-noi.jpg',
        'diaChi': '78 Hai Bà Trưng, TP HCM',
        'soDanhGia': 52, 'diemTrungBinh': 5.0,
    },
    {
        'username': 'rose_garden', 'display': 'Rose Garden Paris',
        'tiemhoa_id': 'rose-garden', 'the_loai': 'Lãng mạn',
        'moTa': 'Thiên đường của những đoá hồng nhập khẩu cao cấp từ Ecuador và Hà Lan.',
        'anh_url': 'https://hoatuoidatviet.vn/upload/images/shop-hoa-tuoi-phuong-cau-ong-lanh.jpg',
        'diaChi': '12 Lê Duẩn, Hà Nội',
        'soDanhGia': 201, 'diemTrungBinh': 4.7,
    },
    {
        'username': 'harmony_flowers', 'display': 'Harmony Flowers',
        'tiemhoa_id': 'harmony-flowers', 'the_loai': 'Sự kiện',
        'moTa': 'Chuyên hoa khai trương, hoa sự kiện sang trọng, giao hàng nhanh nội thành.',
        'anh_url': 'https://flowersight.com/wp-content/uploads/2023/05/ke-hoa-mung-khai-truong-dep-44.jpg',
        'diaChi': '300 Trần Hưng Đạo, Đà Nẵng',
        'soDanhGia': 77, 'diemTrungBinh': 4.6,
    },
]


def ensure_demo_shop():
    """Seed các tiệm hoa demo nếu DB chưa có."""
    for data in DEMO_SHOPS:
        if TiemHoaProfile.objects.filter(tiemhoa_id=data['tiemhoa_id']).exists():
            continue
        shop_user, _ = User.objects.get_or_create(
            username=data['username'],
            defaults={'email': f"{data['username']}@demo.vn", 'role': 'shop'},
        )
        shop_user.first_name = data['display']
        shop_user.role = 'shop'
        if not shop_user.has_usable_password():
            shop_user.set_password('demo1234')
        shop_user.save()
        TiemHoaProfile.objects.create(
            User_id=shop_user,
            tiemhoa_id=data['tiemhoa_id'],
            diaChi=data['diaChi'],
            moTa=data['moTa'],
            maSoThue='0123456789',
            trangThaiDuyet=1,
            soTaiKhoan='0123456789',
            tenNganHang='Vietcombank',
            tenChuTaiKhoan=data['display'].upper(),
            anh_url=data['anh_url'],
            the_loai=data['the_loai'],
            soDanhGia=data['soDanhGia'],
            diemTrungBinh=data['diemTrungBinh'],
        )
    return TiemHoaProfile.objects.first()


def seed_demo_orders(customer_profile):
    """Tạo 3 đơn demo cho user mới để có data test."""
    from decimal import Decimal
    from django.utils import timezone
    from datetime import timedelta
    if customer_profile.orders.exists():
        return
    shops = list(TiemHoaProfile.objects.filter(trangThaiDuyet=1)[:3])
    if not shops:
        return
    statuses = [
        ('dang_thuc_hien', 2, 'Đám cưới', 'Cổ điển', 2500000),
        ('hoan_thanh', 2, 'Sinh nhật', 'Hiện đại', 850000),
        ('chon_hoa', 1, 'Khai trương', 'Sang trọng', 1200000),
    ]
    now = timezone.now()
    for i, (status, yc, dip, style, budget) in enumerate(statuses):
        DonHang.objects.create(
            maDonHang=_short_id('ORD'),
            trangThaiDonHang=status,
            trangThai=yc,
            dipSuDung=dip,
            phongCach=style,
            mauSac='Hồng pastel',
            nganSach=Decimal(budget),
            phiVanChuyen=Decimal('20000'),
            thoiGianHoanThanh=now + timedelta(days=5 + i),
            ngayGiaoDuKien=now + timedelta(days=5 + i),
            dia_chi_nhan_hang='7 An Thượng 24, Đà Nẵng',
            noiDungTuVan='Bó hoa tone pastel theo yêu cầu khách.',
            User_id=customer_profile,
            tiemhoa_id=shops[i % len(shops)],
        )


def create_order(customer_profile, shop_profile, form_data):
    from decimal import Decimal
    return DonHang.objects.create(
        maDonHang=_short_id('ORD'),
        ngayGiaoDuKien=form_data.get('ngayGiaoDuKien') or form_data['thoiGianHoanThanh'],
        phiVanChuyen=Decimal('20000'),
        trangThaiDonHang='chon_hoa',
        trangThai=1,  # Chờ duyệt
        dipSuDung=form_data['dipSuDung'],
        nganSach=form_data['nganSach'],
        mauSac='Chưa chọn',
        thoiGianHoanThanh=form_data['thoiGianHoanThanh'],
        phongCach=form_data['phongCach'],
        ghiChu=form_data.get('ghiChu', ''),
        dia_chi_nhan_hang=form_data['dia_chi_nhan_hang'],
        User_id=customer_profile,
        tiemhoa_id=shop_profile,
        noiDungTuVan='',
    )


def record_payment(order, image_file):
    tt = ThanhToan.objects.create(
        maThanhToan=_short_id('TT'),
        tongTien=(order.nganSach or 0) + (order.phiVanChuyen or 0),
        noiDung=f"{order.maDonHang} Thanh toan hoa",
        hinhAnhBienLai=image_file,
        maDonHang=order,
    )
    order.trangThaiDonHang = 'dang_thuc_hien'
    order.save()
    return tt


def get_or_create_chat(customer_profile, shop_profile):
    chat = PhienChat.objects.filter(
        maKhachHang=customer_profile, maTiemHoa=shop_profile,
    ).first()
    if chat:
        return chat
    return PhienChat.objects.create(
        maPhienChat=_short_id('CHAT'),
        maKhachHang=customer_profile,
        maTiemHoa=shop_profile,
    )


def send_message(chat, sender_user, noi_dung, hinh_anh=None):
    msg = TinNhan.objects.create(
        maTaiKhoan=sender_user,
        noiDung=noi_dung or '',
        hinhAnh=hinh_anh,
        maPhienChat=chat,
    )
    # người gửi mặc định đã đọc tin nhắn của chính mình
    now = timezone.now()
    if sender_user.id == chat.maKhachHang.User_id_id:
        chat.last_read_kh = now
    elif sender_user.id == chat.maTiemHoa.User_id_id:
        chat.last_read_tiem = now
    chat.save(update_fields=['last_read_kh', 'last_read_tiem'])
    return msg


def mark_chat_read(chat, viewer_user):
    """Đánh dấu phiên chat đã đọc cho phía viewer."""
    now = timezone.now()
    if viewer_user.id == chat.maKhachHang.User_id_id:
        chat.last_read_kh = now
        chat.save(update_fields=['last_read_kh'])
    elif viewer_user.id == chat.maTiemHoa.User_id_id:
        chat.last_read_tiem = now
        chat.save(update_fields=['last_read_tiem'])


def chat_unread_count(chat, viewer_user):
    """Số tin nhắn chưa đọc trong phiên cho viewer."""
    if viewer_user.id == chat.maKhachHang.User_id_id:
        last = chat.last_read_kh
        other_id = chat.maTiemHoa.User_id_id
    elif viewer_user.id == chat.maTiemHoa.User_id_id:
        last = chat.last_read_tiem
        other_id = chat.maKhachHang.User_id_id
    else:
        return 0
    qs = chat.messages.filter(maTaiKhoan_id=other_id)
    if last:
        qs = qs.filter(thoiGian__gt=last)
    return qs.count()


def total_chat_unread_for_user(user):
    """Tổng tin nhắn chưa đọc của user (khách hoặc shop) trên mọi phiên."""
    total = 0
    if hasattr(user, 'customer_profile'):
        for c in user.customer_profile.chats.all():
            total += chat_unread_count(c, user)
    if hasattr(user, 'shop_profile'):
        for c in user.shop_profile.chats.all():
            total += chat_unread_count(c, user)
    return total
