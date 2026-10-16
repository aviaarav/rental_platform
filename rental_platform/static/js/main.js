// Common behaviour for every page.
document.addEventListener('DOMContentLoaded', function () {
    // Flash messages disappear automatically after 6 seconds.
    document.querySelectorAll('.alert.auto-dismiss').forEach(function (alertBox) {
        setTimeout(function () {
            var instance = bootstrap.Alert.getOrCreateInstance(alertBox);
            instance.close();
        }, 6000);
    });

    // Image upload: check size and show a small preview.
    document.querySelectorAll('[data-image-input]').forEach(function (input) {
        input.addEventListener('change', function () {
            var preview = document.querySelector('[data-image-preview]');
            var file = input.files && input.files[0];
            if (!file) return;
            if (file.size > 5 * 1024 * 1024) {
                alert('The image must be smaller than 5 MB.');
                input.value = '';
                return;
            }
            if (preview) {
                preview.src = URL.createObjectURL(file);
                preview.classList.remove('d-none');
            }
        });
    });
});