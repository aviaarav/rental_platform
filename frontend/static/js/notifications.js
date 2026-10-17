// Unread notifications: keeps the navbar badge current and pops up a toast for each new one.
document.addEventListener('DOMContentLoaded', function () {
    var container = document.querySelector('[data-notification-toasts]');
    if (!container) return;
    var url = container.getAttribute('data-unread-url');
    var badge = document.querySelector('[data-unread-badge]');
    var POLL_MS = 30000;

    // Ids already shown as a toast in this browser tab, so a page reload does not repeat them.
    var seen = {};
    try { seen = JSON.parse(sessionStorage.getItem('seenNotifications') || '{}'); } catch (e) { seen = {}; }

    function remember() {
        try { sessionStorage.setItem('seenNotifications', JSON.stringify(seen)); } catch (e) { /* ignore */ }
    }

    function updateBadge(count) {
        if (!badge) return;
        badge.textContent = count;
        badge.classList.toggle('d-none', count === 0);
    }

    // A short two-tone chime, generated in the browser so no audio file is needed.
    // Browsers only allow sound after the user has interacted with the page; failures are ignored.
    function chime() {
        try {
            var Ctx = window.AudioContext || window.webkitAudioContext;
            if (!Ctx) return;
            var ctx = new Ctx();
            [[880, 0], [1175, 0.14]].forEach(function (note) {
                var osc = ctx.createOscillator(), gain = ctx.createGain();
                osc.type = 'sine';
                osc.frequency.value = note[0];
                gain.gain.setValueAtTime(0.0001, ctx.currentTime + note[1]);
                gain.gain.exponentialRampToValueAtTime(0.18, ctx.currentTime + note[1] + 0.02);
                gain.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + note[1] + 0.25);
                osc.connect(gain).connect(ctx.destination);
                osc.start(ctx.currentTime + note[1]);
                osc.stop(ctx.currentTime + note[1] + 0.3);
            });
        } catch (e) { /* no sound */ }
    }

    function showToast(item) {
        var toast = document.createElement('div');
        toast.className = 'toast toast-rs';
        toast.setAttribute('role', 'status');
        toast.innerHTML =
            '<div class="toast-body">' +
            '<div class="d-flex justify-content-between align-items-start gap-2">' +
            '<div class="toast-title"></div>' +
            '<button type="button" class="btn-close btn-sm" data-bs-dismiss="toast" aria-label="Close"></button></div>' +
            '<div class="small text-muted toast-message"></div></div>';
        toast.querySelector('.toast-title').textContent = item.title;
        var body = toast.querySelector('.toast-body');
        body.querySelector('.toast-message').textContent = item.message;
        chime();
        if (item.link) {
            // The link marks the notification read on the server, so it is a POST form.
            var form = document.createElement('form');
            form.method = 'post';
            form.action = item.link;
            form.className = 'mt-1';
            var button = document.createElement('button');
            button.className = 'btn btn-link btn-sm p-0';
            button.textContent = 'Open';
            form.appendChild(button);
            body.appendChild(form);
        }
        container.appendChild(toast);
        toast.addEventListener('hidden.bs.toast', function () { toast.remove(); });
        bootstrap.Toast.getOrCreateInstance(toast, { delay: 8000 }).show();
    }

    function poll() {
        fetch(url, { headers: { 'Accept': 'application/json' }, credentials: 'same-origin' })
            .then(function (response) { return response.ok ? response.json() : null; })
            .then(function (data) {
                if (!data) return;
                updateBadge(data.count);
                data.items.forEach(function (item) {
                    if (seen[item.id]) return;
                    seen[item.id] = true;
                    showToast(item);
                });
                remember();
            })
            .catch(function () { /* offline or logged out: try again next time */ });
    }

    poll();
    setInterval(poll, POLL_MS);
});
