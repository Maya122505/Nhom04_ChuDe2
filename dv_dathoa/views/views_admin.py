from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.db.models import Sum, Q
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from dv_dathoa.models import User, TiemHoaProfile, CustomerProfile, DonHang, ThanhToan

def is_admin(user):
    return user.is_authenticated and (user.role == 'admin' or user.is_superuser)

@ensure_csrf_cookie
def login_admin(request):
    error = None
    if request.user.is_authenticated and is_admin(request.user):
        return redirect('admin_users')

    if request.method == 'POST':
        u = request.POST.get('username')
        p = request.POST.get('password')

        user = authenticate(request, username=u, password=p)
        if user is not None:
            if is_admin(user):
                login(request, user)
                return redirect('admin_users')
            else:
                error = "Tài khoản không có quyền Admin!"
        else:
            error = "Tài khoản hoặc mật khẩu sai!"

    return render(request, 'admin/login_admin.html', {'error': error})


def logout_admin(request):
    logout(request)
    return redirect('login_admin')


# Trang Dashboard
def admin_dashboard(request):
    if not is_admin(request.user):
        return redirect('login_admin')

    from django.db.models import Count
    from django.utils import timezone
    from datetime import timedelta, datetime

    active_tab = request.GET.get('tab', 'doanh_thu')

    # Parse date range (default: last 7 days)
    def parse_date(s):
        try:
            return datetime.strptime(s, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            return None
    today = timezone.localdate()
    date_from = parse_date(request.GET.get('from')) or (today - timedelta(days=6))
    date_to = parse_date(request.GET.get('to')) or today
    if date_from > date_to:
        date_from, date_to = date_to, date_from

    # Scope queryset by range
    dt_start = timezone.make_aware(datetime.combine(date_from, datetime.min.time()))
    dt_end = timezone.make_aware(datetime.combine(date_to, datetime.max.time()))

    # Chỉ tính đơn đã được khách thanh toán (đang thực hiện / hoàn thành) → mới là doanh thu thật
    PAID_STATUSES = ['dang_thuc_hien', 'hoan_thanh']
    orders_qs = DonHang.objects.filter(
        ngayDat__range=(dt_start, dt_end),
        trangThaiDonHang__in=PAID_STATUSES,
    )
    payments_qs = ThanhToan.objects.filter(
        maDonHang__ngayDat__range=(dt_start, dt_end),
        maDonHang__trangThaiDonHang__in=PAID_STATUSES,
    )
    users_qs_range = User.objects.filter(
        date_joined__range=(dt_start, dt_end)
    ).exclude(role='admin').exclude(is_superuser=True)

    total_rev = payments_qs.aggregate(total=Sum('tongTien'))['total'] or 0
    total_orders = orders_qs.count()
    users_count = User.objects.exclude(role='admin').exclude(is_superuser=True).count()
    new_users = users_qs_range.count()

    # Tạo data chart theo ngày
    days = (date_to - date_from).days + 1
    day_list = [date_from + timedelta(days=i) for i in range(days)]

    def bars_for(tab):
        buckets = {d: 0 for d in day_list}
        if tab == 'doanh_thu':
            for p in payments_qs.select_related('maDonHang'):
                d = timezone.localtime(p.maDonHang.ngayDat).date()
                if d in buckets:
                    buckets[d] += float(p.tongTien)
        elif tab == 'don_hang':
            for o in orders_qs:
                d = timezone.localtime(o.ngayDat).date()
                if d in buckets:
                    buckets[d] += 1
        elif tab == 'nguoi_dung':
            for u in users_qs_range:
                d = timezone.localtime(u.date_joined).date()
                if d in buckets:
                    buckets[d] += 1
        values = list(buckets.values())
        max_v = max(values) if values else 0

        def fmt(v):
            if not v:
                return ""
            if tab == 'doanh_thu':
                if v >= 1_000_000:
                    return f"{v/1_000_000:.1f}M"
                if v >= 1_000:
                    return f"{v/1_000:.0f}k"
                return f"{v:.0f}"
            return f"{int(v)}"

        return [{
            'date': d,
            'label': d.strftime('%d/%m'),
            'value': buckets[d],
            'value_text': fmt(buckets[d]),
            'pct': (buckets[d] / max_v * 100) if max_v > 0 else 0,
        } for d in day_list]

    chart_bars = bars_for(active_tab)

    def format_vnd(amount):
        return "{:,.0f}đ".format(amount).replace(',', '.')

    # Top shop theo số đơn đã thanh toán (không tính đơn chưa chốt)
    top_shops_qs = TiemHoaProfile.objects.filter(trangThaiDuyet=1).annotate(
        order_count=Count('orders', filter=Q(orders__trangThaiDonHang__in=PAID_STATUSES)),
        revenue=Sum(
            'orders__payments__tongTien',
            filter=Q(orders__trangThaiDonHang__in=PAID_STATUSES),
        ),
    ).order_by('-order_count', '-revenue')[:5]
    top_shops = [{
        'name': s.User_id.first_name or s.User_id.username,
        'address': s.diaChi,
        'image': s.card_image_url,
        'orders': s.order_count,
        'revenue': format_vnd(s.revenue or 0),
    } for s in top_shops_qs]

    # Hoạt động gần đây: đơn mới + thanh toán mới + shop duyệt + user mới
    recent_events = []
    for o in DonHang.objects.order_by('-ngayDat')[:3]:
        if o.trangThaiDonHang == 'hoan_thanh':
            txt, color = f'Đơn #{o.maDonHang} đã hoàn thành', 'emerald'
        elif o.trangThaiDonHang == 'dang_thuc_hien':
            txt, color = f'Đơn #{o.maDonHang} đang thực hiện', 'blue'
        else:
            txt, color = f'Đơn #{o.maDonHang} — {o.get_trangThaiDonHang_display()}', 'pink'
        recent_events.append({
            'ts': o.ngayDat,
            'text': txt,
            'meta': f'{o.tiemhoa_id.User_id.first_name or o.tiemhoa_id.User_id.username} • {timezone.localtime(o.ngayDat):%d/%m %H:%M}',
            'color': color,
        })
    for p in ThanhToan.objects.select_related('maDonHang').order_by('-maDonHang__ngayDat')[:2]:
        recent_events.append({
            'ts': p.maDonHang.ngayDat,
            'text': f'Đã thanh toán {format_vnd(p.tongTien)} cho đơn #{p.maDonHang.maDonHang}',
            'meta': f'{timezone.localtime(p.maDonHang.ngayDat):%d/%m %H:%M}',
            'color': 'emerald',
        })
    for s in TiemHoaProfile.objects.filter(trangThaiDuyet=1).select_related('User_id').order_by('-User_id__date_joined')[:2]:
        recent_events.append({
            'ts': s.User_id.date_joined,
            'text': f'Tiệm {s.User_id.first_name or s.User_id.username} đã được duyệt',
            'meta': f'{timezone.localtime(s.User_id.date_joined):%d/%m %H:%M}',
            'color': 'pink',
        })
    for u in User.objects.exclude(role='admin').exclude(is_superuser=True).order_by('-date_joined')[:2]:
        recent_events.append({
            'ts': u.date_joined,
            'text': f'{"Tiệm hoa" if u.role == "shop" else "Khách hàng"} {u.username} mới đăng ký',
            'meta': f'{u.email} • {timezone.localtime(u.date_joined):%d/%m %H:%M}',
            'color': 'blue',
        })
    recent_events.sort(key=lambda x: x['ts'], reverse=True)
    recent = recent_events[:6]

    context = {
        'total_revenue': format_vnd(total_rev),
        'total_orders': f"{total_orders:,}",
        'new_users': str(new_users),
        'users_count': f"{users_count:,}",
        'active_tab': active_tab,
        'top_shops': top_shops,
        'recent_activity': recent,
        'date_from': date_from.isoformat(),
        'date_to': date_to.isoformat(),
        'chart_bars': chart_bars,
    }
    return render(request, 'admin/dashboard.html', context)


# Trang Quản lý người dùng
def user_management(request):
    if not is_admin(request.user):
        return redirect('login_admin')

    # 1. Các tiệm chờ duyệt
    pending_tiem = TiemHoaProfile.objects.filter(trangThaiDuyet=0)
    tiems_cho_duyet = []
    for t in pending_tiem:
        ten = (t.User_id.first_name + " " + t.User_id.last_name).strip() or t.User_id.username
        tiems_cho_duyet.append({
            'id': t.User_id.id,
            'ten': ten,
            'chu_tiem': t.tenChuTaiKhoan,
            'ngay_dk': t.User_id.date_joined.strftime("%d/%m/%Y"),
            'status': 'Chờ duyệt',
            'address': t.diaChi,
            'phone': t.User_id.phonenumber or 'N/A',
            'email': t.User_id.email,
            'tax_id': t.maSoThue,
            'bank_account': t.soTaiKhoan,
            'bank_name': t.tenNganHang,
            'account_name': t.tenChuTaiKhoan,
        })

    # 2. Xử lý Search và Filter danh sách chung
    q = (request.GET.get('q') or '').strip().lower()
    role_filter = (request.GET.get('role') or '').strip()
    status_filter = (request.GET.get('status') or '').strip()

    all_users = User.objects.exclude(role='admin').exclude(is_superuser=True).order_by('-date_joined')
    
    khach_hangs = []
    for u in all_users:
        # Xác định logic Hiển thị Role & Status
        display_role = 'Khách hàng' if u.role == 'customer' else 'Chủ tiệm'
        display_status = 'Hoạt động'
        orders_count = 0
        shop_id = None
        
        if u.role == 'shop':
            try:
                prof = getattr(u, 'shop_profile')
                if prof.trangThaiDuyet == 0:
                    display_status = 'Chờ duyệt'
                elif prof.trangThaiDuyet == 2:
                    display_status = 'Bị từ chối'
                orders_count = prof.orders.count()
                shop_id = u.id
                
                # Update Tên thật nếu là Tiệm hoa
                fullname = f"{u.first_name} {u.last_name}".strip()
                if not fullname: fullname = prof.tiemhoa_id
                
            except TiemHoaProfile.DoesNotExist:
                fullname = u.username
        else:
            try:
                prof = getattr(u, 'customer_profile')
                orders_count = prof.orders.count()
                fullname = f"{u.first_name} {u.last_name}".strip()
                if not fullname: fullname = u.username
            except CustomerProfile.DoesNotExist:
                fullname = u.username

        if not u.is_active:
             display_status = 'Bị khóa'

        khach_hangs.append({
            'id': u.id,
            'ten': fullname,
            'email': u.email,
            'role': display_role,
            'status': display_status,
            'phone': u.phonenumber or 'N/A',
            'joined': u.date_joined.strftime("%d/%m/%Y"),
            'orders': f"{orders_count} đơn hàng",
            'shop_id': shop_id,
            'is_active': u.is_active,
        })

    # Lọc Query (In-memory filter mapping the mock UI search pattern)
    filtered = []
    for user_obj in khach_hangs:
        if role_filter and user_obj['role'] != role_filter:
            continue
        if status_filter and user_obj['status'] != status_filter:
            continue
        if q and q not in user_obj['ten'].lower() and q not in user_obj['email'].lower():
            continue
        filtered.append(user_obj)

    paginator = Paginator(filtered, 10)
    page = paginator.get_page(request.GET.get('page'))
    context = {
        'tiems': tiems_cho_duyet,
        'users': page.object_list,
        'page_obj': page,
        'paginator': paginator,
        'total': len(filtered),
        'q': q,
        'role_filter': role_filter,
        'status_filter': status_filter,
    }
    return render(request, 'admin/user_management.html', context)


@require_POST
def toggle_user_active(request, user_id):
    if not is_admin(request.user):
        return redirect('login_admin')
    u = get_object_or_404(User, pk=user_id)
    if u.is_superuser or u.role == 'admin':
        return redirect('admin_users')
    u.is_active = not u.is_active
    u.save()
    return redirect(request.META.get('HTTP_REFERER') or 'admin_users')


def pending_detail(request, shop_id):
    if not is_admin(request.user):
        return redirect('login_admin')

    tiem = get_object_or_404(TiemHoaProfile, User_id=shop_id, trangThaiDuyet=0)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'approve':
            tiem.trangThaiDuyet = 1
            tiem.save()
        elif action == 'reject':
            tiem.trangThaiDuyet = 2
            tiem.save()
        return redirect('admin_users')

    qr_url = ''
    bank_code = getattr(tiem, 'bank_bin', '') or tiem.tenNganHang
    if bank_code and tiem.soTaiKhoan:
        qr_url = f'https://img.vietqr.io/image/{bank_code}-{tiem.soTaiKhoan}-compact.png'
    shop_data = {
        'id': tiem.User_id.id,
        'shop_name': f"{tiem.User_id.first_name} {tiem.User_id.last_name}".strip() or tiem.tiemhoa_id,
        'address': tiem.diaChi,
        'phone': tiem.User_id.phonenumber or 'N/A',
        'email': tiem.User_id.email,
        'tax_id': tiem.maSoThue,
        'bank_account': tiem.soTaiKhoan,
        'bank_name': tiem.tenNganHang,
        'account_name': tiem.tenChuTaiKhoan,
        'mo_ta': tiem.moTa,
        'the_loai': getattr(tiem, 'the_loai', '') or '',
        'logo_url': tiem.logoTiemHoa.url if tiem.logoTiemHoa else '',
        'san_pham_url': tiem.hinhAnhSanPham.url if tiem.hinhAnhSanPham else (getattr(tiem, 'anh_url', '') or ''),
        'qr_url': qr_url,
    }
    return render(request, 'admin/pending_detail.html', {'shop': shop_data})
