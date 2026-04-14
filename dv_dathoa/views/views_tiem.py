import re
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.db.models import Sum, Avg, Count
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from dv_dathoa.models import User, TiemHoaProfile, DonHang, ThanhToan, PhienChat, TinNhan, DanhGia, ShopGalleryImage

GALLERY_CATEGORIES = [
    ('hoa_cuoi', 'Hoa cưới'),
    ('hoa_khai_truong', 'Hoa khai trương'),
    ('hoa_sinh_nhat', 'Hoa sinh nhật'),
    ('hoa_su_kien', 'Hoa sự kiện'),
    ('hoa_bo_lang', 'Hoa bó/lẵng'),
    ('hoa_dinh_ky', 'Hoa định kỳ'),
]


def is_shop(user):
    return user.is_authenticated and user.role == 'shop'

def get_shop_display_name(profile):
    if not profile: return ""
    user = profile.User_id
    name = f"{user.first_name} {user.last_name}".strip()
    return name if name else profile.tiemhoa_id

def login_shop(request):
    error = None
    if is_shop(request.user):
        if not hasattr(request.user, 'shop_profile'):
            return redirect('register_shop')
        prof = request.user.shop_profile
        if prof.trangThaiDuyet == 1:
            return redirect('vendor_dashboard')
        return redirect('vendor_pending')

    if request.method == 'POST':
        u = request.POST.get('username')
        p = request.POST.get('password')
        user = authenticate(request, username=u, password=p)
        if user is not None:
            if user.role == 'shop':
                try:
                    prof = user.shop_profile
                    login(request, user)
                    if prof.trangThaiDuyet == 1:
                        return redirect('vendor_dashboard')
                    return redirect('vendor_pending')
                except TiemHoaProfile.DoesNotExist:
                    login(request, user)
                    return redirect('register_shop')
            else:
                error = "Tài khoản này không thuộc hệ thống Chủ tiệm!"
        else:
            error = "Tên đăng nhập hoặc mật khẩu không chính xác!"

    return render(request, 'tiem/login_shop.html', {'error': error})


def logout_shop(request):
    logout(request)
    return redirect('login_shop')


def register_tiem(request):
    """Bước 1: tạo tài khoản User với role=shop."""
    if request.method == 'POST':
        data = request.POST
        errors = {}
        username = data.get('username', '').strip()
        email = data.get('email', '').strip().lower()
        phone = data.get('phone', '').strip()
        password = data.get('password', '')
        password_confirm = data.get('password_confirm', '')

        if not username:
            errors['username'] = 'Bắt buộc'
        elif User.objects.filter(username__iexact=username).exists():
            errors['username'] = 'Tên đăng nhập đã tồn tại'
        if not email:
            errors['email'] = 'Bắt buộc'
        elif User.objects.filter(email__iexact=email).exists():
            errors['email'] = 'Email đã được sử dụng'
        if phone and not re.fullmatch(r'0\d{9,10}', phone):
            errors['phone'] = 'SĐT phải bắt đầu bằng 0, 10–11 số'
        elif phone and User.objects.filter(phonenumber=phone).exists():
            errors['phone'] = 'SĐT đã được sử dụng'
        if len(password) < 6:
            errors['password'] = 'Mật khẩu tối thiểu 6 ký tự'
        if password != password_confirm:
            errors['password_confirm'] = 'Mật khẩu xác nhận không khớp'

        if errors:
            return render(request, 'tiem/register.html', {
                'errors': errors, 'values': data,
            })

        user = User.objects.create_user(
            username=username, email=email, password=password, role='shop',
        )
        user.phonenumber = phone
        user.save()
        messages.success(request, 'Tạo tài khoản thành công! Đăng nhập để hoàn thành hồ sơ gian hàng.')
        return redirect('login_shop')

    return render(request, 'tiem/register.html')


