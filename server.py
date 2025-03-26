from flask import Flask, render_template, request, session
from flask_socketio import SocketIO, emit, disconnect
import random
from collections import Counter
import uuid
import time
import threading

app = Flask(__name__)
app.secret_key = 'your-secret-key'
socketio = SocketIO(app, manage_session=False, cors_allowed_origins="*")

games = {}
SECRET_KEY = "my-super-secret-key"  # Задаём секретный ключ для сброса игр
GAME_TIMEOUT = 5 * 60  # 5 минут в секундах

# Создание колоды чисел
def create_number_deck():
    distribution = {1: 15, 2: 14, 3: 13, 4: 12, 5: 11, 6: 10, 7: 9, 8: 8, 9: 8}
    deck = []
    for num, count in distribution.items():
        deck.extend([num] * count)
    random.shuffle(deck)
    return deck

# Возможные комбинации
def calculate_combinations(cards):
    results = set()
    if len(cards) == 2:
        a, b = cards
        results.add(a + b)
        results.add(a * b)
    elif len(cards) == 3:
        a, b, c = cards
        results.add(a * b * c)
        results.add(a + b + c)
        results.add((a + b) * c)
        results.add(a * b + c)
    return results

# Создание колоды ответов
def create_answer_deck():
    answer_distribution = {12: 4, 16: 4, 14: 4, 18: 4, 15: 4, 10: 4, 13: 4, 11: 4, 24: 4, 20: 4, 9: 4, 36: 4, 17: 3, 
                           8: 3, 30: 3, 21: 3, 48: 3, 72: 3, 19: 3, 40: 3, 22: 3, 28: 3, 7: 3, 32: 3, 60: 3, 42: 3, 
                           56: 3, 6: 3, 45: 2, 27: 2
                           }
    if answer_distribution:
        answer_deck = []
        for num, count in answer_distribution.items():
            answer_deck.extend([num] * count)
        random.shuffle(answer_deck)
        return answer_deck
    else:
        number_deck = create_number_deck()
        all_results = []
        for i in range(len(number_deck)):
            for j in range(i + 1, len(number_deck)):
                pair = [number_deck[i], number_deck[j]]
                all_results.extend(calculate_combinations(pair))
                for k in range(j + 1, len(number_deck)):
                    triplet = [number_deck[i], number_deck[j], number_deck[k]]
                    all_results.extend(calculate_combinations(triplet))
        result_counts = Counter(all_results)
        top_20 = result_counts.most_common(20)
        total_frequency = sum(count for _, count in top_20)
        answer_deck = []
        for result, count in top_20:
            proportion = count / total_frequency
            num_cards = max(1, round(proportion * 100))
            answer_deck.extend([result] * num_cards)
        if len(answer_deck) > 100:
            answer_deck = answer_deck[:100]
        elif len(answer_deck) < 100:
            extra_needed = 100 - len(answer_deck)
            answer_deck.extend([top_20[0][0]] * extra_needed)
        random.shuffle(answer_deck)
        return answer_deck

# Функция для отправки обновлённого списка игр всем клиентам
def broadcast_games():
    active_games = []
    for game in games.values():
        if not game.game_started:
            connected_count = len([p for p in game.players.values() if p["connected"]])
            active_games.append({"id": game.game_id, "creator": game.players[0]["name"], "players": connected_count})
    socketio.emit('update_games', {'games': active_games})  # Убираем broadcast=True

# Функция для автоматического удаления старых неначатых игр
def cleanup_old_games():
    while True:
        current_time = time.time()
        removed_games = 0
        for game_id in list(games.keys()):
            game = games[game_id]
            if not game.game_started and (current_time - game.creation_time) > GAME_TIMEOUT:
                # Уведомляем игроков, что игра была удалена
                for player in game.players.values():
                    if player["connected"]:
                        socketio.emit('game_reset', {'message': 'Игра была удалена из-за истечения времени ожидания.'}, room=player['sid'])
                del games[game_id]
                removed_games += 1
        if removed_games > 0:
            print(f"Автоматически удалено {removed_games} неначатых игр, старше 5 минут.")
            broadcast_games()  # Обновляем список игр для всех клиентов
        time.sleep(30)  # Проверяем каждые 30 секунд

