(function () {
    const url = '/customer/notifications.json';
    let dropdown = null;
    let lastItems = [];

    function escapeHtml(s) {
        const d = document.createElement('div'); d.textContent = s; return d.innerHTML;
    }

    function avatarHtml(item) {
        if (item.avatar_url) {
            return `<img src="${item.avatar_url}" class="w-10 h-10 rounded-full object-cover shrink-0">`;
        }
        return `<div class="w-10 h-10 rounded-full bg-[#e695b2] text-white flex items-center justify-center text-sm font-extrabold shrink-0">${escapeHtml(item.avatar_initial || '?')}</div>`;
    }

    function iconBadge(type) {
        if (type === 'chat') return '<span class="text-[10px] px-2 py-0.5 rounded-full bg-pink-100 text-pink-500 font-bold">Tin nhắn</span>';
        if (type === 'quote') return '<span class="text-[10px] px-2 py-0.5 rounded-full bg-yellow-100 text-yellow-700 font-bold">Báo giá</span>';
        if (type === 'order') return '<span class="text-[10px] px-2 py-0.5 rounded-full bg-green-100 text-green-600 font-bold">Đơn hàng</span>';
        return '';
    }

    function renderItems(items) {
        if (!dropdown) return;
        const body = dropdown.querySelector('.notif-body');
        if (!items || items.length === 0) {
            body.innerHTML = '<div class="py-10 text-center text-sm text-gray-400">Chưa có thông báo mới</div>';
            return;
        }
        body.innerHTML = items.map(it => `
            <a href="${it.url}" class="flex items-start gap-3 px-4 py-3 hover:bg-pink-50 border-b border-gray-50 last:border-b-0">
                ${avatarHtml(it)}
                <div class="flex-1 min-w-0">
                    <div class="flex items-center gap-2 mb-0.5">
                        ${iconBadge(it.type)}
                        <span class="text-[10px] text-gray-400">${escapeHtml(it.time || '')}</span>
                    </div>
                    <div class="text-sm font-bold text-gray-700 truncate">${escapeHtml(it.title)}</div>
                    <div class="text-xs text-gray-500 truncate">${escapeHtml(it.preview || '')}</div>
                </div>
                ${it.unread ? `<span class="min-w-[20px] h-5 px-1.5 rounded-full bg-[#e695b2] text-white text-[10px] font-bold flex items-center justify-center">${it.unread}</span>` : ''}
            </a>
        `).join('');
    }

    function ensureDropdown(btn) {
        if (dropdown && document.body.contains(dropdown)) return dropdown;
        dropdown = document.createElement('div');
        dropdown.className = 'fixed hidden z-50 w-80 bg-white rounded-2xl border border-pink-100 shadow-2xl overflow-hidden';
        dropdown.innerHTML = `
            <div class="px-4 py-3 border-b border-gray-100 flex items-center justify-between bg-pink-50">
                <span class="text-sm font-extrabold text-[#c4698b]">Thông báo</span>
                <button type="button" class="notif-close text-gray-400 hover:text-[#c4698b] text-lg leading-none">×</button>
            </div>
            <div class="notif-body max-h-[70vh] overflow-y-auto"></div>
        `;
        document.body.appendChild(dropdown);
        dropdown.querySelector('.notif-close').addEventListener('click', e => {
            e.stopPropagation();
            dropdown.classList.add('hidden');
        });
        return dropdown;
    }

    function positionDropdown(btn) {
        const r = btn.getBoundingClientRect();
        dropdown.style.top = (r.bottom + 8) + 'px';
        dropdown.style.right = (window.innerWidth - r.right) + 'px';
    }

    function toggleDropdown(btn) {
        ensureDropdown(btn);
        const hidden = dropdown.classList.contains('hidden');
        if (hidden) {
            renderItems(lastItems);
            positionDropdown(btn);
            dropdown.classList.remove('hidden');
            fetchAndUpdate();
        } else {
            dropdown.classList.add('hidden');
        }
    }

    function wireBells() {
        document.querySelectorAll('[data-notif-dot]').forEach(span => {
            const btn = span.closest('button');
            if (!btn || btn.dataset.notifWired) return;
            btn.dataset.notifWired = '1';
            btn.addEventListener('click', e => {
                e.preventDefault();
                e.stopPropagation();
                toggleDropdown(btn);
            });
        });
    }

    async function fetchAndUpdate() {
        try {
            const r = await fetch(url, { credentials: 'same-origin' });
            if (!r.ok) return;
            const d = await r.json();
            const total = d.total || 0;
            lastItems = d.items || [];
            document.querySelectorAll('[data-notif-dot]').forEach(el => {
                if (total > 0) {
                    el.textContent = total > 99 ? '99+' : total;
                    el.classList.remove('hidden');
                    el.classList.add('flex');
                } else {
                    el.classList.add('hidden');
                    el.classList.remove('flex');
                }
            });
            if (dropdown && !dropdown.classList.contains('hidden')) {
                renderItems(lastItems);
            }
        } catch (e) {}
    }

    document.addEventListener('click', e => {
        if (dropdown && !dropdown.classList.contains('hidden') &&
            !dropdown.contains(e.target) && !e.target.closest('[data-notif-dot]')) {
            dropdown.classList.add('hidden');
        }
    });
    window.addEventListener('resize', () => {
        if (dropdown && !dropdown.classList.contains('hidden')) {
            const btn = document.querySelector('[data-notif-dot]')?.closest('button');
            if (btn) positionDropdown(btn);
        }
    });

    wireBells();
    fetchAndUpdate();
    setInterval(fetchAndUpdate, 5000);
})();