def register_shop(request):
    """Bước 2: điền hồ sơ gian hàng."""
    if not request.user.is_authenticated or request.user.role != 'shop':
        return redirect('register_tiem')
    if hasattr(request.user, 'shop_profile') and request.user.shop_profile:
        return redirect('login_shop')

    if request.method == 'POST':
        data = request.POST
        errors = {}
        ten_tiem = data.get('ten_tiem', '').strip()
        dia_chi = data.get('dia_chi', '').strip()
        ma_so_thue = data.get('ma_so_thue', '').strip()
        mo_ta = data.get('mo_ta', '').strip()
        ten_chu_tk = data.get('ten_chu_tk', '').strip()
        so_tk = data.get('so_tk', '').strip()
        ten_ngan_hang = data.get('ten_ngan_hang', '').strip()
        bank_bin = data.get('bank_bin', '').strip()
        the_loai = data.get('the_loai', '')

        if not ten_tiem:
            errors['ten_tiem'] = 'Bắt buộc'
        if not dia_chi:
            errors['dia_chi'] = 'Bắt buộc'
        if not ma_so_thue:
            errors['ma_so_thue'] = 'Bắt buộc'
        if not so_tk or not ten_ngan_hang or not ten_chu_tk:
            errors['bank'] = 'Nhập đủ thông tin ngân hàng'

        if errors:
            return render(request, 'tiem/register_shop.html', {
                'errors': errors, 'values': data,
            })

        tiemhoa_id = re.sub(r'[^a-z0-9]+', '-', ten_tiem.lower()).strip('-') or f'shop-{request.user.pk}'
        # Đảm bảo unique
        base = tiemhoa_id
        i = 2
        while TiemHoaProfile.objects.filter(tiemhoa_id=tiemhoa_id).exists():
            tiemhoa_id = f'{base}-{i}'
            i += 1

        u = request.user
        u.first_name = ten_tiem
        u.save()

        profile = TiemHoaProfile.objects.create(
            User_id=u,
            tiemhoa_id=tiemhoa_id,
            diaChi=dia_chi,
            moTa=mo_ta,
            maSoThue=ma_so_thue,
            trangThaiDuyet=0,
            soTaiKhoan=so_tk,
            tenNganHang=ten_ngan_hang,
            bank_bin=bank_bin,
            tenChuTaiKhoan=ten_chu_tk,
            the_loai=the_loai,
            hinhAnhSanPham=request.FILES.get('anh_san_pham'),
            logoTiemHoa=request.FILES.get('logo'),
            QR_thanh_toan=request.FILES.get('qr'),
        )
        if profile.hinhAnhSanPham:
            profile.anh_url = profile.hinhAnhSanPham.url
            profile.save()

        return redirect('vendor_pending')

    return render(request, 'tiem/register_shop.html')


def vendor_pending(request):
    if not is_shop(request.user):
        return redirect('login_shop')
    if not hasattr(request.user, 'shop_profile'):
        return redirect('register_shop')
    profile = request.user.shop_profile
    if profile.trangThaiDuyet == 1:
        return redirect('vendor_dashboard')
    return render(request, 'tiem/pending.html', {'profile': profile})


