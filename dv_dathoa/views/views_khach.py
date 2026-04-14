from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden, JsonResponse
from django.urls import reverse
from django.db.models import Q, Case, When, IntegerField
from django.core.paginator import Paginator

from dv_dathoa.models import (
    TiemHoaProfile, DonHang, DanhGia, PhienChat, TinNhan,
)
from dv_dathoa.forms.forms_khach import (
    RegisterForm, RequestCreateForm, PaymentForm, ReviewForm, MessageForm,
)
from dv_dathoa.services.khach_logic import (
    register_customer, get_or_create_customer_profile, ensure_demo_shop,
    create_order, record_payment, get_or_create_chat, send_message,
    mark_chat_read, total_chat_unread_for_user,
)


# --- 1. TRANG CHỦ ---
def home_view(request):
    if request.user.is_authenticated:
        return redirect('after_login')
    ensure_demo_shop()
    shops = TiemHoaProfile.objects.filter(trangThaiDuyet=1).order_by('-diemTrungBinh')[:6]
    return render(request, 'khach/index.html', {'shops': shops})


# --- 2. XỬ LÝ TÌM KIẾM ---
def _apply_shop_search(qs, query):
    """Tách query thành từng từ và AND — mỗi từ phải khớp ít nhất 1 field."""
    tokens = [t for t in query.split() if t]
    for tok in tokens:
        qs = qs.filter(
            Q(User_id__username__icontains=tok) |
            Q(User_id__first_name__icontains=tok) |
            Q(User_id__last_name__icontains=tok) |
            Q(tiemhoa_id__icontains=tok) |
            Q(the_loai__icontains=tok) |
            Q(moTa__icontains=tok)
        )
    return qs


def search_view(request):
    ensure_demo_shop()
    query = request.GET.get('q', '').strip()
    shops_qs = TiemHoaProfile.objects.filter(trangThaiDuyet=1)
    if query:
        shops_qs = _apply_shop_search(shops_qs, query)
    paginator = Paginator(shops_qs.order_by('-diemTrungBinh'), 6)
    page = paginator.get_page(request.GET.get('page'))
    return render(request, 'khach/search.html', {
        'flower_shops': page.object_list,
        'page_obj': page,
        'paginator': paginator,
        'total': paginator.count,
        'query': query,
    })


# --- 3. CHI TIẾT TIỆM HOA ---
def _group_shop_gallery(shop):
    """Trả về dict {category: [images]} cho template loop."""
    if not shop:
        return {}, []
    grouped = {}
    uncategorized = []
    for img in shop.gallery.all():
        cat = (img.category or '').strip()
        if cat:
            grouped.setdefault(cat, []).append(img.image.url)
        else:
            uncategorized.append(img.image.url)
    return grouped, uncategorized


def detail_view(request, id=None):
    ensure_demo_shop()
    shop = TiemHoaProfile.objects.filter(pk=id).first()
    if request.user.is_authenticated and shop:
        return redirect('detail_logged', id=shop.pk)
    grouped, uncategorized = _group_shop_gallery(shop)
    return render(request, 'khach/detail.html', {
        'id': id, 'shop': shop,
        'gallery_groups': grouped, 'gallery_uncategorized': uncategorized,
    })


@login_required(login_url='login')
def detail_logged_view(request, id=None):
    ensure_demo_shop()
    shop = get_object_or_404(TiemHoaProfile, pk=id)
    grouped, uncategorized = _group_shop_gallery(shop)
    return render(request, 'khach/detail_logged.html', {
        'id': shop.pk, 'shop': shop,
        'gallery_groups': grouped, 'gallery_uncategorized': uncategorized,
    })


# --- 4. AUTH ---
def login_view(request):
    next_url = request.GET.get('next') or request.POST.get('next') or ''
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            get_or_create_customer_profile(user)
            return redirect(next_url or 'after_login')
        messages.error(request, 'Sai tên đăng nhập hoặc mật khẩu')
    return render(request, 'khach/login.html', {'next': next_url})


def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            register_customer(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password'],
                first_name=form.cleaned_data.get('first_name', ''),
                last_name=form.cleaned_data.get('last_name', ''),
                phonenumber=form.cleaned_data.get('phonenumber', ''),
            )
            messages.success(request, 'Đăng ký thành công! Vui lòng đăng nhập.')
            return redirect('login')
        return render(request, 'khach/register.html', {'form': form})
    return render(request, 'khach/register.html')


def logout_view(request):
    logout(request)
    return redirect('home')


# --- 5. CÁC TRANG PHỤ ---
def success_view(request):
    return render(request, 'khach/success.html')


def pending_view(request):
    return render(request, 'khach/pending.html')


