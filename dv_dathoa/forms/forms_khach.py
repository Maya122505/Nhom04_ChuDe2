from django import forms
from django.contrib.auth import get_user_model
from dv_dathoa.models import DonHang, ThanhToan, DanhGia, TinNhan

User = get_user_model()


import re


class RegisterForm(forms.Form):
    username = forms.CharField(max_length=150)
    email = forms.EmailField()
    first_name = forms.CharField(max_length=150, required=False)
    last_name = forms.CharField(max_length=150, required=False)
    phonenumber = forms.CharField(max_length=20)
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    def clean_username(self):
        u = self.cleaned_data['username'].strip()
        if User.objects.filter(username__iexact=u).exists():
            raise forms.ValidationError("Tên đăng nhập đã tồn tại")
        return u

    def clean_email(self):
        e = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=e).exists():
            raise forms.ValidationError("Email đã được sử dụng")
        return e

    def clean_phonenumber(self):
        p = self.cleaned_data['phonenumber'].strip()
        if not re.fullmatch(r'0\d{9,10}', p):
            raise forms.ValidationError("Số điện thoại phải bắt đầu bằng 0 và có 10–11 chữ số")
        if User.objects.filter(phonenumber=p).exists():
            raise forms.ValidationError("Số điện thoại đã được sử dụng")
        return p

    def clean_password(self):
        pw = self.cleaned_data['password']
        errs = []
        if len(pw) < 8:
            errs.append("ít nhất 8 ký tự")
        if not re.search(r'[A-Z]', pw):
            errs.append("1 chữ IN HOA")
        if not re.search(r'[a-z]', pw):
            errs.append("1 chữ thường")
        if not re.search(r'\d', pw):
            errs.append("1 chữ số")
        if not re.search(r'[^A-Za-z0-9]', pw):
            errs.append("1 ký tự đặc biệt")
        if errs:
            raise forms.ValidationError("Mật khẩu phải có " + ", ".join(errs))
        return pw

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('password') and cleaned.get('confirm_password') \
                and cleaned['password'] != cleaned['confirm_password']:
            self.add_error('confirm_password', "Mật khẩu xác nhận không khớp")
        return cleaned


class RequestCreateForm(forms.ModelForm):
    thoiGianHoanThanh = forms.DateTimeField(
        input_formats=['%Y-%m-%dT%H:%M', '%d/%m/%Y %H:%M', '%d/%m/%Y'],
    )
    ngayGiaoDuKien = forms.DateTimeField(
        input_formats=['%Y-%m-%dT%H:%M', '%d/%m/%Y %H:%M', '%d/%m/%Y'],
        required=False,
    )

    class Meta:
        model = DonHang
        fields = [
            'dipSuDung', 'nganSach', 'thoiGianHoanThanh', 'phongCach',
            'ghiChu', 'dia_chi_nhan_hang',
        ]

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get('ngayGiaoDuKien'):
            cleaned['ngayGiaoDuKien'] = cleaned.get('thoiGianHoanThanh')
        return cleaned


class PaymentForm(forms.ModelForm):
    class Meta:
        model = ThanhToan
        fields = ['hinhAnhBienLai']


class ReviewForm(forms.ModelForm):
    soSao = forms.IntegerField(min_value=1, max_value=5)

    class Meta:
        model = DanhGia
        fields = ['soSao', 'noiDung', 'hinhAnhThucTe']


class MessageForm(forms.ModelForm):
    class Meta:
        model = TinNhan
        fields = ['noiDung', 'hinhAnh']