def dashboard(request):
    if not is_shop(request.user):
        return redirect('login_shop')
    if not hasattr(request.user, 'shop_profile'):
        return redirect('register_shop')
    tiem_profile = request.user.shop_profile
    if tiem_profile.trangThaiDuyet != 1:
        return redirect('vendor_pending')
        
    shop_orders = DonHang.objects.filter(tiemhoa_id=tiem_profile)
    total_revenue_dict = ThanhToan.objects.filter(maDonHang__in=shop_orders).aggregate(total=Sum('tongTien'))
    total_revenue = total_revenue_dict['total'] or 0
    orders_count = shop_orders.count()
    
    # Giả định: status=1 là chờ xác nhận/báo giá, status=2 là đã xác nhận
    new_requests = shop_orders.filter(trangThai=1).count() 
    
    yeu_cau_cho = shop_orders.filter(trangThai=1)
    yeu_cau_list = []
    for yc in yeu_cau_cho:
        name = f"{yc.User_id.User_id.first_name} {yc.User_id.User_id.last_name}".strip()
        if not name: name = yc.User_id.User_id.username
        yeu_cau_list.append({
            'id': yc.maDonHang,
            'khach': name,
            'ngan_sach': f"{yc.nganSach:,.0f}đ".replace(',', '.'),
            'dip': yc.dipSuDung,
            'status': 'Chờ báo giá'
        })
        
    don_hang_dang_lam = shop_orders.filter(trangThaiDonHang='dang_thuc_hien')
    don_hang_list = []
    status_map = dict(DonHang.DON_HANG_STATUS)
    for dh in don_hang_dang_lam:
        name = f"{dh.User_id.User_id.first_name} {dh.User_id.User_id.last_name}".strip()
        if not name: name = dh.User_id.User_id.username
        don_hang_list.append({
             'id': dh.maDonHang,
             'khach': name,
             'status': status_map.get(dh.trangThaiDonHang, 'Đang tiến hành')
        })
         
    hoan_thanh_count = shop_orders.filter(trangThaiDonHang='hoan_thanh').count()
    dang_thuc_hien_count = shop_orders.filter(trangThaiDonHang='dang_thuc_hien').count()
         
    phien_chats = PhienChat.objects.filter(maTiemHoa=tiem_profile)
    tin_nhan_gan_day = []
    
    # Lấy tin nhắn mới nhất từ tất cả các phiên chat
    all_last_msgs = []
    for phien in phien_chats:
        last_msg = TinNhan.objects.filter(maPhienChat=phien).order_by('-thoiGian').first()
        if last_msg:
            all_last_msgs.append((phien, last_msg))
            
    # Sắp xếp theo thoiGian mới nhất
    all_last_msgs.sort(key=lambda x: x[1].thoiGian, reverse=True)
    
    for phien, last_msg in all_last_msgs[:2]: # Chỉ lấy 2 tin nhắn gần đây nhất
        customer = phien.maKhachHang.User_id
        name = f"{customer.first_name} {customer.last_name}".strip()
        if not name: name = customer.username
        
        tin_nhan_gan_day.append({
            'khach_name': name,
            'noi_dung': last_msg.noiDung,
            'thoi_gian': last_msg.thoiGian.strftime('%H:%M'),
        })

    context = {
        'stats': {
            'revenue': f"{total_revenue:,.0f}đ".replace(',', '.'),
            'orders_count': orders_count,
            'new_requests': new_requests,
            'dang_thuc_hien_count': dang_thuc_hien_count,
            'hoan_thanh_count': hoan_thanh_count,
            'shop_name': get_shop_display_name(tiem_profile),
            'logo_url': tiem_profile.logoTiemHoa.url if tiem_profile.logoTiemHoa else '',
        },
        'yeu_cau_cho': yeu_cau_list,
        'don_hang_dang_lam': don_hang_list,
        'tin_nhan_gan_day': tin_nhan_gan_day
    }
    return render(request, 'tiem/dashboard.html', context)


# Các trang Tùy biến khác có thể chèn decorator tương tự sau:
def manage_orders(request):
    if not is_shop(request.user): return redirect('login_shop')
    
    tiem_profile = request.user.shop_profile
    shop_orders = DonHang.objects.filter(tiemhoa_id=tiem_profile).order_by('-ngayDat')
    
    orders_list = []
    for dh in shop_orders:
        name = f"{dh.User_id.User_id.first_name} {dh.User_id.User_id.last_name}".strip()
        if not name: name = dh.User_id.User_id.username
        
        start_time = dh.ngayDat.strftime('%H:%M - %d/%m/%Y') if dh.ngayDat else 'Chưa cấp'
        sp_name = f"Hoa {dh.dipSuDung}" if dh.dipSuDung else "Đơn cắm hoa"
        
        orders_list.append({
            'id': dh.maDonHang,
            'khach': name,
            'phone': dh.User_id.User_id.phonenumber or '-',
            'sp_name': sp_name,
            'sp_desc': f"Ngân sách: {dh.nganSach:,.0f}đ".replace(',', '.') if dh.nganSach else "Thiết kế riêng",
            'start_time': start_time,
            'status': dh.trangThaiDonHang
        })

    return render(request, 'tiem/manage_orders.html', {'orders': orders_list, 'shop_name': get_shop_display_name(tiem_profile)})

@csrf_exempt
def update_order_status(request):
    if not is_shop(request.user) or request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Unauthorized'}, status=403)
        
    order_id = request.POST.get('order_id')
    new_status = request.POST.get('status')
    
    if not order_id or not new_status:
        return JsonResponse({'status': 'error', 'message': 'Thiếu dữ liệu'}, status=400)
        
    try:
        tiem_profile = request.user.shop_profile
        order = DonHang.objects.get(maDonHang=order_id, tiemhoa_id=tiem_profile)
        if order.trangThaiDonHang == 'hoan_thanh':
            return JsonResponse({'status': 'error', 'message': 'Đơn hàng đã hoàn thành, không thể thay đổi'}, status=400)
            
        order.trangThaiDonHang = new_status
        order.save()
        return JsonResponse({'status': 'success'})
    except DonHang.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Không tìm thấy đơn hàng'}, status=404)


