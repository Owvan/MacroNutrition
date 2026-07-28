document.addEventListener('DOMContentLoaded', function () {
    const foodModalEl = document.getElementById('addFoodModal');
    if (!foodModalEl) return;

    const foodSourceInput = document.getElementById('food_source');
    const searchInput = document.getElementById('taco_search_input');
    const searchResults = document.getElementById('taco_search_results');
    const selectedFoodBox = document.getElementById('selected_food_box');
    const selectedFoodName = document.getElementById('selected_food_name');
    const selectedFoodCategory = document.getElementById('selected_food_category');
    const selectedFoodSource = document.getElementById('selected_food_source');
    const tacoFoodIdInput = document.getElementById('taco_food_id');
    const amountInput = document.getElementById('amount_g');

    // Barcode Elements
    const barcodeInput = document.getElementById('barcode_input');
    const btnSearchBarcode = document.getElementById('btn_search_barcode');
    const barcodeResultBox = document.getElementById('barcode_result_box');
    const barcodeProductName = document.getElementById('barcode_product_name');
    const barcodeNumberLabel = document.getElementById('barcode_number_label');
    const barcodeFallbackBox = document.getElementById('barcode_fallback_box');
    const barcodeErrorMsg = document.getElementById('barcode_error_msg');
    const fallbackNameInput = document.getElementById('fallback_name_input');
    const fallbackSearchResults = document.getElementById('fallback_search_results');

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
    let fallbackDebounceTimer = null;

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
        
        // Reset Barcode Tab
        if (barcodeInput) barcodeInput.value = '';
        if (barcodeResultBox) barcodeResultBox.classList.add('d-none');
        if (barcodeFallbackBox) barcodeFallbackBox.classList.add('d-none');
        if (fallbackNameInput) fallbackNameInput.value = '';
        if (fallbackSearchResults) {
            fallbackSearchResults.innerHTML = '';
            fallbackSearchResults.classList.add('d-none');
        }

        // Reset Custom Inputs
        if (customNameInput) customNameInput.value = '';
        if (customKcalInput) customKcalInput.value = '250';
        if (customCInput) customCInput.value = '30';
        if (customPInput) customPInput.value = '10';
        if (customFInput) customFInput.value = '10';

        currentSelectedFood = null;

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

    // Autocomplete Search for TACO & TBCA
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
                                searchResults.innerHTML = '<div class="p-3 text-muted text-center small"><i class="bi bi-search me-1"></i> Nenhum alimento encontrado em TACO ou TBCA.</div>';
                                searchResults.classList.remove('d-none');
                            }
                        }
                    })
                    .catch(err => console.error('Erro na busca alimentícia:', err));
            }, 250);
        });
    }

    function renderSearchResults(foods) {
        if (!searchResults) return;
        searchResults.innerHTML = '';

        foods.forEach(food => {
            const sourceLabel = food.source === 'TBCA' ? 'TBCA (USP)' : 'TACO';
            const sourceBadgeClass = food.source === 'TBCA' ? 'bg-primary text-white' : 'bg-teal text-white';

            const item = document.createElement('a');
            item.href = '#';
            item.className = 'list-group-item list-group-item-action p-2 px-3 border-bottom d-flex justify-content-between align-items-center';
            item.innerHTML = `
                <div>
                    <div class="d-flex align-items-center mb-1">
                        <span class="badge ${sourceBadgeClass} fs-7 me-1 py-1 px-2">${sourceLabel}</span>
                        <small class="text-muted fs-7">${food.category}</small>
                    </div>
                    <strong class="d-block text-dark small">${food.name}</strong>
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
        
        if (selectedFoodSource) {
            selectedFoodSource.textContent = food.source === 'TBCA' ? 'TBCA (USP)' : 'TACO';
            selectedFoodSource.className = food.source === 'TBCA' ? 'badge bg-primary text-white me-1' : 'badge bg-teal text-white me-1';
        }

        if (selectedFoodBox) selectedFoodBox.classList.remove('d-none');
        if (searchResults) searchResults.classList.add('d-none');
        if (searchInput) searchInput.value = food.name;

        updateFoodPreview();
    }

    // Barcode Lookup Functionality
    function executeBarcodeSearch() {
        const code = barcodeInput ? barcodeInput.value.trim() : '';
        if (!code) return;

        if (btnSearchBarcode) {
            btnSearchBarcode.disabled = true;
            btnSearchBarcode.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Consultando...';
        }

        fetch(`/api/barcode/search?code=${encodeURIComponent(code)}`)
            .then(res => res.json())
            .then(data => {
                if (btnSearchBarcode) {
                    btnSearchBarcode.disabled = false;
                    btnSearchBarcode.innerHTML = '<i class="bi bi-search me-1"></i> Consultar EAN';
                }

                if (data.found) {
                    // Populate hidden fields
                    if (customNameInput) customNameInput.value = data.name;
                    if (customKcalInput) customKcalInput.value = data.energy_kcal;
                    if (customCInput) customCInput.value = data.carbs_g;
                    if (customPInput) customPInput.value = data.protein_g;
                    if (customFInput) customFInput.value = data.fat_g;

                    if (barcodeProductName) barcodeProductName.textContent = data.name;
                    if (barcodeNumberLabel) barcodeNumberLabel.textContent = `EAN: ${data.barcode}`;

                    if (barcodeResultBox) barcodeResultBox.classList.remove('d-none');
                    if (barcodeFallbackBox) barcodeFallbackBox.classList.add('d-none');

                    updateFoodPreview();
                } else {
                    // Show fallback error box
                    if (barcodeResultBox) barcodeResultBox.classList.add('d-none');
                    if (barcodeErrorMsg) barcodeErrorMsg.textContent = data.error || 'Código de barras não localizado.';
                    if (barcodeFallbackBox) barcodeFallbackBox.classList.remove('d-none');
                    if (fallbackNameInput) fallbackNameInput.focus();
                }
            })
            .catch(err => {
                if (btnSearchBarcode) {
                    btnSearchBarcode.disabled = false;
                    btnSearchBarcode.innerHTML = '<i class="bi bi-search me-1"></i> Consultar EAN';
                }
                if (barcodeErrorMsg) barcodeErrorMsg.textContent = 'Erro de conexão ao consultar código de barras.';
                if (barcodeFallbackBox) barcodeFallbackBox.classList.remove('d-none');
            });
    }

    if (btnSearchBarcode) {
        btnSearchBarcode.addEventListener('click', executeBarcodeSearch);
    }
    if (barcodeInput) {
        barcodeInput.addEventListener('keypress', function (e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                executeBarcodeSearch();
            }
        });
    }

    // Fallback Name Search in Open Food Facts API
    if (fallbackNameInput) {
        fallbackNameInput.addEventListener('input', function () {
            const query = this.value.trim();

            clearTimeout(fallbackDebounceTimer);
            if (query.length < 2) {
                if (fallbackSearchResults) {
                    fallbackSearchResults.innerHTML = '';
                    fallbackSearchResults.classList.add('d-none');
                }
                return;
            }

            fallbackDebounceTimer = setTimeout(() => {
                fetch(`/api/openfoodfacts/search?q=${encodeURIComponent(query)}`)
                    .then(res => res.json())
                    .then(data => {
                        if (data.success && data.foods.length > 0) {
                            renderFallbackResults(data.foods);
                        } else {
                            if (fallbackSearchResults) {
                                fallbackSearchResults.innerHTML = '<div class="p-2 text-muted text-center small"><i class="bi bi-search me-1"></i> Nenhum produto industrializado encontrado na API.</div>';
                                fallbackSearchResults.classList.remove('d-none');
                            }
                        }
                    })
                    .catch(err => console.error('Erro no fallback OFF:', err));
            }, 300);
        });
    }

    function renderFallbackResults(foods) {
        if (!fallbackSearchResults) return;
        fallbackSearchResults.innerHTML = '';

        foods.forEach(food => {
            const item = document.createElement('a');
            item.href = '#';
            item.className = 'list-group-item list-group-item-action p-2 border-bottom d-flex justify-content-between align-items-center';
            item.innerHTML = `
                <div>
                    <strong class="d-block text-dark small">${food.name}</strong>
                    <small class="text-muted fs-7">Open Food Facts</small>
                </div>
                <div class="text-end">
                    <span class="badge bg-primary bg-opacity-10 text-primary fs-7 fw-bold">${Math.round(food.energy_kcal)} kcal</span>
                </div>
            `;

            item.addEventListener('click', function (e) {
                e.preventDefault();

                if (customNameInput) customNameInput.value = food.name;
                if (customKcalInput) customKcalInput.value = food.energy_kcal;
                if (customCInput) customCInput.value = food.carbs_g;
                if (customPInput) customPInput.value = food.protein_g;
                if (customFInput) customFInput.value = food.fat_g;

                if (barcodeProductName) barcodeProductName.textContent = food.name;
                if (barcodeNumberLabel) barcodeNumberLabel.textContent = 'Open Food Facts API';
                if (barcodeResultBox) barcodeResultBox.classList.remove('d-none');
                if (fallbackSearchResults) fallbackSearchResults.classList.add('d-none');

                updateFoodPreview();
            });

            fallbackSearchResults.appendChild(item);
        });

        fallbackSearchResults.classList.remove('d-none');
    }

    function updateFoodPreview() {
        const amount = parseFloat(amountInput.value) || 0;
        const source = foodSourceInput ? foodSourceInput.value : 'taco';

        if (source === 'custom' || source === 'barcode') {
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