@login_required(login_url='login')
def after_login_view(request):
    ensure_demo_shop()
    profile = get_or_create_customer_profile(request.user)
    recent_orders = _visible_orders(profile)[:3]
    shops = TiemHoaProfile.objects.filter(trangThaiDuyet=1).order_by('-diemTrungBinh')[:6]
    return render(request, 'khach/after_login.html', {
        'recent_orders': recent_orders, 'shops': shops,
    })


def search_suggest_view(request):
    ensure_demo_shop()
    q = request.GET.get('q', '').strip()
    if not q:
        return JsonResponse({'results': []})
    shops = _apply_shop_search(
        TiemHoaProfile.objects.filter(trangThaiDuyet=1), q,
    )[:6]
    return JsonResponse({'results': [
        {
            'id': s.pk,
            'name': s.User_id.first_name or s.User_id.username,
            'desc': (s.moTa or '')[:80],
            'url': reverse('detail_logged', args=[s.pk]) if request.user.is_authenticated else reverse('detail', args=[s.pk]),
        } for s in shops
    ]})


def search_landing_view(request):
    query = request.GET.get('q', '').strip()
    if query:
        return redirect(f"{reverse('search')}?q={query}")
    return render(request, 'khach/search_landing.html', {'query': query})


def search_results_view(request):
    return redirect('search')


# --- 6. TẠO YÊU CẦU ---
@login_required(login_url='login')
def request_create_view(request, id=None):
    shop = get_object_or_404(TiemHoaProfile, pk=id)
    profile = get_or_create_customer_profile(request.user)
    if request.method == 'POST':
        form = RequestCreateForm(request.POST)
        if form.is_valid():
            order = create_order(profile, shop, form.cleaned_data)
            return redirect('request_pending', id=order.pk)
        return render(request, 'khach/request_create.html', {
            'id': id, 'shop': shop, 'form': form,
        })
    return render(request, 'khach/request_create.html', {'id': id, 'shop': shop})


@login_required(login_url='login')
def request_pending_view(request, id=None):
    order = get_object_or_404(DonHang, pk=id, User_id__User_id=request.user)
    if order.trangThai == 2:
        return redirect('quote_confirm', id=order.pk)
    return render(request, 'khach/request_pending.html', {
        'id': order.pk, 'order': order,
    })


@login_required(login_url='login')
def order_status_json_view(request, id=None):
    order = get_object_or_404(DonHang, pk=id, User_id__User_id=request.user)
    return JsonResponse({
        'trangThai': order.trangThai,
        'trangThaiDonHang': order.trangThaiDonHang,
        'approved': order.trangThai == 2,
    })


# --- 7. BÁO GIÁ & THANH TOÁN ---
@login_required(login_url='login')
def quote_confirm_view(request, id=None):
    order = DonHang.objects.filter(pk=id, User_id__User_id=request.user).first()
    if not order:
        return redirect('quote_list')
    if order.trangThai == 1:
        return redirect('request_pending', id=order.pk)
    if request.method == 'POST':
        # Khách bấm "Xác nhận báo giá" → chuyển sang Chờ thanh toán
        if order.trangThaiDonHang == 'chon_hoa':
            order.trangThaiDonHang = 'cho_thanh_toan'
            order.save()
        return redirect('quote_list')
    return render(request, 'khach/quote_confirm.html', {
        'id': order.pk, 'order': order,
    })


@login_required(login_url='login')
def quote_list_view(request):
    profile = get_or_create_customer_profile(request.user)
    quotes = profile.orders.filter(trangThaiDonHang='cho_thanh_toan').order_by('-ngayDat')
    paginator = Paginator(quotes, 5)
    page = paginator.get_page(request.GET.get('page'))
    return render(request, 'khach/quote_list.html', {
        'quotes': page.object_list, 'page_obj': page, 'paginator': paginator,
    })


@login_required(login_url='login')
def payment_view(request, id=None):
    order = get_object_or_404(DonHang, pk=id, User_id__User_id=request.user)
    # Phải xác nhận báo giá trước mới vào được payment
    if order.trangThaiDonHang == 'chon_hoa':
        return redirect('quote_confirm', id=order.pk)
    if order.trangThaiDonHang in ('dang_thuc_hien', 'hoan_thanh'):
        return redirect('order_status')
    if request.method == 'POST':
        form = PaymentForm(request.POST, request.FILES)
        if form.is_valid():
            record_payment(order, form.cleaned_data['hinhAnhBienLai'])
            return redirect('order_status')
        return render(request, 'khach/payment.html', {
            'id': order.pk, 'order': order, 'form': form,
            'error': 'Vui lòng tải lên hình ảnh biên lai',
        })
    return render(request, 'khach/payment.html', {'id': order.pk, 'order': order})


