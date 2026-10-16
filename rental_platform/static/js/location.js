// Current location (browser Geolocation API, only after the user allows it).
document.addEventListener('DOMContentLoaded', function () {
    var MESSAGES = {
        1: 'Location permission was denied. Allow location in the browser to see distances.',
        2: 'Your location is not available right now. Please try again.',
        3: 'Finding your location took too long. Please try again.'
    };

    function show(status, message, cssClass) {
        if (!status) return;
        status.textContent = message;
        status.className = 'small ' + cssClass;
    }

    function locate(status, onSuccess, onFinish) {
        if (!navigator.geolocation) {
            show(status, 'Your browser does not support location.', 'text-danger');
            onFinish();
            return;
        }
        show(status, 'Waiting for location permission...', 'text-muted');
        navigator.geolocation.getCurrentPosition(function (position) {
            onSuccess(position.coords.latitude, position.coords.longitude);
        }, function (error) {
            show(status, MESSAGES[error.code] || 'Could not get your location.', 'text-danger');
            onFinish();
        }, { enableHighAccuracy: true, timeout: 15000 });
    }

    // 1) Fills latitude / longitude inputs (add listing forms, browse filter).
    document.querySelectorAll('[data-use-location]').forEach(function (button) {
        button.addEventListener('click', function () {
            var scope = button.closest('form') || document;
            var latInput = scope.querySelector('[data-lat-input]');
            var lngInput = scope.querySelector('[data-lng-input]');
            var status = scope.querySelector('[data-location-status]');
            button.disabled = true;
            locate(status, function (lat, lng) {
                if (latInput) latInput.value = lat.toFixed(6);
                if (lngInput) lngInput.value = lng.toFixed(6);
                show(status, 'Location captured.', 'text-success');
                button.disabled = false;
                if (button.hasAttribute('data-auto-submit') && button.form) button.form.submit();
            }, function () { button.disabled = false; });
        });
    });

    // 2) Resource page: reload the same page with ?lat=&lng= so the server draws the route and distance.
    document.querySelectorAll('[data-locate-redirect]').forEach(function (button) {
        button.addEventListener('click', function () {
            var status = document.querySelector('[data-location-status]');
            button.disabled = true;
            locate(status, function (lat, lng) {
                var url = new URL(window.location.href);
                url.searchParams.set('lat', lat.toFixed(6));
                url.searchParams.set('lng', lng.toFixed(6));
                window.location.href = url.toString();
            }, function () { button.disabled = false; });
        });
    });

    // 3) Browse page: turn location off.
    document.querySelectorAll('[data-clear-location]').forEach(function (button) {
        button.addEventListener('click', function () {
            var form = button.closest('form');
            form.querySelector('[data-lat-input]').value = '';
            form.querySelector('[data-lng-input]').value = '';
            var radius = form.querySelector('[name="radius"]');
            if (radius) radius.value = '';
            form.submit();
        });
    });
}); c