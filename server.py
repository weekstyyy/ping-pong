import socket
import json
import threading
import time
import random

# --- основные настройки ---
width, height = 800, 600
ball_speed = 5
paddle_speed = 10
countdown_start = 3

# --- параметры объектов ---
column_width = 80
column_height = 200
column1_x = 30
column2_x = width - 110

# --- параметры платформы (камня) ---
platform_y = 450
# верхняя зона
platform_hit_top = platform_y + 20
platform_hit_bottom = platform_y + 70
# нижняя зона — где отскакивает мяч от пола
platform_hit_floor = platform_y + 120  # примерно середина светло-серой части
platform_left = 150
platform_right = platform_left + 500


class GameServer:
    def __init__(self, host='localhost', port=8080):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((host, port))
        self.server.listen(2)
        print("🎮 Сервер запущен. Очікування гравців...")

        self.clients = {0: None, 1: None}
        self.connected = {0: False, 1: False}
        self.lock = threading.Lock()

        self.reset_game_state()
        self.sound_event = None

    # --- сброс состояния ---
    def reset_game_state(self):
        self.paddles = {0: 250, 1: 250}
        self.scores = [0, 0]
        self.ball = {
            "x": width // 2,
            "y": height // 2,
            "vx": ball_speed * random.choice([-1, 1]),
            "vy": ball_speed * random.choice([-1, 1])
        }
        self.countdown = countdown_start
        self.game_over = False
        self.winner = None

    # --- управление игроком ---
    def handle_client(self, pid):
        conn = self.clients[pid]
        try:
            while True:
                data = conn.recv(64).decode()
                with self.lock:
                    if data == "UP":
                        self.paddles[pid] = max(60, self.paddles[pid] - paddle_speed)
                    elif data == "DOWN":
                        self.paddles[pid] = min(height - column_height, self.paddles[pid] + paddle_speed)
        except:
            with self.lock:
                self.connected[pid] = False
                self.game_over = True
                self.winner = 1 - pid
                print(f"⚠️ Гравець {pid} відключився. Переміг гравець {1 - pid}.")

    # --- отправка состояния клиентам ---
    def broadcast_state(self):
        state = json.dumps({
            "paddles": self.paddles,
            "ball": self.ball,
            "scores": self.scores,
            "countdown": max(self.countdown, 0),
            "winner": self.winner if self.game_over else None,
            "sound_event": self.sound_event
        }) + "\n"

        for pid, conn in self.clients.items():
            if conn:
                try:
                    conn.sendall(state.encode())
                except:
                    self.connected[pid] = False

    # --- логика мяча ---
    def ball_logic(self):
        # ✅ обратный отсчёт только в начале игры
        while self.countdown > 0:
            time.sleep(1)
            with self.lock:
                self.countdown -= 1
                self.broadcast_state()

        while not self.game_over:
            with self.lock:
                bx, by = self.ball["x"], self.ball["y"]
                vx, vy = self.ball["vx"], self.ball["vy"]

                bx += vx
                by += vy

                # --- отскок от верха ---
                if by <= 60:
                    by = 60
                    vy *= -1
                    self.sound_event = "wall_hit"

                # --- отскок от колонн ---
                left_rect = (column1_x, self.paddles[0], column_width, column_height)
                right_rect = (column2_x, self.paddles[1], column_width, column_height)

                if (left_rect[0] <= bx <= left_rect[0] + left_rect[2] and
                    left_rect[1] <= by <= left_rect[1] + left_rect[3]):
                    bx = left_rect[0] + left_rect[2] + 1
                    vx = abs(vx)
                    self.sound_event = "platform_hit"

                if (right_rect[0] <= bx <= right_rect[0] + right_rect[2] and
                    right_rect[1] <= by <= right_rect[1] + right_rect[3]):
                    bx = right_rect[0] - 1
                    vx = -abs(vx)
                    self.sound_event = "platform_hit"

                # --- отскок от верхней части платформы ---
                if platform_left <= bx <= platform_right:
                    if platform_hit_top <= by <= platform_hit_bottom and vy > 0:
                        by = platform_hit_top - 1
                        vy *= -1
                        self.sound_event = "platform_hit"

                # --- отскок от нижней части платформы (пола) ---
                if platform_left <= bx <= platform_right:
                    if by >= platform_hit_floor and vy > 0:
                        by = platform_hit_floor - 1
                        vy *= -1
                        self.sound_event = "platform_hit"

                # --- если мяч улетел ---
                if bx < 0:
                    self.scores[1] += 1
                    self.reset_ball()  # ⚙️ теперь без отсчёта
                    continue
                elif bx > width:
                    self.scores[0] += 1
                    self.reset_ball()  # ⚙️ теперь без отсчёта
                    continue

                # --- проверка победы ---
                if self.scores[0] >= 10:
                    self.game_over = True
                    self.winner = 0
                elif self.scores[1] >= 10:
                    self.game_over = True
                    self.winner = 1

                # обновляем
                self.ball["x"], self.ball["y"] = bx, by
                self.ball["vx"], self.ball["vy"] = vx, vy

                self.broadcast_state()
                self.sound_event = None

            time.sleep(0.016)

    # --- сброс мяча ---
    def reset_ball(self):
        self.ball = {
            "x": width // 2,
            "y": height // 2,
            "vx": ball_speed * random.choice([-1, 1]),
            "vy": ball_speed * random.choice([-1, 1])
        }
        # ❌ убрали self.countdown = 2
        self.broadcast_state()

    # --- приём игроков ---
    def accept_players(self):
        for pid in [0, 1]:
            print(f"Очікуємо гравця {pid}...")
            conn, _ = self.server.accept()
            self.clients[pid] = conn
            conn.sendall((str(pid) + "\n").encode())
            self.connected[pid] = True
            print(f"✅ Гравець {pid} приєднався.")
            threading.Thread(target=self.handle_client, args=(pid,), daemon=True).start()

    # --- основной цикл ---
    def run(self):
        while True:
            self.accept_players()
            self.reset_game_state()
            threading.Thread(target=self.ball_logic, daemon=True).start()

            while not self.game_over and all(self.connected.values()):
                time.sleep(0.1)

            print(f"🏁 Гравець {self.winner} переміг!")
            time.sleep(3)

            for pid in [0, 1]:
                try:
                    self.clients[pid].close()
                except:
                    pass
                self.clients[pid] = None
                self.connected[pid] = False


if __name__ == "__main__":
    GameServer().run()