# --- 8. ĐƠN HÀNG CỦA TÔI ---
VISIBLE_ORDER_STATUSES = ['dang_thuc_hien', 'hoan_thanh']


def _visible_orders(profile):
    return profile.orders.filter(
        trangThaiDonHang__in=VISIBLE_ORDER_STATUSES
    ).annotate(
        _status_rank=Case(
            When(trangThaiDonHang='dang_thuc_hien', then=0),
            When(trangThaiDonHang='hoan_thanh', then=1),
            default=2, output_field=IntegerField(),
        )
    ).order_by('_status_rank', '-ngayDat')


@login_required(login_url='login')
def order_status_view(request):
    profile = get_or_create_customer_profile(request.user)
    paginator = Paginator(_visible_orders(profile), 3)
    page = paginator.get_page(request.GET.get('page'))
    return render(request, 'khach/order_status.html', {
        'orders': page.object_list,
        'page_obj': page,
        'paginator': paginator,
    })


@login_required(login_url='login')
def order_status_detail_view(request, id=None):
    order = get_object_or_404(DonHang, pk=id, User_id__User_id=request.user)
    if order.trangThaiDonHang == 'hoan_thanh':
        return redirect('order_status_detail_done', id=order.pk)
    profile = order.User_id
    paginator = Paginator(_visible_orders(profile), 3)
    page = paginator.get_page(request.GET.get('page'))
    return render(request, 'khach/order_status_detail.html', {
        'id': order.pk, 'order': order,
        'orders': page.object_list, 'page_obj': page, 'paginator': paginator,
    })


@login_required(login_url='login')
def order_status_detail_done_view(request, id=None):
    order = get_object_or_404(DonHang, pk=id, User_id__User_id=request.user)
    profile = order.User_id
    paginator = Paginator(_visible_orders(profile), 3)
    page = paginator.get_page(request.GET.get('page'))
    review = order.reviews.first()
    return render(request, 'khach/order_status_detail_done.html', {
        'id': order.pk, 'order': order, 'review': review,
        'orders': page.object_list, 'page_obj': page, 'paginator': paginator,
    })


# --- 9. ĐÁNH GIÁ ---
@login_required(login_url='login')
def review_service_view(request, id=None):
    order = get_object_or_404(DonHang, pk=id, User_id__User_id=request.user)
    if order.trangThaiDonHang != 'hoan_thanh':
        return HttpResponseForbidden("Chỉ có thể đánh giá đơn hàng đã hoàn thành.")
    # Không cho đánh giá lại
    if order.reviews.exists():
        return redirect('review_service_done', id=order.pk)
    if request.method == 'POST':
        form = ReviewForm(request.POST, request.FILES)
        if form.is_valid():
            review = form.save(commit=False)
            review.maDonHang = order
            review.save()
            return redirect('review_service_done', id=order.pk)
        return render(request, 'khach/review_service.html', {
            'id': order.pk, 'order': order, 'form': form,
        })
    return render(request, 'khach/review_service.html', {'id': order.pk, 'order': order})


@login_required(login_url='login')
def review_service_done_view(request, id=None):
    order = get_object_or_404(DonHang, pk=id, User_id__User_id=request.user)
    review = order.reviews.first()
    return render(request, 'khach/review_service_done.html', {
        'id': order.pk, 'order': order, 'review': review,
    })


# --- 10. CHAT ---
def _block_self_chat(request, shop):
    """Chặn user tự chat với shop của chính mình."""
    if request.user.id == shop.User_id_id:
        messages.error(request, "Bạn không thể chat với shop của chính mình.")
        return redirect('after_login')
    if request.user.role == 'shop':
        messages.error(request, "Tài khoản chủ tiệm không thể nhắn ở trang khách. Vui lòng đăng nhập tài khoản khách hàng.")
        return redirect('login')
    return None


@login_required(login_url='login')
def chat_kh_view(request, id=None):
    shop = get_object_or_404(TiemHoaProfile, pk=id)
    blocked = _block_self_chat(request, shop)
    if blocked:
        return blocked
    profile = get_or_create_customer_profile(request.user)
    chat = get_or_create_chat(profile, shop)
    if request.method == 'POST':
        form = MessageForm(request.POST, request.FILES)
        if form.is_valid() and (form.cleaned_data.get('noiDung') or form.cleaned_data.get('hinhAnh')):
            msg = send_message(
                chat, request.user,
                form.cleaned_data.get('noiDung') or '',
                form.cleaned_data.get('hinhAnh'),
            )
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'ok': True, 'message': {
                    'id': msg.maTinNhan,
                    'is_me': True,
                    'noiDung': msg.noiDung,
                    'hinhAnh': msg.hinhAnh.url if msg.hinhAnh else '',
                    'thoiGian': msg.thoiGian.strftime('%H:%M'),
                }})
            return redirect('chat_kh', id=shop.pk)
    mark_chat_read(chat, request.user)
    messages_qs = chat.messages.all().order_by('thoiGian')
    return render(request, 'khach/chatbox_kh.html', {
        'id': shop.pk, 'shop': shop, 'chat': chat,
        'messages_list': messages_qs,
    })


