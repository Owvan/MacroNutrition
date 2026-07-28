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

    const totalPctBadge = document.getElementById('total-pct-badge');

    // Display elements for grams & kcal
    const carbGramsEl = document.getElementById('carb-grams');
    const carbKcalEl = document.getElementById('carb-kcal');
    const proteinGramsEl = document.getElementById('protein-grams');
    const proteinKcalEl = document.getElementById('protein-kcal');
    const fatGramsEl = document.getElementById('fat-grams');
    const fatKcalEl = document.getElementById('fat-kcal');

    // Chart Canvas
    const canvas = document.getElementById('macroChart');
    let macroChart = null;

    // Initialize Chart.js Donut Chart
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

    function updateMacroCalculations() {
        const totalCalories = parseFloat(targetCalInput.value) || 2000;
        const carbPct = parseFloat(carbPctInput.value) || 0;
        const proteinPct = parseFloat(proteinPctInput.value) || 0;
        const fatPct = parseFloat(fatPctInput.value) || 0;

        const totalPct = carbPct + proteinPct + fatPct;

        // Update Total Percentage Badge
        if (totalPctBadge) {
            totalPctBadge.textContent = `${totalPct.toFixed(0)}%`;
            if (Math.abs(totalPct - 100) < 0.1) {
                totalPctBadge.className = 'badge bg-success bg-opacity-10 text-success fs-6 fw-bold';
            } else {
                totalPctBadge.className = 'badge bg-danger bg-opacity-10 text-danger fs-6 fw-bold';
            }
        }

        // Calculate kcal and grams
        const carbKcal = totalCalories * (carbPct / 100);
        const proteinKcal = totalCalories * (proteinPct / 100);
        const fatKcal = totalCalories * (fatPct / 100);

        const carbGrams = Math.round(carbKcal / 4);
        const proteinGrams = Math.round(proteinKcal / 4);
        const fatGrams = Math.round(fatKcal / 9);

        // Update Text Elements
        if (carbGramsEl) carbGramsEl.textContent = `${carbGrams}g`;
        if (carbKcalEl) carbKcalEl.textContent = `${Math.round(carbKcal)} kcal`;

        if (proteinGramsEl) proteinGramsEl.textContent = `${proteinGrams}g`;
        if (proteinKcalEl) proteinKcalEl.textContent = `${Math.round(proteinKcal)} kcal`;

        if (fatGramsEl) fatGramsEl.textContent = `${fatGrams}g`;
        if (fatKcalEl) fatKcalEl.textContent = `${Math.round(fatKcal)} kcal`;

        // Update Chart
        if (macroChart) {
            macroChart.data.datasets[0].data = [carbGrams, proteinGrams, fatGrams];
            macroChart.update();
        }
    }

    // Sync Number Inputs with Range Sliders
    function syncInputAndRange(inputEl, rangeEl) {
        if (!inputEl || !rangeEl) return;
        
        inputEl.addEventListener('input', function () {
            rangeEl.value = inputEl.value;
            updateMacroCalculations();
        });

        rangeEl.addEventListener('input', function () {
            inputEl.value = rangeEl.value;
            updateMacroCalculations();
        });
    }

    syncInputAndRange(carbPctInput, carbRange);
    syncInputAndRange(proteinPctInput, proteinRange);
    syncInputAndRange(fatPctInput, fatRange);

    if (targetCalInput) {
        targetCalInput.addEventListener('input', updateMacroCalculations);
    }

    // Presets
    window.applyPreset = function (carb, protein, fat) {
        if (carbPctInput) carbPctInput.value = carb;
        if (carbRange) carbRange.value = carb;

        if (proteinPctInput) proteinPctInput.value = protein;
        if (proteinRange) proteinRange.value = protein;

        if (fatPctInput) fatPctInput.value = fat;
        if (fatRange) fatRange.value = fat;

        updateMacroCalculations();
    };

    // Initial Calculation Run
    updateMacroCalculations();
});
