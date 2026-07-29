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
    const liveMaintainEl = document.getElementById('live-maintain');
    const liveGainMildEl = document.getElementById('live-gain-mild');
    const btnAdvance = document.getElementById('btn-advance-macros');

    let selectedCalorieValue = null;
    let selectedTargetType = null;
    let currentTDEE = 2000;

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
        currentTDEE = tdee;

        const lossMild = Math.round(tdee - 300);
        const lossNorm = Math.round(tdee - 500);
        const maint = Math.round(tdee);
        const gainMild = Math.round(tdee + 300);

        if (liveBmrEl) liveBmrEl.textContent = Math.round(bmr).toLocaleString('pt-BR') + ' kcal';
        if (liveTdeeEl) liveTdeeEl.textContent = Math.round(tdee).toLocaleString('pt-BR') + ' kcal';

        if (liveLossMildEl) liveLossMildEl.textContent = lossMild.toLocaleString('pt-BR') + ' kcal';
        if (liveLossNormEl) liveLossNormEl.textContent = lossNorm.toLocaleString('pt-BR') + ' kcal';
        if (liveMaintainEl) liveMaintainEl.textContent = maint.toLocaleString('pt-BR') + ' kcal';
        if (liveGainMildEl) liveGainMildEl.textContent = gainMild.toLocaleString('pt-BR') + ' kcal';

        // Update selected calorie value based on target type
        if (selectedTargetType === 'loss_mild') selectedCalorieValue = lossMild;
        else if (selectedTargetType === 'loss_norm') selectedCalorieValue = lossNorm;
        else if (selectedTargetType === 'maintain') selectedCalorieValue = maint;
        else if (selectedTargetType === 'gain_mild') selectedCalorieValue = gainMild;
        else selectedCalorieValue = maint;

        updateAdvanceButton();

        // Auto save BMR/TDEE on live update
        autoSaveBMR(gender, weight, height, age, activity);
    }

    function updateAdvanceButton() {
        if (btnAdvance && selectedCalorieValue) {
            const baseUrl = btnAdvance.dataset.baseUrl || '/macronutrientes';
            btnAdvance.href = `${baseUrl}?target_calories=${selectedCalorieValue}`;
        }
    }

    // Export function to window for target card selection
    window.selectTargetCard = function(element, targetType) {
        const allCards = document.querySelectorAll('.target-card-selectable');
        allCards.forEach(card => {
            card.classList.remove('selected', 'border-teal', 'bg-teal-light', 'bg-opacity-10', 'shadow');
            const icon = card.querySelector('.check-icon');
            if (icon) {
                icon.className = 'bi bi-circle check-icon text-muted fs-5';
            }
        });

        element.classList.add('selected', 'border-teal', 'bg-teal-light', 'bg-opacity-10', 'shadow');
        const icon = element.querySelector('.check-icon');
        if (icon) {
            icon.className = 'bi bi-check-circle-fill check-icon text-teal fs-5';
        }

        selectedTargetType = targetType;
        if (targetType === 'loss_mild') selectedCalorieValue = Math.round(currentTDEE - 300);
        else if (targetType === 'loss_norm') selectedCalorieValue = Math.round(currentTDEE - 500);
        else if (targetType === 'maintain') selectedCalorieValue = Math.round(currentTDEE);
        else if (targetType === 'gain_mild') selectedCalorieValue = Math.round(currentTDEE + 300);

        updateAdvanceButton();
    };

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

    // Select default or objective card on load
    const userObjectiveCard = document.querySelector('.target-card-selectable.user-objective');
    if (userObjectiveCard) {
        const type = userObjectiveCard.dataset.targetType;
        window.selectTargetCard(userObjectiveCard, type);
    } else {
        const defaultCard = document.querySelector('.target-card-selectable');
        if (defaultCard) {
            const type = defaultCard.dataset.targetType;
            window.selectTargetCard(defaultCard, type);
        }
    }
});