class Game:
    def __init__(self, game_id, creator_sid, creator_name):
        self.game_id = game_id
        self.number_deck = create_number_deck()
        self.answer_deck = create_answer_deck()
        self.discard_pile = []
        self.players = {
            0: {
                "sid": creator_sid,
                "hand": [self.number_deck.pop(0) for _ in range(5)],
                "score_pile": [],
                "score": 0,
                "wins": 0,
                "name": creator_name,
                "connected": True
            }
        }
        self.table_cards = [self.answer_deck.pop(0) for _ in range(5)]
        self.current_player_idx = 0
        self.game_started = False
        self.creator_sid = creator_sid
        self.creation_time = time.time()

    def add_player(self, sid, name):
        if self.game_started or len(self.players) >= 4:
            return False
        for pid, player in self.players.items():
            if player["name"] == name:
                emit('error', {'message': 'Игрок с таким именем уже есть в этой игре!'}, room=sid)
                return False
        player_id = len(self.players)
        self.players[player_id] = {
            "sid": sid,
            "hand": [self.number_deck.pop(0) for _ in range(5)],
            "score_pile": [],
            "score": 0,
            "wins": 0,
            "name": name,
            "connected": True
        }
        print(f"Добавлен игрок {name} с SID: {sid} и ID: {player_id} в игру {self.game_id}")
        return player_id

    def update_sid(self, player_id, new_sid):
        if player_id in self.players:
            self.players[player_id]["sid"] = new_sid
            self.players[player_id]["connected"] = True
            print(f"Обновлён SID игрока {self.players[player_id]['name']} на {new_sid}")
            if player_id == 0:
                self.creator_sid = new_sid

    def remove_player(self, sid):
        for pid, player in list(self.players.items()):
            if player["sid"] == sid and pid != 0:
                player["connected"] = False
                print(f"Игрок {player['name']} с SID: {sid} отключился из игры {self.game_id}")
                return True
        return False

    def get_player_id_by_sid(self, sid):
        for pid, player in self.players.items():
            if player["sid"] == sid:
                return pid
        return None

    def cleanup_disconnected(self):
        for pid, player in list(self.players.items()):
            if pid != 0 and not player["connected"] and (time.time() - self.creation_time) > 30:
                del self.players[pid]
                print(f"Окончательно удалён игрок {player['name']} из игры {self.game_id}")

    def start_game(self):
        self.cleanup_disconnected()
        connected_players = [p for p in self.players.values() if p["connected"]]
        if len(connected_players) >= 2 and not self.game_started:
            self.game_started = True
            print(f"Игра {self.game_id} началась с {len(connected_players)} игроками!")
            self.update_all_players()

    def process_play(self, player_id, cards, operation):
        if len(cards) not in [2, 3] or player_id != self.current_player_idx or not self.game_started:
            return False, None
        if player_id not in self.players or not self.players[player_id]["connected"]:
            return False, None
        
        hand_copy = self.players[player_id]["hand"].copy()
        for card in cards:
            if card in hand_copy:
                hand_copy.remove(card)
            else:
                return False, None

        valid_result = None
        points = 0
        expression = ""
        if len(cards) == 2:
            a, b = cards
            if operation == "Сложить" and a + b in self.table_cards:
                valid_result = a + b
                points = 1
                expression = f"{a}+{b}"
            elif operation == "Умножить" and a * b in self.table_cards:
                valid_result = a * b
                points = 1
                expression = f"{a}*{b}"
        elif len(cards) == 3:
            a, b, c = cards
            if operation == "Сложить" and a + b + c in self.table_cards:
                valid_result = a + b + c
                points = 2
                expression = f"{a}+{b}+{c}"
            elif operation == "Умножить" and a * b * c in self.table_cards:
                valid_result = a * b * c
                points = 2
                expression = f"{a}*{b}*{c}"
            elif operation == "(A+B)*C" and (a + b) * c in self.table_cards:
                valid_result = (a + b) * c
                points = 3
                expression = f"({a}+{b})*{c}"
            elif operation == "A*B+C" and a * b + c in self.table_cards:
                valid_result = a * b + c
                points = 3
                expression = f"{a}*{b}+{c}"

        if valid_result:
            for card in cards:
                self.players[player_id]["hand"].remove(card)
            self.table_cards.remove(valid_result)
            self.players[player_id]["score_pile"].append(valid_result)
            self.players[player_id]["score"] = self.players[player_id].get("score", 0) + points
            self.players[player_id]["hand"].extend([self.number_deck.pop(0) for _ in range(5 - len(self.players[player_id]["hand"])) if self.number_deck])
            while len(self.table_cards) < 5 and self.answer_deck:
                self.table_cards.append(self.answer_deck.pop(0))
            self.current_player_idx = (self.current_player_idx + 1) % len(self.players)
            print(f"Валидный ход: {cards} -> {valid_result} с операцией {operation}, начислено {points} очков")
            log_message = f"Игрок {self.players[player_id]['name']} сделал ход {expression} = {valid_result} и заработал {points} очков"
            is_winner = self.players[player_id]["score"] >= 15
            return is_winner, log_message
        return False, None

    def get_state(self, player_id):
        return {
            "table_cards": self.table_cards,
            "hand": self.players[player_id]["hand"],
            "current_player": self.current_player_idx,
            "current_player_name": self.players[self.current_player_idx]["name"],
            "score": self.players[player_id]["score"],
            "player_id": player_id,
            "player_name": self.players[player_id]["name"],
            "players": [
                {
                    "name": p["name"],
                    "score": p.get("score", 0),
                    "wins": p.get("wins", 0),
                    "is_current": i == self.current_player_idx
                } for i, p in self.players.items() if p["connected"]
            ]
        }

    def process_draw(self, player_id):
        if player_id != self.current_player_idx or not self.game_started or player_id not in self.players or not self.players[player_id]["connected"]:
            return False, None
        if not self.number_deck and self.discard_pile:
            self.number_deck.extend(self.discard_pile)
            random.shuffle(self.number_deck)
            self.discard_pile.clear()
        if self.number_deck:
            drawn_card = self.number_deck.pop(0)
            self.players[player_id]["hand"].append(drawn_card)
            self.current_player_idx = (self.current_player_idx + 1) % len(self.players)
            log_message = f"Игрок {self.players[player_id]['name']} взял карту из колоды"
            return True, log_message
        return False, None

    def update_all_players(self):
        self.cleanup_disconnected()
        for pid, player in self.players.items():
            if player["connected"]:
                state = self.get_state(pid)
                print(f"Отправка состояния игроку {pid} с SID {player['sid']}: {state}")
                if pid == self.current_player_idx:
                    socketio.emit('your_turn', state, room=player['sid'])
                else:
                    socketio.emit('update', state, room=player['sid'])

    def end_game(self):
        self.cleanup_disconnected()
        scores = {pid: len(player["score_pile"]) for pid, player in self.players.items() if player["connected"]}
        if not scores:
            return
        max_score = max(scores.values())
        winners = [self.players[pid]["name"] for pid, score in scores.items() if score == max_score]
        winner_text = "Ничья между: " + ", ".join(winners) if len(winners) > 1 else f"Победил {winners[0]}"
        for pid, player in self.players.items():
            if player["connected"]:
                socketio.emit('win', {'winner': winner_text}, room=player['sid'])