def send_quote(request, req_id):
    if not is_shop(request.user):
        return redirect('login_shop')
    tiem_profile = request.user.shop_profile
    order = get_object_or_404(DonHang, maDonHang=req_id, tiemhoa_id=tiem_profile)
    if request.method == 'POST':
        from decimal import Decimal, InvalidOperation
        action = request.POST.get('action')
        if action == 'approve':
            noi_dung = request.POST.get('noi_dung_tu_van', '').strip()
            try:
                phi_vc = Decimal(request.POST.get('phi_van_chuyen', '0') or '0')
            except InvalidOperation:
                phi_vc = order.phiVanChuyen
            order.noiDungTuVan = noi_dung or order.noiDungTuVan
            order.phiVanChuyen = phi_vc
            order.trangThai = 2
            order.save()
        elif action == 'reject':
            order.trangThai = 0
            order.save()
        return redirect('vendor_quotes')
    return render(request, 'tiem/send_quote.html', {
        'order': order,
        'shop_name': get_shop_display_name(tiem_profile),
    })


def profile(request):
    if not is_shop(request.user):
        return redirect('login_shop')
    if not hasattr(request.user, 'shop_profile'):
        return redirect('register_shop')
    tiem_profile = request.user.shop_profile
    gallery = list(tiem_profile.gallery.all())
    # Back-compat: nếu chưa có gallery records, dùng 4 field cũ
    if not gallery:
        legacy = [tiem_profile.hinhAnhSanPham, tiem_profile.hinhAnhSanPham_2,
                  tiem_profile.hinhAnhSanPham_3, tiem_profile.hinhAnhSanPham_4]
        legacy_urls = [f.url for f in legacy if f]
    else:
        legacy_urls = []
    all_urls = [g.image.url for g in gallery] + legacy_urls
    # Group all images by category for expanded view
    grouped = {}
    others = []
    for img in gallery:
        cat = (img.category or '').strip()
        if cat:
            grouped.setdefault(cat, []).append(img.image.url)
        else:
            others.append(img.image.url)
    others += legacy_urls
    return render(request, 'tiem/profile.html', {
        'shop': tiem_profile,
        'shop_name': get_shop_display_name(tiem_profile),
        'album_preview': all_urls[:4],
        'gallery_groups': grouped,
        'gallery_others': others,
        'gallery_total': len(all_urls),
    })


def profile_edit(request):
    if not is_shop(request.user):
        return redirect('login_shop')
    if not hasattr(request.user, 'shop_profile'):
        return redirect('register_shop')
    tiem_profile = request.user.shop_profile
    if request.method == 'POST':
        user = request.user
        ten_tiem = request.POST.get('ten_tiem', '').strip()
        mo_ta = request.POST.get('mo_ta', '').strip()
        dia_chi = request.POST.get('dia_chi', '').strip()
        the_loai = request.POST.get('the_loai', '').strip()
        so_tk = request.POST.get('so_tk', '').strip()
        ten_ngan_hang = request.POST.get('ten_ngan_hang', '').strip()
        bank_bin = request.POST.get('bank_bin', '').strip()
        ten_chu_tk = request.POST.get('ten_chu_tk', '').strip()

        if ten_tiem:
            user.first_name = ten_tiem
            user.save()
        if dia_chi:
            tiem_profile.diaChi = dia_chi
        if mo_ta:
            tiem_profile.moTa = mo_ta
        if the_loai:
            tiem_profile.the_loai = the_loai
        if so_tk:
            tiem_profile.soTaiKhoan = so_tk
        if ten_ngan_hang:
            tiem_profile.tenNganHang = ten_ngan_hang
        if bank_bin:
            tiem_profile.bank_bin = bank_bin
        if ten_chu_tk:
            tiem_profile.tenChuTaiKhoan = ten_chu_tk
        logo = request.FILES.get('logo')
        if logo:
            tiem_profile.logoTiemHoa = logo
        tiem_profile.save()
        # Xoá ảnh được user đánh dấu
        delete_ids = request.POST.getlist('delete_image_ids')
        if delete_ids:
            ShopGalleryImage.objects.filter(
                shop=tiem_profile, pk__in=delete_ids
            ).delete()
        # Thêm ảnh mới theo từng loại hoa
        for slug, name in GALLERY_CATEGORIES:
            for f in request.FILES.getlist(f'gallery_{slug}'):
                ShopGalleryImage.objects.create(shop=tiem_profile, image=f, category=name)
        # Ảnh chưa phân loại
        for f in request.FILES.getlist('gallery_other'):
            ShopGalleryImage.objects.create(shop=tiem_profile, image=f, category='')
        # Cập nhật anh_url để hiển thị cho khách
        first_img = tiem_profile.gallery.first()
        if first_img:
            tiem_profile.anh_url = first_img.image.url
            tiem_profile.save()
        messages.success(request, 'Đã lưu thay đổi')
        return redirect('vendor_profile')
    # Group existing gallery by category
    grouped = {name: [] for _, name in GALLERY_CATEGORIES}
    others = []
    for img in tiem_profile.gallery.all():
        if img.category in grouped:
            grouped[img.category].append(img)
        else:
            others.append(img)
    sections = [{'slug': slug, 'name': name, 'images': grouped[name]}
                for slug, name in GALLERY_CATEGORIES]
    return render(request, 'tiem/profile_edit.html', {
        'shop': tiem_profile,
        'shop_name': get_shop_display_name(tiem_profile),
        'gallery_sections': sections,
        'gallery_others': others,
    })

