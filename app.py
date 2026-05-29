from flask import Flask, render_template, jsonify, request, session
import json
import os
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

# Загрузка данных из JSON
with open('data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Файл для хранения статистики пользователя
STATS_FILE = 'user_stats.json'

def load_user_stats():
    """Загружает статистику пользователя из файла"""
    if os.path.exists(STATS_FILE):
        with open(STATS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        # Начальные данные
        return {
            'cards_studied': 0,
            'total_days': 1,
            'streak_days': 1,
            'last_visit': datetime.now().strftime('%Y-%m-%d'),
            'level': 1,
            'experience': 0,
            'max_exp': 100,
            'today_cards': 0,
            'today_mistakes': 0
        }

def save_user_stats(stats):
    """Сохраняет статистику пользователя в файл"""
    with open(STATS_FILE, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)

def update_streak(stats):
    """Обновляет счётчик дней подряд"""
    today = datetime.now().strftime('%Y-%m-%d')
    last_visit = stats.get('last_visit', '')
    
    if last_visit != today:
        last_date = datetime.strptime(last_visit, '%Y-%m-%d') if last_visit else None
        today_date = datetime.now()
        
        if last_date and (today_date - last_date).days == 1:
            # Посещение было вчера → увеличиваем streak
            stats['streak_days'] = stats.get('streak_days', 0) + 1
        elif last_date and (today_date - last_date).days > 1:
            # Был пропуск → сбрасываем streak
            stats['streak_days'] = 1
        elif not last_visit:
            # Первый визит
            stats['streak_days'] = 1
        
        # Обновляем общее количество дней (уникальные дни)
        if last_visit != today:
            stats['total_days'] = stats.get('total_days', 0) + 1
        
        stats['last_visit'] = today
        # Сбрасываем счётчики за сегодня
        stats['today_cards'] = 0
        stats['today_mistakes'] = 0
        save_user_stats(stats)
    
    return stats

# Загружаем статистику
user_stats = load_user_stats()
user_stats = update_streak(user_stats)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/decks')
def get_decks():
    decks = list(data.keys())
    return jsonify(decks)

@app.route('/api/cards/<deck_name>')
def get_cards(deck_name):
    if deck_name in data:
        cards = data[deck_name]
        return jsonify(cards)
    return jsonify([])

@app.route('/api/stats')
def get_stats():
    global user_stats
    # Обновляем streak при каждом запросе статистики
    user_stats = update_streak(user_stats)
    return jsonify({
        'cards_studied': user_stats['cards_studied'],
        'streak_days': user_stats['streak_days'],
        'total_days': user_stats['total_days'],
        'level': user_stats['level'],
        'experience': user_stats['experience'],
        'max_exp': user_stats['max_exp'],
        'today_cards': user_stats.get('today_cards', 0),
        'today_mistakes': user_stats.get('today_mistakes', 0)
    })

@app.route('/api/update_progress', methods=['POST'])
def update_progress():
    global user_stats
    req = request.json
    action = req.get('action')
    
    # Обновляем streak
    user_stats = update_streak(user_stats)
    
    if action == 'know':
        user_stats['experience'] += 5
        user_stats['cards_studied'] += 1
        user_stats['today_cards'] = user_stats.get('today_cards', 0) + 1
    elif action == 'dont_know':
        user_stats['experience'] += 1
        user_stats['cards_studied'] += 1
        user_stats['today_cards'] = user_stats.get('today_cards', 0) + 1
        user_stats['today_mistakes'] = user_stats.get('today_mistakes', 0) + 1
    
    # Повышение уровня
    if user_stats['experience'] >= user_stats['max_exp']:
        user_stats['level'] += 1
        user_stats['experience'] -= user_stats['max_exp']
        user_stats['max_exp'] += 50
    
    save_user_stats(user_stats)
    
    return jsonify({
        'cards_studied': user_stats['cards_studied'],
        'streak_days': user_stats['streak_days'],
        'total_days': user_stats['total_days'],
        'level': user_stats['level'],
        'experience': user_stats['experience'],
        'max_exp': user_stats['max_exp'],
        'today_cards': user_stats.get('today_cards', 0),
        'today_mistakes': user_stats.get('today_mistakes', 0)
    })

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)