# Новый маршрут для сброса неначатых игр
@app.route('/reset_games/<secret_key>')
def reset_games(secret_key):
    if secret_key != SECRET_KEY:
        return "Неверный секретный ключ!", 403
    removed_games = 0
    for game_id in list(games.keys()):
        if not games[game_id].game_started:
            # Уведомляем игроков, что игра была удалена
            for player in games[game_id].players.values():
                if player["connected"]:
                    socketio.emit('game_reset', {'message': 'Игра была сброшена администратором.'}, room=player['sid'])
            del games[game_id]
            removed_games += 1
    broadcast_games()  # Обновляем список игр для всех клиентов
    return f"Удалено {removed_games} неначатых игр.", 200

@app.route('/')
def index():
    active_games = []
    for game in games.values():
        if not game.game_started:
            connected_count = len([p for p in game.players.values() if p["connected"]])
            active_games.append({"id": game.game_id, "creator": game.players[0]["name"], "players": connected_count})
    return render_template('index.html', games=active_games)

@app.route('/waiting/<game_id>/<player_id>')
def waiting(game_id, player_id):
    print(f"Запрос на /waiting/{game_id}/{player_id}")
    player_id = int(player_id)
    if game_id not in games:
        return "Игра не найдена", 404
    if player_id not in games[game_id].players:
        print(f"Доступ запрещён: player_id={player_id} не в игре")
        return "Вы не участник этой игры", 403
    game = games[game_id]
    return render_template('waiting.html', game_id=game_id, player_id=player_id, creator=game.players[0]["name"])