def _customer_display(customer_user):
    # Hiển thị theo thứ tự VN: họ + tên (last_name first_name); kèm @username để phân biệt
    full = f"{customer_user.last_name} {customer_user.first_name}".strip()
    if full and full.lower() != customer_user.username.lower():
        return f"{full} (@{customer_user.username})"
    return full or customer_user.username


def _build_chat_list(tiem_profile, viewer_user):
    from dv_dathoa.services.khach_logic import chat_unread_count
    phien_chats = PhienChat.objects.filter(maTiemHoa=tiem_profile)
    items = []
    for phien in phien_chats:
        last_msg = TinNhan.objects.filter(maPhienChat=phien).order_by('-thoiGian').first()
        customer = phien.maKhachHang.User_id
        name = _customer_display(customer)
        if last_msg:
            body = last_msg.noiDung or ('[Hình ảnh]' if last_msg.hinhAnh else '')
            # Phân biệt rõ tin của shop ("Bạn: ...") vs khách
            if last_msg.maTaiKhoan_id == viewer_user.id:
                preview = f"Bạn: {body}"
            else:
                preview = body
            time_text = last_msg.thoiGian.strftime('%H:%M')
            sort_key = last_msg.thoiGian
        else:
            preview = ''
            time_text = ''
            sort_key = phien.thoiGianTao
        items.append({
            'phien_id': phien.maPhienChat,
            'khach_name': name,
            'avatar_letter': (name[:1] or '?').upper(),
            'last_msg': preview,
            'time_text': time_text,
            'unread': chat_unread_count(phien, viewer_user),
            '_sort': sort_key,
        })
    items.sort(key=lambda x: x['_sort'], reverse=True)
    for it in items:
        it.pop('_sort', None)
    return items


def chat(request):
    if not is_shop(request.user):
        return redirect('login_shop')
    if not hasattr(request.user, 'shop_profile'):
        return redirect('register_shop')
    from dv_dathoa.services.khach_logic import mark_chat_read

    tiem_profile = request.user.shop_profile
    chat_list = _build_chat_list(tiem_profile, request.user)

    selected_chat_id = request.GET.get('chat_id')
    active_phien = None
    if selected_chat_id:
        active_phien = PhienChat.objects.filter(
            maPhienChat=selected_chat_id, maTiemHoa=tiem_profile,
        ).first()
    if not active_phien and chat_list:
        active_phien = PhienChat.objects.filter(
            maPhienChat=chat_list[0]['phien_id'], maTiemHoa=tiem_profile,
        ).first()

    active_chat = None
    if active_phien:
        mark_chat_read(active_phien, request.user)
        customer = active_phien.maKhachHang.User_id
        name = _customer_display(customer)
        msgs = TinNhan.objects.filter(maPhienChat=active_phien).order_by('thoiGian')
        active_chat = {
            'phien_id': active_phien.maPhienChat,
            'khach_name': name,
            'avatar_letter': (name[:1] or '?').upper(),
            'messages': msgs,
        }
        # cập nhật unread count = 0 trong list cho item đang active
        for it in chat_list:
            if it['phien_id'] == active_phien.maPhienChat:
                it['unread'] = 0
                break

    logo_url = tiem_profile.logoTiemHoa.url if tiem_profile.logoTiemHoa else ''
    return render(request, 'tiem/chat.html', {
        'chat_list': chat_list,
        'active_chat': active_chat,
        'shop_name': get_shop_display_name(tiem_profile),
        'shop_user_id': request.user.id,
        'logo_url': logo_url,
    })


