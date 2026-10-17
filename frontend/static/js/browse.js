// Date inputs: start cannot be in the past, end cannot be before start.
document.addEventListener('DOMContentLoaded', function () {
    var start = document.querySelector('[data-start-date]');
    var end = document.querySelector('[data-end-date]');
    if (!start || !end) return;

    function today() {
        var d = new Date();
        return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0');
    }

    start.min = today();
    end.min = start.value || today();
    start.addEventListener('change', function () {
        end.min = start.value || today();
        if (end.value && end.value < start.value) end.value = start.value;
    });
});