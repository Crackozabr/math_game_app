import random
import tkinter as tk
from tkinter import messagebox
from itertools import permutations
from collections import Counter

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

# Создание колоды ответов с 20 самыми популярными результатами
def create_answer_deck():
    number_deck = create_number_deck()
    all_results = []

    # Собираем все возможные результаты
    for i in range(len(number_deck)):
        for j in range(i + 1, len(number_deck)):
            pair = [number_deck[i], number_deck[j]]
            all_results.extend(calculate_combinations(pair))
            for k in range(j + 1, len(number_deck)):
                triplet = [number_deck[i], number_deck[j], number_deck[k]]
                all_results.extend(calculate_combinations(triplet))

    # Подсчитываем частоту каждого результата
    result_counts = Counter(all_results)
    
    # Берем 20 самых популярных результатов
    top_20 = result_counts.most_common(20)
    total_frequency = sum(count for _, count in top_20)
    
    # Распределяем 100 карт пропорционально частоте
    answer_deck = []
    for result, count in top_20:
        # Пропорциональное количество карт для каждого результата
        proportion = count / total_frequency
        num_cards = max(1, round(proportion * 100))  # Минимум 1 карта
        answer_deck.extend([result] * num_cards)

    # Обрезаем или дополняем до 100 карт
    if len(answer_deck) > 100:
        answer_deck = answer_deck[:100]
    elif len(answer_deck) < 100:
        # Дополняем самым популярным результатом
        extra_needed = 100 - len(answer_deck)
        answer_deck.extend([top_20[0][0]] * extra_needed)

    random.shuffle(answer_deck)
    return answer_deck

# Класс игрока
class Player:
    def __init__(self, name):
        self.name = name
        self.hand = []
        self.score_pile = []

    def draw_cards(self, deck, count):
        for _ in range(count):
            if deck:
                self.hand.append(deck.pop(0))
            else:
                return False
        return True

