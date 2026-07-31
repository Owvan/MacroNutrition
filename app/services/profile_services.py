from app.database import get_db

GOAL_LABELS = {
    'weight_loss': 'Emagrecimento / Perda de Gordura',
    'weight_gain': 'Ganho de Peso / Massa Muscular',
    'maintenance': 'Manutenção de Peso'
}

PACE_RATES = {
    'conservative': 0.25,
    'recommended': 0.50,
    'moderate': 0.75,
    'aggressive': 1.00
}

def calculate_bmi_info(height_cm, weight_kg):
    """Calcula IMC, classificação OMS e faixa de peso ideal."""
    height_m = float(height_cm or 170) / 100.0
    weight_kg = float(weight_kg or 70)
    
    if height_m <= 0 or weight_kg <= 0:
        return None
    
    bmi = round(weight_kg / (height_m ** 2), 1)
    
    if bmi < 18.5:
        category = 'Abaixo do peso'
        color = 'warning'
        risk_desc = 'Riscos: desnutrição, imunidade reduzida, osteopenia, fadiga crônica e perda de massa muscular.'
    elif bmi < 25.0:
        category = 'Peso Normal (Ideal)'
        color = 'success'
        risk_desc = 'Faixa saudável! Menor risco de doenças crônicas não transmissíveis e equilíbrio metabólico.'
    elif bmi < 30.0:
        category = 'Sobrepeso'
        color = 'warning'
        risk_desc = 'Riscos: elevação inicial da pressão arterial, resistência à insulina e alteração de colesterol.'
    elif bmi < 35.0:
        category = 'Obesidade Grau I'
        color = 'danger'
        risk_desc = 'Riscos: aumento significativo no risco de Diabetes Tipo 2, hipertensão arterial e esteatose hepática.'
    elif bmi < 40.0:
        category = 'Obesidade Grau II'
        color = 'danger'
        risk_desc = 'Riscos: alto risco metabólico e cardiovascular, apneia do sono e sobrecarga nas articulações.'
    else:
        category = 'Obesidade Grau III'
        color = 'danger'
        risk_desc = 'Riscos: altíssimo risco de eventos cardiovasculares (infarto/AVC). Requer atenção médica imediata.'
        
    min_ideal = round(18.5 * (height_m ** 2), 1)
    max_ideal = round(24.9 * (height_m ** 2), 1)
    suggested_ideal = round(22.0 * (height_m ** 2), 1)
    
    suggested_change = 0.0
    suggested_goal_type = 'maintenance'
    
    if weight_kg > max_ideal:
        suggested_change = round(weight_kg - suggested_ideal, 1)
        suggested_goal_type = 'weight_loss'
    elif weight_kg < min_ideal:
        suggested_change = round(suggested_ideal - weight_kg, 1)
        suggested_goal_type = 'weight_gain'
        
    suggested_weeks = max(4, int(round(suggested_change / 0.5))) if suggested_change > 0 else 8

    return {
        'bmi': bmi,
        'category': category,
        'color': color,
        'risk_desc': risk_desc,
        'min_ideal': min_ideal,
        'max_ideal': max_ideal,
        'suggested_ideal': suggested_ideal,
        'suggested_change': suggested_change,
        'suggested_goal_type': suggested_goal_type,
        'suggested_weeks': suggested_weeks
    }

def classify_weekly_rate(goal_type, weekly_rate_kg):
    """Classifica o ritmo semanal de perda/ganho de peso em categorias (Recomendado, Moderado, Agressivo, Conservador)."""
    if goal_type == 'maintenance' or weekly_rate_kg <= 0:
        return {
            'label': 'Manutenção de Peso',
            'badge_class': 'bg-teal text-white',
            'icon': 'bi-dash-circle-fill',
            'desc': 'Manter o peso estável sem alteração calórica brusca.'
        }
    
    if goal_type == 'weight_loss':
        if weekly_rate_kg <= 0.25:
            return {
                'label': 'Conservador / Suave',
                'badge_class': 'bg-info text-white',
                'icon': 'bi-info-circle-fill',
                'desc': 'Ritmo suave e fácil de manter a longo prazo.'
            }
        elif weekly_rate_kg <= 0.75:
            return {
                'label': 'Recomendado (Saudável)',
                'badge_class': 'bg-success text-white',
                'icon': 'bi-check-circle-fill',
                'desc': 'Ritmo ideal segundo a OMS para queimar gordura preservando massa muscular.'
            }
        elif weekly_rate_kg <= 1.0:
            return {
                'label': 'Moderado / Desafiador',
                'badge_class': 'bg-warning text-dark',
                'icon': 'bi-exclamation-triangle-fill',
                'desc': 'Exige bom controle de ingestão proteica e déficit disciplinado.'
            }
        else:
            return {
                'label': 'Agressivo (Cuidados Necessários)',
                'badge_class': 'bg-danger text-white',
                'icon': 'bi-exclamation-octagon-fill',
                'desc': 'Ritmo intenso! Risco de fadiga e perda de massa muscular. Requer atenção.'
            }
    else: # weight_gain
        if weekly_rate_kg <= 0.25:
            return {
                'label': 'Suave / Limpo',
                'badge_class': 'bg-info text-white',
                'icon': 'bi-info-circle-fill',
                'desc': 'Ganho gradual focado em minimizar acúmulo de gordura.'
            }
        elif weekly_rate_kg <= 0.5:
            return {
                'label': 'Recomendado (Hipertrofia)',
                'badge_class': 'bg-success text-white',
                'icon': 'bi-check-circle-fill',
                'desc': 'Ritmo recomendado para síntese proteica e hipertrofia muscular.'
            }
        else:
            return {
                'label': 'Agressivo / Superávit Alto',
                'badge_class': 'bg-warning text-dark',
                'icon': 'bi-exclamation-triangle-fill',
                'desc': 'Ganho rápido com maior probabilidade de ganho de gordura associado.'
            }

