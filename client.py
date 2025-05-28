from pygame import *
import socket
import json
from threading import Thread

WIDTH, HEIGHT = 800, 600
init()
screen = display.set_mode((WIDTH, HEIGHT))
display.set_caption("Пінг-Понг")

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(('localhost', 8081))
buffer = ""
game_state = {}

def receive():
    global buffer, game_state
    while True:
        try:
            data = client.recv(1024).decode()
            buffer += data
            while "\n" in buffer:
                packet, buffer = buffer.split("\n", 1)
                if packet.strip():
                    game_state = json.loads(packet)
        except:
            break

Thread(target=receive, daemon=True).start()

font_main = font.SysFont(None, 36)
clock = time.Clock()

game_over = False
winner = None

while True:
    for e in event.get():
        if e.type == QUIT:
            exit()

    if "countdown" in game_state and game_state["countdown"] > 0:
        screen.fill((0, 0, 0))
        countdown_text = font.Font(None, 72).render(str(game_state["countdown"]), True, (255, 255, 255))
        screen.blit(countdown_text, (WIDTH // 2 - 20, HEIGHT // 2 - 30))
        display.update()
        continue  # Не малюємо гру до завершення відліку

    if "winner" in game_state and game_state["winner"] is not None:
        win_text = font.Font(None, 72).render(f"Гравець {game_state['winner']} переміг!", True, (255, 215, 0))
        screen.blit(win_text, (WIDTH // 2 - 200, HEIGHT // 2 - 50))
        display.update()
        continue  # Блокує гру після перемоги

    if game_state:
        screen.fill((30, 30, 30))
        draw.rect(screen, (0, 255, 0), (20, game_state['paddles']['0'], 20, 100))
        draw.rect(screen, (255, 0, 255), (WIDTH - 40, game_state['paddles']['1'], 20, 100))
        draw.circle(screen, (255, 255, 255), (game_state['ball']['x'], game_state['ball']['y']), 10)

        score_text = font_main.render(f"{game_state['scores'][0]} : {game_state['scores'][1]}", True, (255, 255, 255))
        screen.blit(score_text, (WIDTH // 2 - 40, 20))

    display.update()
    clock.tick(60)

    keys = key.get_pressed()
    if keys[K_w]:
        client.send(b"UP")
    elif keys[K_s]:
        client.send(b"DOWN")
