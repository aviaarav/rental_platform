// Booking request page: live route map, distance and cost estimate (no reload needed).
document.addEventListener('DOMContentLoaded', function () {
    var form = document.querySelector('[data-request-form]');
    if (!form) return;

    var resLat = parseFloat(form.dataset.resourceLat);
    var resLng = parseFloat(form.dataset.resourceLng);
    var hasResource = isFinite(resLat) && isFinite(resLng);
    var price = parseFloat(form.dataset.price) || 0;
    var deposit = parseFloat(form.dataset.deposit) || 0;
    var perHour = form.dataset.chargeType === 'Per Hour';
    var isEquipment = form.dataset.kind === 'equipment';

    var latInput = form.querySelector('[data-lat-input]');
    var lngInput = form.querySelector('[data-lng-input]');
    var mapBox = document.querySelector('[data-route-map]');
    var coordsText = document.querySelector('[data-route-coords]');
    var distText = document.querySelector('[data-route-distance]');
    var captured = document.querySelector('[data-location-captured]');
    var estimate = document.querySelector('[data-estimate]');

    function valid(lat, lng) {
        return isFinite(lat) && isFinite(lng) && Math.abs(lat) <= 90 && Math.abs(lng) <= 180;
    }

    // Same maths as app/utils/geo.py so the numbers match the server.
    function haversineKm(lat1, lng1, lat2, lng2) {
        var r = 6371.0088, toRad = Math.PI / 180;
        var dPhi = (lat2 - lat1) * toRad, dLambda = (lng2 - lng1) * toRad;
        var a = Math.sin(dPhi / 2) * Math.sin(dPhi / 2)
              + Math.cos(lat1 * toRad) * Math.cos(lat2 * toRad) * Math.sin(dLambda / 2) * Math.sin(dLambda / 2);
        return Math.round(2 * r * Math.asin(Math.sqrt(a)) * 10) / 10;
    }

    function routePoints(lat1, lng1, lat2, lng2) {
        var width = 420, height = 200, pad = 55;
        var midLat = ((lat1 + lat2) / 2) * Math.PI / 180;
        var dx = (lng2 - lng1) * Math.cos(midLat), dy = lat2 - lat1;
        var cx = width / 2, cy = height / 2;
        if (Math.abs(dx) < 1e-9 && Math.abs(dy) < 1e-9) return [cx - 40, cy, cx + 40, cy];
        var sx = Math.abs(dx) > 1e-9 ? (width - 2 * pad) / Math.abs(dx) : Infinity;
        var sy = Math.abs(dy) > 1e-9 ? (height - 2 * pad) / Math.abs(dy) : Infinity;
        var scale = Math.min(sx, sy);
        var shiftX = dx * scale, shiftY = -dy * scale;
        return [cx - shiftX / 2, cy - shiftY / 2, cx + shiftX / 2, cy + shiftY / 2];
    }

    function mapSvg(p, distance, labelB) {
        var mx = (p[0] + p[2]) / 2, my = (p[1] + p[3]) / 2;
        return '<svg viewBox="0 0 420 200" class="route-map" role="img" aria-label="Route, ' + distance + '">' +
            '<rect width="420" height="200" rx="10" fill="#e3eefe"/>' +
            '<rect x="16" y="14" width="74" height="40" rx="6" fill="#cfe0fb"/><rect x="330" y="14" width="74" height="30" rx="6" fill="#cfe0fb"/>' +
            '<rect x="20" y="150" width="60" height="36" rx="6" fill="#cfe0fb"/><rect x="300" y="146" width="96" height="40" rx="6" fill="#cfe0fb"/>' +
            '<line x1="0" y1="100" x2="420" y2="100" stroke="#fff" stroke-width="7"/><line x1="160" y1="0" x2="160" y2="200" stroke="#fff" stroke-width="7"/><line x1="280" y1="0" x2="280" y2="200" stroke="#fff" stroke-width="4"/>' +
            '<line x1="' + p[0] + '" y1="' + p[1] + '" x2="' + p[2] + '" y2="' + p[3] + '" stroke="#0d6efd" stroke-width="3" stroke-dasharray="8 6"/>' +
            '<circle cx="' + p[0] + '" cy="' + p[1] + '" r="10" fill="#0d6efd"/><circle cx="' + p[0] + '" cy="' + p[1] + '" r="4" fill="#fff"/>' +
            '<text x="' + p[0] + '" y="' + (p[1] + 26) + '" text-anchor="middle" font-size="11" font-weight="700" fill="#0a4cb8">You</text>' +
            '<circle cx="' + p[2] + '" cy="' + p[3] + '" r="10" fill="#dc3545"/><circle cx="' + p[2] + '" cy="' + p[3] + '" r="4" fill="#fff"/>' +
            '<text x="' + p[2] + '" y="' + (p[3] + 26) + '" text-anchor="middle" font-size="11" font-weight="700" fill="#dc3545">' + labelB + '</text>' +
            '<rect x="' + (mx - 36) + '" y="' + (my - 28) + '" width="72" height="20" rx="10" fill="#fff" stroke="#0d6efd"/>' +
            '<text x="' + mx + '" y="' + (my - 14) + '" text-anchor="middle" font-size="11" font-weight="700" fill="#0d6efd">' + distance + '</text></svg>';
    }

    function placeholder(text) {
        return '<div class="map-placeholder"><i class="bi bi-geo-alt"></i><span>' + text + '</span></div>';
    }

    function updateRoute() {
        if (!mapBox) return;
        var lat = parseFloat(latInput.value), lng = parseFloat(lngInput.value);
        if (!hasResource) {
            mapBox.innerHTML = placeholder('The owner has not shared the location of this listing, so distance cannot be shown.');
            return;
        }
        if (!valid(lat, lng)) {
            mapBox.innerHTML = placeholder('Use My Current Location to see the route and distance.');
            if (captured) captured.classList.add('d-none');
            if (coordsText) coordsText.textContent = '';
            if (distText) distText.textContent = '';
            return;
        }
        var km = haversineKm(lat, lng, resLat, resLng);
        mapBox.innerHTML = mapSvg(routePoints(lat, lng, resLat, resLng), km + ' km', isEquipment ? 'Resource' : 'Professional');
        if (coordsText) coordsText.textContent = 'You ' + lat.toFixed(4) + ', ' + lng.toFixed(4) + '  to  ' + (isEquipment ? 'Resource' : 'Professional') + ' ' + resLat.toFixed(4) + ', ' + resLng.toFixed(4);
        if (distText) distText.textContent = 'Distance: ' + km + ' km';
        if (captured) captured.classList.remove('d-none');
    }

    function money(n) { return 'Rs. ' + Math.round(n).toLocaleString('en-IN'); }

    function updateEstimate() {
        if (!estimate) return;
        var start = form.querySelector('[name="start_date"]').value;
        var end = form.querySelector('[name="end_date"]').value;
        var days = 0;
        if (start && end) {
            days = Math.round((new Date(end) - new Date(start)) / 86400000) + 1;
            if (!(days > 0)) days = 0;
        }
        var lines = [], total = 0;
        if (isEquipment) {
            var rent = days * price;
            lines.push(['Rental: ' + days + ' day' + (days === 1 ? '' : 's') + ' x Rs. ' + price, money(rent)]);
            if (deposit > 0) lines.push(['Security deposit (refundable)', money(deposit)]);
            total = rent + deposit;
        } else {
            var hoursInput = form.querySelector('[name="duration_hours"]');
            var hours = hoursInput ? parseInt(hoursInput.value, 10) || 0 : 0;
            var charge = perHour ? hours * price * days : days * price;
            lines.push([(perHour ? 'Charge: ' + hours + ' hour' + (hours === 1 ? '' : 's') + ' x Rs. ' + price + (days > 1 ? ' x ' + days + ' days' : '')
                                 : 'Charge: ' + days + ' day' + (days === 1 ? '' : 's') + ' x Rs. ' + price), money(charge)]);
            lines.push(['Final amount is settled with the professional', '']);
            total = charge;
        }
        estimate.innerHTML = lines.map(function (l) {
            return '<div class="line"><span>' + l[0] + '</span><span>' + l[1] + '</span></div>';
        }).join('') + '<div class="total"><span>Estimated total</span><span>' + money(total) + '</span></div>';
    }

    ['input', 'change'].forEach(function (event) {
        form.addEventListener(event, function () { updateRoute(); updateEstimate(); });
    });
    updateRoute();
    updateEstimate();
});
