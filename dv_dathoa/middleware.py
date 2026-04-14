"""Middleware tách session theo URL prefix để 3 vai trò (khách / shop / admin)
đăng nhập – đăng xuất độc lập trong cùng 1 trình duyệt.

- /shop/*       → cookie sid_shop
- /admin-sys/*  → cookie sid_admin
- còn lại       → cookie sid_kh
"""
import time
from importlib import import_module

from django.conf import settings
from django.contrib.sessions.exceptions import SessionInterrupted
from django.contrib.sessions.middleware import SessionMiddleware
from django.db.utils import DatabaseError
from django.utils.cache import patch_vary_headers
from django.utils.http import http_date


def cookie_name_for_path(path):
    if path.startswith('/shop/'):
        return 'sid_shop'
    if path.startswith('/admin-sys/'):
        return 'sid_admin'
    return 'sid_kh'


class NamespacedSessionMiddleware(SessionMiddleware):
    def __init__(self, get_response):
        super().__init__(get_response)
        engine = import_module(settings.SESSION_ENGINE)
        self.SessionStore = engine.SessionStore

    def process_request(self, request):
        cookie_name = cookie_name_for_path(request.path)
        request._session_cookie_name = cookie_name
        session_key = request.COOKIES.get(cookie_name)
        request.session = self.SessionStore(session_key)

    def process_response(self, request, response):
        cookie_name = getattr(request, '_session_cookie_name', settings.SESSION_COOKIE_NAME)
        try:
            accessed = request.session.accessed
            modified = request.session.modified
            empty = request.session.is_empty()
        except AttributeError:
            return response

        if cookie_name in request.COOKIES and empty:
            response.delete_cookie(
                cookie_name,
                path=settings.SESSION_COOKIE_PATH,
                domain=settings.SESSION_COOKIE_DOMAIN,
                samesite=settings.SESSION_COOKIE_SAMESITE,
            )
            patch_vary_headers(response, ('Cookie',))
            return response

        if accessed:
            patch_vary_headers(response, ('Cookie',))
        if (modified or settings.SESSION_SAVE_EVERY_REQUEST) and not empty:
            if request.session.get_expire_at_browser_close():
                max_age = None
                expires = None
            else:
                max_age = request.session.get_expiry_age()
                expires_time = time.time() + max_age
                expires = http_date(expires_time)
            if response.status_code != 500:
                try:
                    request.session.save()
                except DatabaseError:
                    raise SessionInterrupted(
                        "The request's session was deleted before the request "
                        "completed. The user may have logged out in a concurrent "
                        "request, for example."
                    )
                response.set_cookie(
                    cookie_name,
                    request.session.session_key,
                    max_age=max_age,
                    expires=expires,
                    domain=settings.SESSION_COOKIE_DOMAIN,
                    path=settings.SESSION_COOKIE_PATH,
                    secure=settings.SESSION_COOKIE_SECURE or None,
                    httponly=settings.SESSION_COOKIE_HTTPONLY or None,
                    samesite=settings.SESSION_COOKIE_SAMESITE,
                )
        return response