@app.route('/game/<game_id>/<player_id>')
def game_page(game_id, player_id):
    print(f"Запрос на /game/{game_id}/{player_id}")
    player_id = int(player_id)
    if game_id not in games or not games[game_id].game_started:
        return "Игра не начата или не существует", 404
    if player_id not in games[game_id].players:
        return "Вы не участник этой игры", 403
    return render_template('game.html', game_id=game_id, player_id=player_id, player_name=games[game_id].players[player_id]['name'])

@socketio.on('play_again')
def handle_play_again(data):
    game_id = data['game_id']
    player_id = data['player_id']
    if game_id not in games:
        return
    if 'play_again_votes' not in games[game_id].__dict__:
        games[game_id].play_again_votes = set()
    games[game_id].play_again_votes.add(player_id)
    connected_players = sum(1 for p in games[game_id].players.values() if p["connected"])
    if len(games[game_id].play_again_votes) == connected_players:
        new_game_id = str(uuid.uuid4())
        new_game = Game(new_game_id, games[game_id].creator_sid, games[game_id].players[0]["name"])
        for pid, player in games[game_id].players.items():
            if pid != 0 and player["connected"]:
                new_game.add_player(player["sid"], player["name"])
        games[new_game_id] = new_game
        del games[game_id]
        new_game.start_game()
        for pid, player in new_game.players.items():
            if player["connected"]:
                socketio.emit('start', {'game_id': new_game_id, 'player_id': pid}, room=player['sid'])
        broadcast_games()

@socketio.on('connect')
def handle_connect():
    print(f"Клиент подключился с SID: {request.sid}")

@socketio.on('update_sid')
def handle_update_sid(data):
    game_id = data['game_id']
    player_id = int(data['player_id'])
    if game_id in games and player_id in games[game_id].players:
        games[game_id].update_sid(player_id, request.sid)
        print(f"Обновлён SID для игрока {player_id} в игре {game_id}")
        if games[game_id].game_started:
            state = games[game_id].get_state(player_id)
            print(f"Отправка состояния игры для player_id {player_id}: {state}")
            if player_id == games[game_id].current_player_idx:
                socketio.emit('your_turn', state, room=request.sid)
            else:
                socketio.emit('update', state, room=request.sid)
        else:
            emit('update_players', {
                'players': [p["name"] for p in games[game_id].players.values() if p["connected"]],
                'creator': games[game_id].players[0]["name"],
                'is_creator': player_id == 0
            }, room=request.sid)
            for pid, player in games[game_id].players.items():
                if player["connected"] and pid != player_id:
                    socketio.emit('player_joined', {'players': [p["name"] for p in games[game_id].players.values() if p["connected"]]}, room=player['sid'])

@socketio.on('create_game')
def handle_create_game(data):
    name = data['name']
    if not name:
        emit('error', {'message': 'Введите имя!'})
        return
    game_id = str(uuid.uuid4())
    games[game_id] = Game(game_id, request.sid, name)
    print(f"Создана игра {game_id} игроком {name} с SID: {request.sid}")
    emit('game_created', {'game_id': game_id, 'player_id': 0})
    broadcast_games()

@socketio.on('join_game')
def handle_join_game(data):
    name = data['name']
    game_id = data['game_id']
    if not name or game_id not in games or games[game_id].game_started:
        emit('error', {'message': 'Нельзя присоединиться к игре!'})
        return
    player_id = games[game_id].add_player(request.sid, name)
    if player_id is False:
        emit('error', {'message': 'Игра уже полна!'})
        return
    print(f"Игрок {name} присоединился к игре {game_id} с player_id: {player_id}")
    emit('init', {'player_id': player_id, 'player_name': name, 'game_id': game_id})
    for pid, player in games[game_id].players.items():
        if player["connected"]:
            socketio.emit('player_joined', {'players': [p["name"] for p in games[game_id].players.values() if p["connected"]]}, room=player['sid'])
            if pid != player_id:
                socketio.emit('chat_message', {
                    'sender': 'Система',
                    'message': f"{name} присоединился к игре"
                }, room=player['sid'])
    broadcast_games()

@socketio.on('start_game')
def handle_start_game(data):
    game_id = data['game_id']
    print(f"Получено start_game для игры {game_id} от SID: {request.sid}")
    if game_id not in games:
        print(f"Ошибка: Игра {game_id} не найдена")
        emit('error', {'message': 'Игра не найдена!'})
        return
    if games[game_id].creator_sid != request.sid:
        print(f"Ошибка: SID {request.sid} не является создателем игры {game_id}")
        emit('error', {'message': 'Только создатель может начать игру!'})
        return
    print(f"Запуск игры {game_id}")
    games[game_id].start_game()
    for pid, player in games[game_id].players.items():
        if player["connected"]:
            print(f"Отправка start игроку {pid} с SID {player['sid']}")
            socketio.emit('start', {'game_id': game_id, 'player_id': pid}, room=player['sid'])
    broadcast_games()