def chat_messages_json(request, chat_id):
    if not is_shop(request.user):
        return JsonResponse({'error': 'unauthorized'}, status=401)
    tiem_profile = request.user.shop_profile
    phien = get_object_or_404(PhienChat, maPhienChat=chat_id, maTiemHoa=tiem_profile)
    after = request.GET.get('after')
    qs = phien.messages.all().order_by('thoiGian')
    if after:
        try:
            qs = qs.filter(maTinNhan__gt=int(after))
        except ValueError:
            pass
    from dv_dathoa.services.khach_logic import mark_chat_read
    mark_chat_read(phien, request.user)
    return JsonResponse({'messages': [
        {
            'id': m.maTinNhan,
            'is_me': m.maTaiKhoan_id == request.user.id,
            'noiDung': m.noiDung,
            'hinhAnh': m.hinhAnh.url if m.hinhAnh else '',
            'thoiGian': m.thoiGian.strftime('%H:%M'),
        } for m in qs
    ]})


@csrf_exempt
def chat_send(request, chat_id):
    if not is_shop(request.user):
        return JsonResponse({'error': 'unauthorized'}, status=401)
    if request.method != 'POST':
        return JsonResponse({'error': 'method'}, status=405)
    tiem_profile = request.user.shop_profile
    phien = get_object_or_404(PhienChat, maPhienChat=chat_id, maTiemHoa=tiem_profile)
    from dv_dathoa.services.khach_logic import send_message
    text = (request.POST.get('noiDung') or '').strip()
    img = request.FILES.get('hinhAnh')
    if not text and not img:
        return JsonResponse({'error': 'empty'}, status=400)
    msg = send_message(phien, request.user, text, img)
    return JsonResponse({'ok': True, 'message': {
        'id': msg.maTinNhan,
        'is_me': True,
        'noiDung': msg.noiDung,
        'hinhAnh': msg.hinhAnh.url if msg.hinhAnh else '',
        'thoiGian': msg.thoiGian.strftime('%H:%M'),
    }})


def chat_unread_json(request):
    if not is_shop(request.user):
        return JsonResponse({'total': 0, 'sessions': []})
    tiem_profile = request.user.shop_profile
    from dv_dathoa.services.khach_logic import chat_unread_count
    sessions = []
    total = 0
    for phien in PhienChat.objects.filter(maTiemHoa=tiem_profile):
        n = chat_unread_count(phien, request.user)
        if n:
            sessions.append({'phien_id': phien.maPhienChat, 'unread': n})
            total += n
    return JsonResponse({'total': total, 'sessions': sessions})

def quotes(request):
    if not is_shop(request.user):
        return redirect('login_shop')
    tiem_profile = request.user.shop_profile
    pending_qs = DonHang.objects.filter(
        tiemhoa_id=tiem_profile, trangThai=1
    ).order_by('-ngayDat')
    quotes_list = []
    for o in pending_qs:
        cust = o.User_id.User_id
        name = f"{cust.last_name} {cust.first_name}".strip() or cust.username
        quotes_list.append({
            'id': o.maDonHang,
            'khach': name,
            'phone': cust.phonenumber or '-',
            'email': cust.email,
            'dip': o.dipSuDung,
            'phong_cach': o.phongCach,
            'ngan_sach': f"{o.nganSach:,.0f}đ".replace(',', '.'),
            'ngay_giao': o.thoiGianHoanThanh.strftime('%d/%m/%Y %H:%M') if o.thoiGianHoanThanh else '',
            'dia_chi': o.dia_chi_nhan_hang,
            'ghi_chu': o.ghiChu,
            'ngay_dat': o.ngayDat.strftime('%d/%m/%Y %H:%M'),
        })
    return render(request, 'tiem/quotes.html', {
        'quotes': quotes_list,
        'shop_name': get_shop_display_name(tiem_profile),
    })

def _pct_change(cur, prev):
    if not prev:
        return "—" if not cur else "+100%"
    diff = (cur - prev) / prev * 100
    sign = '+' if diff >= 0 else ''
    return f"{sign}{diff:.0f}%"


