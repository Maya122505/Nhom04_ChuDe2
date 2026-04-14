import os
import django
from django.utils import timezone
from datetime import timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Nhom4_ChuDe2.settings')
django.setup()

from dv_dathoa.models import User, CustomerProfile, TiemHoaProfile, PhienChat, TinNhan, DonHang, ThanhToan

def run():
    print("Xóa dữ liệu cũ (reset data)...")
    User.objects.all().delete()
    
    print("1. Tạo Admin...")
    admin = User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    admin.role = 'admin'
    admin.save()
    
    print("2. Tạo Tiệm hoa...")
    # Tiệm hoa 1: Đã duyệt - Lavender Studio
    shop_user1 = User.objects.create_user('lavender', 'lavender@example.com', 'shop123')
    shop_user1.role = 'shop'
    shop_user1.first_name = "Lavender"
    shop_user1.last_name = "Studio"
    shop_user1.save()
    shop1 = TiemHoaProfile.objects.create(
        User_id=shop_user1,
        tiemhoa_id='TH01',
        diaChi='05 Phan Kế Bính, Đà Nẵng',
        moTa='Lavender Studio chuyên cung cấp các loại hoa tươi, hoa thiết kế theo yêu cầu.',
        maSoThue='1234567890',
        trangThaiDuyet=1, # 1 = Đã duyệt
        soTaiKhoan='0123456789',
        tenNganHang='Vietcombank',
        tenChuTaiKhoan='LAVENDER STUDIO'
    )
    
    # Tiệm hoa 2: Chờ duyệt (hoạt động ngầm)
    shop_user2 = User.objects.create_user('hoamai_shop', 'hoamai@example.com', 'shop123')
    shop_user2.role = 'shop'
    shop_user2.save()
    shop2 = TiemHoaProfile.objects.create(
        User_id=shop_user2,
        tiemhoa_id='TH02',
        diaChi='10 Nguyễn Văn Linh, Đà Nẵng',
        moTa='Tiệm hoa Mai - Chuyên hoa sự kiện.',
        maSoThue='0987654321',
        trangThaiDuyet=0, # 0 = Chờ duyệt
        soTaiKhoan='987654321',
        tenNganHang='Techcombank',
        tenChuTaiKhoan='HOA MAI SHOP'
    )
    
    print("3. Tạo Khách hàng...")
    customers = []
    for i in range(1, 4):
        cust_user = User.objects.create_user(f'khachhang{i}', f'kh{i}@example.com', 'khach123')
        cust_user.role = 'customer'
        cust_user.first_name = "Khách"
        cust_user.last_name = str(i)
        cust_user.save()
        cust = CustomerProfile.objects.create(
            User_id=cust_user,
            customer_id=f'KH0{i}',
            dia_chi_mac_dinh=f'12{i} Hoàng Diệu, Đà Nẵng'
        )
        customers.append(cust)
        
    print("4. Tạo Phiên chat và Tin nhắn...")
    # 3 phiên chat của 3 khách hàng với Lavender Studio
    for i, c in enumerate(customers):
        chat = PhienChat.objects.create(
            maPhienChat=f'PC_{c.customer_id}_{shop1.tiemhoa_id}',
            trangThai='mo',
            maKhachHang=c,
            maTiemHoa=shop1
        )
        # Chỉ tạo tin nhắn cho khách hàng 1 (như yêu cầu: 1 dòng dữ liệu tin nhắn)
        if i == 0:
            # Khách hàng nhắn
            TinNhan.objects.create(
                maTaiKhoan=c.User_id,
                noiDung='Chào shop, mình muốn đặt một bó hoa sinh nhật, shop tư vấn giúp mình nhé.',
                maPhienChat=chat
            )
            # Shop trả lời (tạo thành một phiên giao tiếp qua lại)
            TinNhan.objects.create(
                maTaiKhoan=shop1.User_id,
                noiDung='Chào bạn, shop đã nhận được yêu cầu. Bạn cần hoa tông màu gì và ngân sách khoảng bao nhiêu ạ?',
                maPhienChat=chat
            )
            
    print("5. Tạo Đơn hàng và Thanh toán...")
    # Đơn hàng cho Khách hàng 1: Trạng thái đang thực hiện, Shop đã gửi đề xuất -> Khách đã xác nhận -> Đã thanh toán
    don_hang = DonHang.objects.create(
        maDonHang='DH_001',
        trangThaiDonHang='dang_thuc_hien', # Đang thực hiện
        ngayGiaoDuKien=timezone.now() + timedelta(days=1),
        phiVanChuyen=30000,
        noiDungTuVan='Bó hoa hồng phối baby trắng, gói giấy xám sang trọng',
        trangThai=2, # 2 = Xác nhận (đã chốt đề xuất)
        dipSuDung='Sinh nhật',
        nganSach=500000,
        mauSac='Đỏ tía, Trắng',
        thoiGianHoanThanh=timezone.now() + timedelta(days=1),
        phongCach='Sang trọng, hiện đại',
        ghiChu='Giao hàng trước 10h sáng ngày mai.',
        dia_chi_nhan_hang=customers[0].dia_chi_mac_dinh,
        User_id=customers[0],
        tiemhoa_id=shop1
    )
    
    # Dữ liệu thanh toán của đơn hàng 1 (khách hàng đã tải lên biên lai, v.v.)
    ThanhToan.objects.create(
        maThanhToan='TT_DH_001',
        tongTien=530000, # 500k hoa + 30k ship
        noiDung='Thanh toán bó hoa sinh nhật DH_001',
        hinhAnhBienLai='', # Tạm thời để trống trong test data
        maDonHang=don_hang
    )

    print("✅ Đã tạo Mock Data thành công!")
    print("   - 1 Admin (admin/admin123)")
    print("   - 1 Shop 'Lavender' Đã duyệt (lavender/shop123)")
    print("   - 1 Shop 'Hoa Mai' Chờ duyệt (hoamai_shop/shop123)")
    print("   - 3 Khách hàng (khachhang1, khachhang2, khachhang3 / pass: khach123)")
    print("   - 3 Phiên chat, 1 Đơn hàng đang thực hiện, 1 Thanh toán rỗng.")

if __name__ == '__main__':
    run()
