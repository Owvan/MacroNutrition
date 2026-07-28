document.addEventListener('DOMContentLoaded', function () {
    const foodModalEl = document.getElementById('addFoodModal');
    if (!foodModalEl) return;

    const foodSourceInput = document.getElementById('food_source');
    const searchInput = document.getElementById('taco_search_input');
    const searchResults = document.getElementById('taco_search_results');
    const selectedFoodBox = document.getElementById('selected_food_box');
    const selectedFoodName = document.getElementById('selected_food_name');
    const selectedFoodCategory = document.getElementById('selected_food_category');
    const tacoFoodIdInput = document.getElementById('taco_food_id');
    const amountInput = document.getElementById('amount_g');

    // Custom Food Inputs
    const customNameInput = document.getElementById('custom_name');
    const customKcalInput = document.getElementById('custom_kcal');
    const customCInput = document.getElementById('custom_c');
    const customPInput = document.getElementById('custom_p');
    const customFInput = document.getElementById('custom_f');

    // Live Preview Elements inside Modal
    const previewKcal = document.getElementById('preview_kcal');
    const previewCarbs = document.getElementById('preview_carbs');
    const previewProtein = document.getElementById('preview_protein');
    const previewFat = document.getElementById('preview_fat');

    let currentSelectedFood = null;
    let debounceTimer = null;

    window.switchFoodSource = function (type) {
        if (foodSourceInput) foodSourceInput.value = type;
        updateFoodPreview();
    };

    window.openAddFoodModal = function (mealId, mealName) {
        document.getElementById('modal_meal_id').value = mealId;
        document.getElementById('modal_meal_title').textContent = mealName;

        if (foodSourceInput) foodSourceInput.value = 'taco';
        if (searchInput) searchInput.value = '';
        if (searchResults) {
            searchResults.innerHTML = '';
            searchResults.classList.add('d-none');
        }
        if (selectedFoodBox) selectedFoodBox.classList.add('d-none');
        if (tacoFoodIdInput) tacoFoodIdInput.value = '';
        if (amountInput) amountInput.value = 100;
        
        if (customNameInput) customNameInput.value = '';
        if (customKcalInput) customKcalInput.value = '250';
        if (customCInput) customCInput.value = '30';
        if (customPInput) customPInput.value = '10';
        if (customFInput) customFInput.value = '10';

        currentSelectedFood = null;

        // Reset to first tab
        const tacoTabBtn = document.getElementById('taco-tab');
        if (tacoTabBtn && typeof bootstrap !== 'undefined') {
            const tab = new bootstrap.Tab(tacoTabBtn);
            tab.show();
        }

        updateFoodPreview();

        if (typeof bootstrap !== 'undefined') {
            const modal = new bootstrap.Modal(foodModalEl);
            modal.show();
        }
    };

    // TACO Search Autocomplete
    if (searchInput) {
        searchInput.addEventListener('input', function () {
            const query = this.value.trim();

            clearTimeout(debounceTimer);
            if (query.length < 2) {
                if (searchResults) {
                    searchResults.innerHTML = '';
                    searchResults.classList.add('d-none');
                }
                return;
            }

            debounceTimer = setTimeout(() => {
                fetch(`/api/taco/search?q=${encodeURIComponent(query)}`)
                    .then(response => response.json())
                    .then(data => {
                        if (data.success && data.foods.length > 0) {
                            renderSearchResults(data.foods);
                        } else {
                            if (searchResults) {
                                searchResults.innerHTML = '<div class="p-3 text-muted text-center small"><i class="bi bi-search me-1"></i> Nenhum alimento encontrado na Tabela TACO.</div>';
                                searchResults.classList.remove('d-none');
                            }
                        }
                    })
                    .catch(err => console.error('Erro na busca TACO:', err));
            }, 250);
        });
    }

    function renderSearchResults(foods) {
        if (!searchResults) return;
        searchResults.innerHTML = '';

        foods.forEach(food => {
            const item = document.createElement('a');
            item.href = '#';
            item.className = 'list-group-item list-group-item-action p-2 px-3 border-bottom d-flex justify-content-between align-items-center';
            item.innerHTML = `
                <div>
                    <strong class="d-block text-dark small">${food.name}</strong>
                    <small class="text-muted fs-7">${food.category}</small>
                </div>
                <div class="text-end">
                    <span class="badge bg-teal-light text-teal fs-7 fw-bold">${Math.round(food.energy_kcal)} kcal</span>
                    <small class="text-muted d-block fs-7">/ 100g</small>
                </div>
            `;

            item.addEventListener('click', function (e) {
                e.preventDefault();
                selectFood(food);
            });

            searchResults.appendChild(item);
        });

        searchResults.classList.remove('d-none');
    }

    function selectFood(food) {
        currentSelectedFood = food;
        if (tacoFoodIdInput) tacoFoodIdInput.value = food.id;
        if (selectedFoodName) selectedFoodName.textContent = food.name;
        if (selectedFoodCategory) selectedFoodCategory.textContent = food.category;

        if (selectedFoodBox) selectedFoodBox.classList.remove('d-none');
        if (searchResults) searchResults.classList.add('d-none');
        if (searchInput) searchInput.value = food.name;

        updateFoodPreview();
    }

    function updateFoodPreview() {
        const amount = parseFloat(amountInput.value) || 0;
        const source = foodSourceInput ? foodSourceInput.value : 'taco';

        if (source === 'custom') {
            const customKcal = parseFloat(customKcalInput ? customKcalInput.value : 0) || 0;
            const customC = parseFloat(customCInput ? customCInput.value : 0) || 0;
            const customP = parseFloat(customPInput ? customPInput.value : 0) || 0;
            const customF = parseFloat(customFInput ? customFInput.value : 0) || 0;

            const factor = amount / 100.0;
            const kcal = Math.round(customKcal * factor);
            const carbs = (customC * factor).toFixed(1);
            const protein = (customP * factor).toFixed(1);
            const fat = (customF * factor).toFixed(1);

            if (previewKcal) previewKcal.textContent = `${kcal} kcal`;
            if (previewCarbs) previewCarbs.textContent = `${carbs}g`;
            if (previewProtein) previewProtein.textContent = `${protein}g`;
            if (previewFat) previewFat.textContent = `${fat}g`;
            return;
        }

        // TACO Food Mode
        if (!currentSelectedFood || amount <= 0) {
            if (previewKcal) previewKcal.textContent = '0 kcal';
            if (previewCarbs) previewCarbs.textContent = '0g';
            if (previewProtein) previewProtein.textContent = '0g';
            if (previewFat) previewFat.textContent = '0g';
            return;
        }

        const factor = amount / 100.0;
        const kcal = Math.round(currentSelectedFood.energy_kcal * factor);
        const carbs = (currentSelectedFood.carbs_g * factor).toFixed(1);
        const protein = (currentSelectedFood.protein_g * factor).toFixed(1);
        const fat = (currentSelectedFood.fat_g * factor).toFixed(1);

        if (previewKcal) previewKcal.textContent = `${kcal} kcal`;
        if (previewCarbs) previewCarbs.textContent = `${carbs}g`;
        if (previewProtein) previewProtein.textContent = `${protein}g`;
        if (previewFat) previewFat.textContent = `${fat}g`;
    }

    if (amountInput) amountInput.addEventListener('input', updateFoodPreview);
    [customKcalInput, customCInput, customPInput, customFInput].forEach(inp => {
        if (inp) inp.addEventListener('input', updateFoodPreview);
    });
});
