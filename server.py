import socket
import json
import threading
import time
import random

WIDTH, HEIGHT = 800, 600
BALL_SPEED = 5
PADDLE_SPEED = 10
paddles = {0: 250, 1: 250}
scores = [0, 0]
ball = {"x": WIDTH//2, "y": HEIGHT//2, "vx": BALL_SPEED, "vy": BALL_SPEED}
clients = []
COUNTDOWN_START = 3  # секунди
countdown = COUNTDOWN_START
start_time = time.time()
def countdown_timer():
    global countdown, start_time
    while countdown > 0:
        time.sleep(1)
        countdown -= 1
    start_time = time.time()  # Початок гри після відліку

def handle_client(conn, pid):
    global paddles
    while True:
        try:
            data = conn.recv(64).decode()
            if data == "UP":
                paddles[pid] -= PADDLE_SPEED
            elif data == "DOWN":
                paddles[pid] += PADDLE_SPEED
        except:
            break

def ball_logic():
    global ball, scores, game_over, winner

    # Очікуємо завершення відліку
    while countdown > 0:
        time.sleep(0.016)
        data = json.dumps({
            "paddles": paddles,
            "ball": ball,
            "scores": scores,
            "countdown": countdown
        }) + "\n"
        for c in clients:
            try:
                c.send(data.encode())
            except:
                continue

    # Основна гра
    while not game_over:
        ball["x"] += ball["vx"]
        ball["y"] += ball["vy"]

        if ball["y"] <= 0 or ball["y"] >= HEIGHT:
            ball["vy"] *= -1

        if (ball["x"] <= 40 and paddles[0] <= ball["y"] <= paddles[0] + 100) or \
           (ball["x"] >= WIDTH - 40 and paddles[1] <= ball["y"] <= paddles[1] + 100):
            ball["vx"] *= -1

        if ball["x"] < 0:
            scores[1] += 1
            reset_ball()
        elif ball["x"] > WIDTH:
            scores[0] += 1
            reset_ball()

        # Перемога при 10 очках
        if scores[0] >= 10:
            game_over = True
            winner = 0
        elif scores[1] >= 10:
            game_over = True
            winner = 1

        data = json.dumps({
            "paddles": paddles,
            "ball": ball,
            "scores": scores,
            "countdown": 0,
            "winner": winner if game_over else None
        }) + "\n"
        for c in clients:
            try:
                c.send(data.encode())
            except:
                continue
        time.sleep(0.016)


def reset_ball():
    ball["x"], ball["y"] = WIDTH//2, HEIGHT//2
    ball["vx"] = BALL_SPEED * random.choice([-1, 1])
    ball["vy"] = BALL_SPEED * random.choice([-1, 1])

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(("localhost", 8081))
server.listen(2)

print("🎮 Server started")
for pid in range(2):
    conn, _ = server.accept()
    print(f"Player {pid} connected")
    clients.append(conn)
    threading.Thread(target=handle_client, args=(conn, pid), daemon=True).start()
game_over = False
winner = None

threading.Thread(target=countdown_timer, daemon=True).start()
threading.Thread(target=ball_logic, daemon=True).start()

while True:
    time.sleep(1)