def _build_revenue_chart(shop_orders_qs, period_start, period_end):
    """Chia period thành N điểm (tối đa 14), tính doanh thu mỗi điểm.
    Trả về dict: {labels, values, points, path_line, path_area}
    """
    from datetime import timedelta
    from decimal import Decimal
    paid_qs = ThanhToan.objects.filter(maDonHang__in=shop_orders_qs)
    total_days = max(1, (period_end.date() - period_start.date()).days + 1)
    buckets = min(total_days, 14)
    bucket_days = total_days / buckets
    labels, values = [], []
    for i in range(buckets):
        a = period_start + timedelta(days=bucket_days * i)
        b = period_start + timedelta(days=bucket_days * (i + 1))
        v = paid_qs.filter(maDonHang__ngayDat__gte=a, maDonHang__ngayDat__lt=b).aggregate(t=Sum('tongTien'))['t'] or Decimal('0')
        values.append(float(v))
        labels.append(a.strftime('%d/%m'))
    # SVG coords 400x160 với padding
    W, H, PAD_L, PAD_R, PAD_T, PAD_B = 400, 160, 10, 10, 10, 20
    inner_w = W - PAD_L - PAD_R
    inner_h = H - PAD_T - PAD_B
    vmax = max(values) if values else 0
    pts = []
    if len(values) == 1:
        xs = [PAD_L + inner_w / 2]
    else:
        xs = [PAD_L + inner_w * i / (len(values) - 1) for i in range(len(values))]
    for x, v in zip(xs, values):
        y = PAD_T + inner_h * (1 - (v / vmax if vmax > 0 else 0))
        pts.append((x, y))
    if pts:
        path_line = "M " + " L ".join(f"{x:.1f} {y:.1f}" for x, y in pts)
        path_area = (
            f"M {pts[0][0]:.1f} {H - PAD_B} " +
            " ".join(f"L {x:.1f} {y:.1f}" for x, y in pts) +
            f" L {pts[-1][0]:.1f} {H - PAD_B} Z"
        )
    else:
        path_line = path_area = ""
    return {
        'labels': labels,
        'values': values,
        'points': [{'x': round(x, 1), 'y': round(y, 1), 'value': v, 'label': lb}
                   for (x, y), v, lb in zip(pts, values, labels)],
        'path_line': path_line,
        'path_area': path_area,
        'max_value': vmax,
    }


