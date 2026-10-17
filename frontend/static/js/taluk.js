// Dependent dropdown: choose District -> Taluk list loads from /api/taluks.
document.addEventListener('DOMContentLoaded', function () {
    var districtSelect = document.querySelector('[data-district-select]');
    var talukSelect = document.querySelector('[data-taluk-select]');
    if (!districtSelect || !talukSelect) return;

    function loadTaluks(selectedTaluk) {
        var district = districtSelect.value;
        talukSelect.innerHTML = '<option value="">Select taluk</option>';
        if (!district) return;
        fetch('/api/taluks?district=' + encodeURIComponent(district))
            .then(function (response) { return response.json(); })
            .then(function (taluks) {
                taluks.forEach(function (name) {
                    var option = document.createElement('option');
                    option.value = name;
                    option.textContent = name;
                    if (name === selectedTaluk) option.selected = true;
                    talukSelect.appendChild(option);
                });
            });
    }

    districtSelect.addEventListener('change', function () { loadTaluks(''); });
    // Keeps the chosen taluk after a failed form submit or when editing.
    if (districtSelect.value) loadTaluks(talukSelect.dataset.selected || '');
});