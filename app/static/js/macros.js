document.addEventListener('DOMContentLoaded', function () {
    const macroForm = document.getElementById('macro-form');
    if (!macroForm) return;

    const targetCalInput = document.getElementById('target_calories');
    const carbPctInput = document.getElementById('carb_pct');
    const proteinPctInput = document.getElementById('protein_pct');
    const fatPctInput = document.getElementById('fat_pct');

    const carbRange = document.getElementById('carb_range');
    const proteinRange = document.getElementById('protein_range');
    const fatRange = document.getElementById('fat_range');

    const presetSelect = document.getElementById('preset_select');
    const totalPctBadge = document.getElementById('total-pct-badge');

    // Display elements for grams & kcal
    const carbGramsEl = document.getElementById('carb-grams');
    const carbKcalEl = document.getElementById('carb-kcal');
    const proteinGramsEl = document.getElementById('protein-grams');
    const proteinKcalEl = document.getElementById('protein-kcal');
    const fatGramsEl = document.getElementById('fat-grams');
    const fatKcalEl = document.getElementById('fat-kcal');

    // Modal elements
    const customMacroModalEl = document.getElementById('customMacroModal');
    let customModal = null;
    if (customMacroModalEl && typeof bootstrap !== 'undefined') {
        customModal = new bootstrap.Modal(customMacroModalEl);
    }

    const modalCarbInput = document.getElementById('modal_carb');
    const modalProteinInput = document.getElementById('modal_protein');
    const modalFatInput = document.getElementById('modal_fat');
    const modalTotalBadge = document.getElementById('modal-total-pct-badge');
    const modalErrorMsg = document.getElementById('modal-error-msg');
    const btnApplyModal = document.getElementById('btn-apply-modal-custom');

    // Chart Canvas
    const canvas = document.getElementById('macroChart');
    let macroChart = null;

    if (canvas && typeof Chart !== 'undefined') {
        const ctx = canvas.getContext('2d');
        macroChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Carboidratos (g)', 'Proteínas (g)', 'Gorduras (g)'],
                datasets: [{
                    data: [250, 100, 66],
                    backgroundColor: [
                        '#0d9488', // Teal (Carbs)
                        '#3b82f6', // Blue (Protein)
                        '#f59e0b'  // Amber/Gold (Fats)
                    ],
                    borderWidth: 3,
                    borderColor: '#ffffff',
                    hoverOffset: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            font: { family: 'Inter', size: 13, weight: '500' },
                            padding: 16
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function (context) {
                                const label = context.label || '';
                                const value = context.raw || 0;
                                return ` ${label}: ${value}g`;
                            }
                        }
                    }
                },
                cutout: '65%'
            }
        });
    }

    const inputs = {
        carb: carbPctInput,
        protein: proteinPctInput,
        fat: fatPctInput
    };

    const ranges = {
        carb: carbRange,
        protein: proteinRange,
        fat: fatRange
    };

    let isBalancing = false;

    function autoBalanceSliders(changedType, newValue) {
        if (isBalancing) return;
        isBalancing = true;

        newValue = Math.max(0, Math.min(100, parseFloat(newValue) || 0));

        let otherTypes = [];
        if (changedType === 'carb') otherTypes = ['protein', 'fat'];
        else if (changedType === 'protein') otherTypes = ['carb', 'fat'];
        else if (changedType === 'fat') otherTypes = ['carb', 'protein'];

        const valOther1 = parseFloat(inputs[otherTypes[0]].value) || 0;
        const valOther2 = parseFloat(inputs[otherTypes[1]].value) || 0;
        const sumOthers = valOther1 + valOther2;
        const remaining = 100 - newValue;

        let newOther1 = 0;
        let newOther2 = 0;

        if (sumOthers > 0) {
            newOther1 = Math.round(valOther1 * (remaining / sumOthers));
            newOther2 = remaining - newOther1;
        } else {
            newOther1 = Math.round(remaining / 2);
            newOther2 = remaining - newOther1;
        }

        newOther1 = Math.max(0, Math.min(100, newOther1));
        newOther2 = Math.max(0, Math.min(100, newOther2));

        inputs[changedType].value = newValue;
        ranges[changedType].value = newValue;

        inputs[otherTypes[0]].value = newOther1;
        ranges[otherTypes[0]].value = newOther1;

        inputs[otherTypes[1]].value = newOther2;
        ranges[otherTypes[1]].value = newOther2;

        updateMacroCalculations();
        isBalancing = false;
    }

    function updateMacroCalculations() {
        const totalCalories = parseFloat(targetCalInput.value) || 2000;
        const carbPct = parseFloat(carbPctInput.value) || 0;
        const proteinPct = parseFloat(proteinPctInput.value) || 0;
        const fatPct = parseFloat(fatPctInput.value) || 0;

        const totalPct = carbPct + proteinPct + fatPct;

        if (totalPctBadge) {
            totalPctBadge.textContent = `${totalPct.toFixed(0)}%`;
            if (Math.abs(totalPct - 100) < 0.1) {
                totalPctBadge.className = 'badge bg-success bg-opacity-10 text-success fs-6 fw-bold';
            } else {
                totalPctBadge.className = 'badge bg-danger bg-opacity-10 text-danger fs-6 fw-bold';
            }
        }

        const carbKcal = totalCalories * (carbPct / 100);
        const proteinKcal = totalCalories * (proteinPct / 100);
        const fatKcal = totalCalories * (fatPct / 100);

        const carbGrams = Math.round(carbKcal / 4);
        const proteinGrams = Math.round(proteinKcal / 4);
        const fatGrams = Math.round(fatKcal / 9);

        if (carbGramsEl) carbGramsEl.textContent = `${carbGrams}g`;
        if (carbKcalEl) carbKcalEl.textContent = `${Math.round(carbKcal)} kcal`;

        if (proteinGramsEl) proteinGramsEl.textContent = `${proteinGrams}g`;
        if (proteinKcalEl) proteinKcalEl.textContent = `${Math.round(proteinKcal)} kcal`;

        if (fatGramsEl) fatGramsEl.textContent = `${fatGrams}g`;
        if (fatKcalEl) fatKcalEl.textContent = `${Math.round(fatKcal)} kcal`;

        if (macroChart) {
            macroChart.data.datasets[0].data = [carbGrams, proteinGrams, fatGrams];
            macroChart.update();
        }
    }

    // Dropdown Preset Change Event
    if (presetSelect) {
        presetSelect.addEventListener('change', function () {
            const val = this.value;
            if (val === 'oms') {
                applyPreset(50, 20, 30);
            } else if (val === 'sports') {
                applyPreset(40, 30, 30);
            } else if (val === 'lowcarb') {
                applyPreset(25, 40, 35);
            } else if (val === 'keto') {
                applyPreset(5, 25, 70);
            } else if (val === 'custom') {
                // Populate Modal with current values
                if (modalCarbInput) modalCarbInput.value = carbPctInput.value;
                if (modalProteinInput) modalProteinInput.value = proteinPctInput.value;
                if (modalFatInput) modalFatInput.value = fatPctInput.value;

                validateModalPercentages();

                if (customModal) {
                    customModal.show();
                } else if (customMacroModalEl && typeof bootstrap !== 'undefined') {
                    customModal = new bootstrap.Modal(customMacroModalEl);
                    customModal.show();
                }
            }
        });
    }

    // Modal Live Validation
    function validateModalPercentages() {
        if (!modalCarbInput || !modalProteinInput || !modalFatInput) return;

        const c = parseFloat(modalCarbInput.value) || 0;
        const p = parseFloat(modalProteinInput.value) || 0;
        const f = parseFloat(modalFatInput.value) || 0;
        const sum = c + p + f;

        if (modalTotalBadge) {
            modalTotalBadge.textContent = `${sum.toFixed(0)}%`;
            if (Math.abs(sum - 100) < 0.1) {
                modalTotalBadge.className = 'badge bg-success bg-opacity-10 text-success fs-5 fw-bold';
                if (modalErrorMsg) modalErrorMsg.classList.add('d-none');
                if (btnApplyModal) btnApplyModal.disabled = false;
            } else {
                modalTotalBadge.className = 'badge bg-danger bg-opacity-10 text-danger fs-5 fw-bold';
                if (modalErrorMsg) modalErrorMsg.classList.remove('d-none');
                if (btnApplyModal) btnApplyModal.disabled = true;
            }
        }
    }

    [modalCarbInput, modalProteinInput, modalFatInput].forEach(inp => {
        if (inp) {
            inp.addEventListener('input', validateModalPercentages);
        }
    });

    // Apply Custom Modal Values
    if (btnApplyModal) {
        btnApplyModal.addEventListener('click', function () {
            const c = parseFloat(modalCarbInput.value) || 0;
            const p = parseFloat(modalProteinInput.value) || 0;
            const f = parseFloat(modalFatInput.value) || 0;

            if (Math.abs((c + p + f) - 100) < 0.1) {
                applyPreset(c, p, f);
                if (customModal) customModal.hide();
            }
        });
    }

    // Attach listener for auto balancing
    ['carb', 'protein', 'fat'].forEach(type => {
        const input = inputs[type];
        const range = ranges[type];

        if (input) {
            input.addEventListener('input', function () {
                autoBalanceSliders(type, this.value);
            });
        }
        if (range) {
            range.value = input.value;
            range.addEventListener('input', function () {
                autoBalanceSliders(type, this.value);
            });
        }
    });

    if (targetCalInput) {
        targetCalInput.addEventListener('input', updateMacroCalculations);
    }

    // Helper to apply preset values
    window.applyPreset = function (carb, protein, fat) {
        isBalancing = true;
        if (carbPctInput) carbPctInput.value = carb;
        if (carbRange) carbRange.value = carb;

        if (proteinPctInput) proteinPctInput.value = protein;
        if (proteinRange) proteinRange.value = protein;

        if (fatPctInput) fatPctInput.value = fat;
        if (fatRange) fatRange.value = fat;

        isBalancing = false;
        updateMacroCalculations();
    };

    updateMacroCalculations();
});