def stats(request):
    if not is_shop(request.user): return redirect('login_shop')
    from django.utils import timezone
    from datetime import datetime, timedelta
    from decimal import Decimal
    tiem_profile = request.user.shop_profile
    base_qs = DonHang.objects.filter(tiemhoa_id=tiem_profile, trangThaiDonHang='hoan_thanh')

    month_filter = request.GET.get('month', '')
    now = timezone.localtime()
    if month_filter:
        try:
            y, m = map(int, month_filter.split('-'))
            period_start = timezone.make_aware(datetime(y, m, 1))
            if m == 12:
                period_end = timezone.make_aware(datetime(y + 1, 1, 1)) - timedelta(seconds=1)
            else:
                period_end = timezone.make_aware(datetime(y, m + 1, 1)) - timedelta(seconds=1)
            display_month = f"Tháng {m}, {y}"
        except (ValueError, TypeError):
            month_filter = ''
    if not month_filter:
        # Mặc định: 30 ngày gần nhất
        period_end = now
        period_start = now - timedelta(days=29)
        display_month = "30 ngày qua"

    shop_orders = base_qs.filter(ngayDat__gte=period_start, ngayDat__lte=period_end)
    prev_span = period_end - period_start
    prev_start = period_start - prev_span - timedelta(seconds=1)
    prev_end = period_start - timedelta(seconds=1)
    prev_orders = base_qs.filter(ngayDat__gte=prev_start, ngayDat__lte=prev_end)

    total_orders = shop_orders.count()
    prev_total_orders = prev_orders.count()
    total_revenue = ThanhToan.objects.filter(maDonHang__in=shop_orders).aggregate(t=Sum('tongTien'))['t'] or Decimal('0')
    prev_revenue = ThanhToan.objects.filter(maDonHang__in=prev_orders).aggregate(t=Sum('tongTien'))['t'] or Decimal('0')
    avg_rating = round(DanhGia.objects.filter(maDonHang__in=shop_orders).aggregate(a=Avg('soSao'))['a'] or 0.0, 1)
    prev_avg = round(DanhGia.objects.filter(maDonHang__in=prev_orders).aggregate(a=Avg('soSao'))['a'] or 0.0, 1)

    chart = _build_revenue_chart(shop_orders, period_start, period_end)

    revenue_delta = _pct_change(float(total_revenue), float(prev_revenue))
    orders_delta = _pct_change(total_orders, prev_total_orders)
    rating_delta = f"{avg_rating - prev_avg:+.1f}" if prev_avg else "—"

    # Recent completed orders
    hoan_thanh_qs = shop_orders.order_by('-ngayDat')[:5]
    completed_orders = []
    status_map = dict(DonHang.DON_HANG_STATUS)
    for dh in hoan_thanh_qs:
        name = f"{dh.User_id.User_id.first_name} {dh.User_id.User_id.last_name}".strip()
        if not name: name = dh.User_id.User_id.username
        
        ngay_tt = dh.ngayDat.strftime('%d/%m/%Y, %H:%M') if dh.ngayDat else ''
        tong_tien_obj = ThanhToan.objects.filter(maDonHang=dh).aggregate(t=Sum('tongTien'))
        tong_tien = tong_tien_obj['t'] or 0
        
        completed_orders.append({
            'id': dh.maDonHang,
            'khach': name,
            'ngay_thanh_toan': ngay_tt,
            'tong_tien': f"{tong_tien:,.0f}đ".replace(',', '.'),
            'status': status_map.get(dh.trangThaiDonHang, 'Hoàn thành')
        })

    # Phân loại thiết kế — tính dash-offset luỹ kế cho donut
    categories_qs = shop_orders.values('dipSuDung').annotate(count=Count('dipSuDung')).order_by('-count')
    category_list = []
    colors = ['#F2789F', '#F7B5C8', '#FDE2EB', '#E8C5D8', '#FBCFE8']
    cumulative = 0
    for i, cat in enumerate(categories_qs):
        dip = cat['dipSuDung'] or 'Khác'
        count = cat['count']
        percent = (count / total_orders * 100) if total_orders > 0 else 0
        category_list.append({
            'name': dip,
            'count': count,
            'percent': round(percent, 1),
            'dash': round(percent, 2),
            'offset': -round(cumulative, 2),
            'color': colors[i % len(colors)],
        })
        cumulative += percent
        
    # Phản hồi từ khách hàng
    reviews_qs = DanhGia.objects.filter(maDonHang__in=shop_orders).order_by('-ngayDanhGia')[:3]
    recent_reviews = []
    for rv in reviews_qs:
        customer = rv.maDonHang.User_id.User_id
        name = f"{customer.first_name} {customer.last_name}".strip() or customer.username
        time_text = rv.ngayDanhGia.strftime('%d/%m, %H:%M')
        initials = ''.join([part[0] for part in name.split()[:2]]).upper() if name else 'C'
        
        recent_reviews.append({
            'name': name,
            'initials': initials,
            'time_text': f"{time_text} • Đơn #{rv.maDonHang.maDonHang}",
            'rating': range(rv.soSao),
            'rating_empty': range(5 - rv.soSao),
            'content': rv.noiDung
        })

    context = {
        'stats': {
            'revenue': f"{total_revenue:,.0f}đ".replace(',', '.'),
            'orders_count': total_orders,
            'avg_rating': avg_rating,
            'revenue_delta': revenue_delta,
            'orders_delta': orders_delta,
            'rating_delta': rating_delta,
        },
        'completed_orders': completed_orders,
        'category_list': category_list,
        'recent_reviews': recent_reviews,
        'month_filter': month_filter,
        'display_month': display_month,
        'shop_name': get_shop_display_name(tiem_profile),
        'chart': chart,
        'last_updated': now.strftime('%H:%M, %d/%m/%Y'),
    }

    return render(request, 'tiem/stats.html', context)

def order_detail(request, order_id):
    if not is_shop(request.user):
        return redirect('login_shop')
    tiem_profile = request.user.shop_profile
    order = get_object_or_404(DonHang, maDonHang=order_id, tiemhoa_id=tiem_profile)
    cust = order.User_id.User_id
    payment = order.payments.first()
    context = {
        'order': order,
        'customer_name': f"{cust.last_name} {cust.first_name}".strip() or cust.username,
        'customer_phone': cust.phonenumber or '-',
        'customer_email': cust.email,
        'payment': payment,
        'total': (order.nganSach or 0) + (order.phiVanChuyen or 0),
        'shop_name': get_shop_display_name(tiem_profile),
    }
    return render(request, 'tiem/order_detail.html', context)