@login_required(login_url='login')
def chat_messages_json_view(request, id=None):
    shop = get_object_or_404(TiemHoaProfile, pk=id)
    if request.user.id == shop.User_id_id or request.user.role == 'shop':
        return JsonResponse({'messages': []})
    profile = get_or_create_customer_profile(request.user)
    chat = get_or_create_chat(profile, shop)
    after = request.GET.get('after')
    qs = chat.messages.all().order_by('thoiGian')
    if after:
        try:
            qs = qs.filter(maTinNhan__gt=int(after))
        except ValueError:
            pass
    mark_chat_read(chat, request.user)
    return JsonResponse({'messages': [
        {
            'id': m.maTinNhan,
            'sender_id': m.maTaiKhoan_id,
            'is_me': m.maTaiKhoan_id == request.user.id,
            'noiDung': m.noiDung,
            'hinhAnh': m.hinhAnh.url if m.hinhAnh else '',
            'thoiGian': m.thoiGian.strftime('%H:%M'),
        } for m in qs
    ]})


@login_required(login_url='login')
def notifications_json_view(request):
    """Tổng hợp thông báo cho khách: tin nhắn chưa đọc + cập nhật đơn hàng."""
    from dv_dathoa.services.khach_logic import chat_unread_count
    profile = get_or_create_customer_profile(request.user)

    items = []
    chat_unread = 0

    # 1. Tin nhắn chưa đọc từ từng shop
    for chat in profile.chats.select_related('maTiemHoa__User_id'):
        n = chat_unread_count(chat, request.user)
        if n <= 0:
            continue
        chat_unread += n
        last = chat.messages.order_by('-thoiGian').first()
        preview = (last.noiDung or '[Hình ảnh]') if last else ''
        shop = chat.maTiemHoa
        items.append({
            'type': 'chat',
            'shop_id': shop.pk,
            'title': shop.display_name,
            'preview': preview[:60],
            'unread': n,
            'avatar_url': shop.avatar_url or '',
            'avatar_initial': shop.avatar_initial,
            'url': reverse('chat_kh', args=[shop.pk]),
            'time': last.thoiGian.strftime('%H:%M %d/%m') if last else '',
        })

    # 2. Đơn shop đã báo giá, khách chưa xác nhận
    pending_quotes = DonHang.objects.filter(
        User_id=profile, trangThai=2, trangThaiDonHang='chon_hoa',
    ).select_related('tiemhoa_id__User_id').order_by('-ngayDat')
    for o in pending_quotes:
        shop = o.tiemhoa_id
        items.append({
            'type': 'quote',
            'order_id': o.maDonHang,
            'title': f"{shop.display_name} đã gửi báo giá",
            'preview': f"Đơn #{o.maDonHang} – hãy xác nhận báo giá",
            'avatar_url': shop.avatar_url or '',
            'avatar_initial': shop.avatar_initial,
            'url': reverse('quote_confirm', args=[o.maDonHang]),
            'time': o.ngayDat.strftime('%H:%M %d/%m'),
        })

    # 3. Đơn đang thực hiện / hoàn thành (cập nhật trạng thái từ shop)
    progress = DonHang.objects.filter(
        User_id=profile, trangThaiDonHang__in=['dang_thuc_hien', 'hoan_thanh'],
    ).select_related('tiemhoa_id__User_id').order_by('-ngayDat')[:5]
    for o in progress:
        shop = o.tiemhoa_id
        if o.trangThaiDonHang == 'dang_thuc_hien':
            title = f"Đơn #{o.maDonHang} đang được thực hiện"
            url = reverse('order_status_detail', args=[o.maDonHang])
        else:
            title = f"Đơn #{o.maDonHang} đã hoàn thành"
            url = reverse('order_status_detail_done', args=[o.maDonHang])
        items.append({
            'type': 'order',
            'order_id': o.maDonHang,
            'title': title,
            'preview': f"Từ tiệm {shop.display_name}",
            'avatar_url': shop.avatar_url or '',
            'avatar_initial': shop.avatar_initial,
            'url': url,
            'time': o.ngayDat.strftime('%H:%M %d/%m'),
        })

    order_updates = len(pending_quotes)
    return JsonResponse({
        'chat_unread': chat_unread,
        'order_updates': order_updates,
        'total': chat_unread + order_updates,
        'items': items,
    })