@socketio.on('end_game')
def handle_end_game(data):
    game_id = data['game_id']
    if game_id not in games or games[game_id].creator_sid != request.sid:
        emit('error', {'message': 'Только создатель может завершить игру!'})
        return
    games[game_id].end_game()
    del games[game_id]
    broadcast_games()

@socketio.on('play')
def handle_play(data):
    game_id = data['game_id']
    if game_id not in games:
        return
    is_winner, log_message = games[game_id].process_play(data['player_id'], data['cards'], data['operation'])
    if log_message:
        print(f"Успешный ход игрока {data['player_id']} в игре {game_id}")
        for pid, player in games[game_id].players.items():
            if player["connected"]:
                socketio.emit('log', {'message': log_message}, room=player['sid'])
        if is_winner:
            winner_name = games[game_id].players[data['player_id']]['name']
            games[game_id].players[data['player_id']]['wins'] += 1
            winner = f"Победил {winner_name}"
            players_wins = [
                {"name": p["name"], "wins": p.get("wins", 0)}
                for p in games[game_id].players.values() if p["connected"]
            ]
            for pid, player in games[game_id].players.items():
                if player["connected"]:
                    socketio.emit('win', {'winner': winner, 'players': players_wins}, room=player['sid'])
        else:
            games[game_id].update_all_players()
    else:
        print(f"Ошибка хода игрока {data['player_id']} в игре {game_id}")
        socketio.emit('error', {'message': 'Невозможно составить результат из выбранных карт и операции!'}, room=games[game_id].players[data['player_id']]['sid'])

@socketio.on('draw')
def handle_draw(data):
    game_id = data['game_id']
    if game_id not in games:
        return
    success, log_message = games[game_id].process_draw(data['player_id'])
    if success:
        for pid, player in games[game_id].players.items():
            if player["connected"]:
                socketio.emit('log', {'message': log_message}, room=player['sid'])
        games[game_id].update_all_players()
    else:
        socketio.emit('error', {'message': 'Не удалось взять карту!'}, room=games[game_id].players[data['player_id']]['sid'])

@socketio.on('chat_message')
def handle_chat_message(data):
    game_id = data['game_id']
    player_id = data['player_id']
    message = data['message']
    if game_id not in games or player_id not in games[game_id].players:
        return
    sender_name = games[game_id].players[player_id]['name']
    for pid, player in games[game_id].players.items():
        if player["connected"]:
            socketio.emit('chat_message', {
                'sender': sender_name,
                'message': message
            }, room=player['sid'])
    print(f"Сообщение в чате от {sender_name} в игре {game_id}: {message}")

@socketio.on('disconnect')
def handle_disconnect():
    print(f"Клиент с SID: {request.sid} отключился")
    for game_id, game in list(games.items()):
        if game.remove_player(request.sid):
            player_name = game.players[game.get_player_id_by_sid(request.sid)]['name'] if game.get_player_id_by_sid(request.sid) is not None else "Неизвестный"
            if (time.time() - game.creation_time) > 30 and not any(p["connected"] for p in game.players.values()):
                del games[game_id]
                print(f"Игра {game_id} удалена, так как все игроки отключились")
            elif not game.game_started:
                for pid, player in game.players.items():
                    if player["connected"]:
                        socketio.emit('player_joined', {'players': [p["name"] for p in game.players.values() if p["connected"]]}, room=player['sid'])
            else:
                for pid, player in game.players.items():
                    if player["connected"]:
                        socketio.emit('message', {'text': 'Один из игроков отключился.'}, room=player['sid'])
                        socketio.emit('chat_message', {
                            'sender': 'Система',
                            'message': f"{player_name} покинул игру"
                        }, room=player['sid'])
            broadcast_games()

# Запускаем фоновую задачу для очистки старых игр
cleanup_thread = threading.Thread(target=cleanup_old_games, daemon=True)
cleanup_thread.start()

from itertools import permutations
if __name__ == "__main__":
    print("Сервер запущен на http://0.0.0.0:5000")
    socketio.run(app, host='0.0.0.0', port=5000)