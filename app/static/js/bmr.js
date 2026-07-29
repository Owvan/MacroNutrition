document.addEventListener('DOMContentLoaded', function () {
    const bmrForm = document.getElementById('bmr-form');
    if (!bmrForm) return;

    const weightInput = document.getElementById('weight');
    const heightInput = document.getElementById('height');
    const ageInput = document.getElementById('age');
    const activitySelect = document.getElementById('activity_level');
    const genderInputs = document.querySelectorAll('input[name="gender"]');

    const liveBmrEl = document.getElementById('live-bmr');
    const liveTdeeEl = document.getElementById('live-tdee');
    const liveLossMildEl = document.getElementById('live-loss-mild');
    const liveLossNormEl = document.getElementById('live-loss-norm');
    const liveGainMildEl = document.getElementById('live-gain-mild');

    let saveTimeout = null;

    function autoSaveBMR(gender, weight, height, age, activity_level) {
        if (saveTimeout) clearTimeout(saveTimeout);
        saveTimeout = setTimeout(() => {
            fetch('/api/save-bmr', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ gender, weight, height, age, activity_level })
            }).catch(err => console.error('Erro ao auto-salvar TMB:', err));
        }, 500);
    }

    function calculateLive() {
        const weight = parseFloat(weightInput.value) || 0;
        const height = parseFloat(heightInput.value) || 0;
        const age = parseInt(ageInput.value) || 0;
        const activity = parseFloat(activitySelect.value) || 1.2;

        let gender = 'male';
        genderInputs.forEach(input => {
            if (input.checked) gender = input.value;
        });

        if (weight <= 0 || height <= 0 || age <= 0) {
            return;
        }

        let bmr = 0;
        if (gender === 'female') {
            bmr = (10 * weight) + (6.25 * height) - (5 * age) - 161;
        } else {
            bmr = (10 * weight) + (6.25 * height) - (5 * age) + 5;
        }

        const tdee = bmr * activity;

        if (liveBmrEl) liveBmrEl.textContent = Math.round(bmr).toLocaleString('pt-BR') + ' kcal';
        if (liveTdeeEl) liveTdeeEl.textContent = Math.round(tdee).toLocaleString('pt-BR') + ' kcal';

        if (liveLossMildEl) liveLossMildEl.textContent = Math.round(tdee - 300).toLocaleString('pt-BR') + ' kcal';
        if (liveLossNormEl) liveLossNormEl.textContent = Math.round(tdee - 500).toLocaleString('pt-BR') + ' kcal';
        if (liveGainMildEl) liveGainMildEl.textContent = Math.round(tdee + 300).toLocaleString('pt-BR') + ' kcal';

        // Auto save BMR/TDEE on live update
        autoSaveBMR(gender, weight, height, age, activity);
    }

    [weightInput, heightInput, ageInput, activitySelect].forEach(input => {
        if (input) {
            input.addEventListener('input', calculateLive);
            input.addEventListener('change', calculateLive);
        }
    });

    genderInputs.forEach(input => {
        input.addEventListener('change', calculateLive);
    });

    // Run initial live calculation
    calculateLive();
});