# Класс игры с графическим интерфейсом
class CardGameGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Математическая карточная игра")

        # Инициализация игры
        self.number_deck = create_number_deck()
        self.answer_deck = create_answer_deck()
        self.discard_pile = []
        self.players = [Player("Игрок 1"), Player("Игрок 2")]
        self.current_player_idx = 0
        for player in self.players:
            player.draw_cards(self.number_deck, 5)
        self.table_cards = [self.answer_deck.pop(0) for _ in range(5)]

        # Интерфейс
        self.create_widgets()
        self.update_display()

    def create_widgets(self):
        self.table_frame = tk.LabelFrame(self.root, text="Карты на столе", padx=10, pady=10)
        self.table_frame.pack(padx=10, pady=10)
        self.table_labels = [tk.Label(self.table_frame, text="", width=5, relief="raised") for _ in range(5)]
        for i, label in enumerate(self.table_labels):
            label.grid(row=0, column=i, padx=5)

        self.hand_frame = tk.LabelFrame(self.root, text="Ваши карты", padx=10, pady=10)
        self.hand_frame.pack(padx=10, pady=10)
        self.hand_buttons = []
        self.hand_vars = []

        self.operation_frame = tk.LabelFrame(self.root, text="Выберите операцию", padx=10, pady=10)
        self.operation_frame.pack(padx=10, pady=10)
        self.operations = ["Сложить", "Умножить", "(A+B)*C", "A*B+C"]
        self.operation_var = tk.StringVar(value=self.operations[0])
        for op in self.operations:
            tk.Radiobutton(self.operation_frame, text=op, variable=self.operation_var, value=op).pack(side=tk.LEFT)

        self.action_frame = tk.Frame(self.root)
        self.action_frame.pack(padx=10, pady=10)
        tk.Button(self.action_frame, text="Выложить карты", command=self.play_cards).pack(side=tk.LEFT, padx=5)
        tk.Button(self.action_frame, text="Взять карту", command=self.draw_card).pack(side=tk.LEFT, padx=5)

        self.info_label = tk.Label(self.root, text="", font=("Arial", 12))
        self.info_label.pack(pady=10)

    def update_display(self):
        for i, card in enumerate(self.table_cards):
            self.table_labels[i].config(text=str(card))

        for btn in self.hand_buttons:
            btn.destroy()
        self.hand_buttons = []
        self.hand_vars = []
        for i, card in enumerate(self.players[self.current_player_idx].hand):
            var = tk.BooleanVar()
            btn = tk.Checkbutton(self.hand_frame, text=str(card), font=("Arial", 12), variable=var)
            btn.grid(row=0, column=i, padx=5)
            self.hand_buttons.append(btn)
            self.hand_vars.append(var)

        current_player = self.players[self.current_player_idx]
        self.hand_frame.config(text=f"Карты {current_player.name}")
        self.info_label.config(text=f"Ход: {current_player.name} | Собрано карт: {len(current_player.score_pile)}")

    def play_cards(self):
        selected_cards = [int(btn.cget("text")) for btn, var in zip(self.hand_buttons, self.hand_vars) if var.get()]
        if len(selected_cards) not in [2, 3]:
            messagebox.showwarning("Ошибка", "Выберите 2 или 3 карты!")
            return

        operation = self.operation_var.get()
        valid_result = None

        if len(selected_cards) == 2:
            for a, b in permutations(selected_cards, 2):
                if operation == "Сложить" and a + b in self.table_cards:
                    valid_result = a + b
                    break
                elif operation == "Умножить" and a * b in self.table_cards:
                    valid_result = a * b
                    break
                elif operation in ["(A+B)*C", "A*B+C"]:
                    messagebox.showwarning("Ошибка", "Для двух карт доступны только сложение или умножение!")
                    return
        else:  # 3 карты
            for a, b, c in permutations(selected_cards, 3):
                if operation == "Сложить" and a + b + c in self.table_cards:
                    valid_result = a + b + c
                    break
                elif operation == "Умножить" and a * b * c in self.table_cards:
                    valid_result = a * b * c
                    break
                elif operation == "(A+B)*C" and (a + b) * c in self.table_cards:
                    valid_result = (a + b) * c
                    break
                elif operation == "A*B+C" and a * b + c in self.table_cards:
                    valid_result = a * b + c
                    break

        if valid_result is not None:
            current_player = self.players[self.current_player_idx]
            for card in selected_cards:
                current_player.hand.remove(card)
            self.table_cards.remove(valid_result)
            current_player.score_pile.append(valid_result)

            if len(current_player.score_pile) >= 5:
                messagebox.showinfo("Победа", f"{current_player.name} победил!")
                self.root.quit()
                return

            current_player.draw_cards(self.number_deck, 5 - len(current_player.hand))
            while len(self.table_cards) < 5 and self.answer_deck:
                self.table_cards.append(self.answer_deck.pop(0))
            if not self.number_deck and self.discard_pile:
                self.number_deck.extend(self.discard_pile)
                random.shuffle(self.number_deck)
                self.discard_pile.clear()

            self.current_player_idx = (self.current_player_idx + 1) % 2
            self.update_display()
        else:
            messagebox.showwarning("Ошибка", "Результат не совпадает с картой на столе!")

    def draw_card(self):
        current_player = self.players[self.current_player_idx]
        if not current_player.draw_cards(self.number_deck, 1):
            if self.discard_pile:
                self.number_deck.extend(self.discard_pile)
                random.shuffle(self.number_deck)
                self.discard_pile.clear()
                current_player.draw_cards(self.number_deck, 1)
            else:
                messagebox.showinfo("Конец", "Карты закончились!")
                self.root.quit()
                return
        self.current_player_idx = (self.current_player_idx + 1) % 2
        self.update_display()

# Запуск игры
if __name__ == "__main__":
    root = tk.Tk()
    app = CardGameGUI(root)
    root.mainloop()