def get_user_profile(user_id):
    """Retorna o perfil do usuário cadastrado no banco com dados de IMC, peso meta e estimativa de tempo."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        SELECT id, user_id, full_name, gender, age, height, current_weight, target_weight,
               goal_type, target_weight_change_kg, target_timeframe_weeks, weekly_pace,
               weekly_rate_kg, activity_level, created_at, updated_at
        FROM user_profiles
        WHERE user_id = ?
    ''', (user_id,))
    row = cursor.fetchone()
    if not row:
        return None
    
    profile = dict(row)
    cur_w = profile['current_weight']
    
    # Fill target_weight if missing
    if not profile.get('target_weight'):
        chg = profile.get('target_weight_change_kg', 0.0)
        goal = profile.get('goal_type', 'weight_loss')
        if goal == 'weight_loss':
            profile['target_weight'] = round(cur_w - chg, 1)
        elif goal == 'weight_gain':
            profile['target_weight'] = round(cur_w + chg, 1)
        else:
            profile['target_weight'] = cur_w
            
    tar_w = profile['target_weight']
    diff_kg = round(abs(cur_w - tar_w), 1)
    profile['weight_difference_kg'] = diff_kg

    # Determine goal label automatically based on weights
    if tar_w < cur_w:
        profile['goal_type'] = 'weight_loss'
    elif tar_w > cur_w:
        profile['goal_type'] = 'weight_gain'
    else:
        profile['goal_type'] = 'maintenance'
        
    profile['goal_label'] = GOAL_LABELS.get(profile['goal_type'], 'Manutenção de Peso')
    
    # IMC Info
    bmi_info = calculate_bmi_info(profile['height'], cur_w)
    profile['bmi_info'] = bmi_info
    
    # Calculate weekly target rate & weeks
    saved_rate = profile.get('weekly_rate_kg')
    weeks = profile.get('target_timeframe_weeks') or 1
    
    if saved_rate is not None and float(saved_rate) > 0:
        weekly_rate = round(float(saved_rate), 2)
    elif diff_kg > 0:
        weekly_rate = round(diff_kg / max(weeks, 1), 2)
    else:
        weekly_rate = 0.50

    profile['weekly_rate_kg'] = weekly_rate
    profile['calculated_weeks'] = max(1, int(round(diff_kg / weekly_rate))) if weekly_rate > 0 else 0
    profile['calculated_months'] = round(profile['calculated_weeks'] / 4.33, 1)
    
    # Classify weekly rate
    profile['rate_classification'] = classify_weekly_rate(profile['goal_type'], weekly_rate)
    
    return profile

def save_or_update_user_profile(user_id, full_name, gender, age, height, current_weight, target_weight, weekly_rate_kg, activity_level, weekly_pace='recommended', goal_type=None):
    """Cria ou atualiza o perfil e metas do usuário com base no peso meta e ritmo semanal."""
    db = get_db()
    cursor = db.cursor()

    full_name = str(full_name or '').strip()
    gender = str(gender or 'male').strip()
    age = int(age or 25)
    height = float(height or 170.0)
    current_weight = float(current_weight or 70.0)
    target_weight = float(target_weight or 65.0)
    weekly_rate_kg = float(str(weekly_rate_kg or 0.50).replace(',', '.'))
    activity_level = float(str(activity_level or 1.2).replace(',', '.'))
    weekly_pace = str(weekly_pace or 'recommended').strip()

    # Determine goal type & diff
    if target_weight < current_weight:
        computed_goal = 'weight_loss'
    elif target_weight > current_weight:
        computed_goal = 'weight_gain'
    else:
        computed_goal = 'maintenance'

    goal_type = goal_type or computed_goal
    target_weight_change_kg = round(abs(current_weight - target_weight), 1)

    if weekly_rate_kg > 0 and target_weight_change_kg > 0:
        target_timeframe_weeks = max(1, int(round(target_weight_change_kg / weekly_rate_kg)))
    else:
        target_timeframe_weeks = 8

    cursor.execute('SELECT id FROM user_profiles WHERE user_id = ?', (user_id,))
    existing = cursor.fetchone()

    if existing:
        cursor.execute('''
            UPDATE user_profiles
            SET full_name = ?,
                gender = ?,
                age = ?,
                height = ?,
                current_weight = ?,
                target_weight = ?,
                goal_type = ?,
                target_weight_change_kg = ?,
                target_timeframe_weeks = ?,
                weekly_pace = ?,
                weekly_rate_kg = ?,
                activity_level = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
        ''', (full_name, gender, age, height, current_weight, target_weight, goal_type, target_weight_change_kg, target_timeframe_weeks, weekly_pace, weekly_rate_kg, activity_level, user_id))
    else:
        cursor.execute('''
            INSERT INTO user_profiles
            (user_id, full_name, gender, age, height, current_weight, target_weight, goal_type, target_weight_change_kg, target_timeframe_weeks, weekly_pace, weekly_rate_kg, activity_level)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, full_name, gender, age, height, current_weight, target_weight, goal_type, target_weight_change_kg, target_timeframe_weeks, weekly_pace, weekly_rate_kg, activity_level))

    db.commit()
    return True
