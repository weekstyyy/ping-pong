import pygame
from pygame import *
import socket
import json
from threading import Thread

# ---ПУГАМЕ НАЛАШТУВАННЯ ---
WIDTH, HEIGHT = 800, 600
init()
screen = display.set_mode((WIDTH, HEIGHT))
clock = time.Clock()
display.set_caption("Пінг-Понг")
# ---СЕРВЕР ---
def connect_to_server():
    while True:
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect(('localhost', 8080)) # ---- Підключення до сервера
            buffer = ""
            game_state = {}
            my_id = int(client.recv(24).decode())
            return my_id, game_state, buffer, client
        except:
            pass


def receive():
    global buffer, game_state, game_over
    while not game_over:
        try:
            data = client.recv(1024).decode()
            buffer += data
            while "\n" in buffer:
                packet, buffer = buffer.split("\n", 1)
                if packet.strip():
                    game_state = json.loads(packet)
        except:
            game_state["winner"] = -1
            break

# --- ШРИФТИ ---
font_win = font.Font(None, 72)
font_main = font.Font(None, 36)
# --- ЗОБРАЖЕННЯ ----
background = pygame.image.load("background.png").convert()

frame_img = pygame.image.load("frame.png").convert_alpha()
frame_img = pygame.transform.scale(frame_img, (240, 200))

platform_img = pygame.image.load("platform.png").convert_alpha()
platform_img = pygame.transform.scale(platform_img, (500, 450))

column1_img = pygame.image.load("column1.png").convert_alpha()
column1_img = pygame.transform.scale(column1_img, (80, 200))

column2_img = pygame.image.load("column2.png").convert_alpha()
column2_img = pygame.transform.scale(column2_img, (80, 200))

kitty_img = pygame.image.load("kitty.png").convert_alpha()
kitty_img = pygame.transform.scale(kitty_img, (130, 120))

eye_img = pygame.image.load("oko.png").convert_alpha()
eye_img = pygame.transform.scale(eye_img, (40, 40))

vine1_img = pygame.image.load("wine_vine1.png").convert_alpha()
vine1_img = pygame.transform.scale(vine1_img, (250, 250))

vine2_img = pygame.image.load("wine_vine2.png").convert_alpha()
vine2_img = pygame.transform.scale(vine2_img, (200, 300))
vine22_img = vine2_img
vine21_img = pygame.transform.scale(vine2_img, (275, 375))
vine21_img = pygame.transform.flip(vine21_img, True, False)
vine23_img = pygame.transform.scale(vine2_img, (170, 200))

vine3_img = pygame.image.load("wine_vine3.png").convert_alpha()
vine3_img = pygame.transform.scale(vine3_img, (250, 250))
vine3_img = pygame.transform.flip(vine3_img, True, False)

# --- ЗВУКИ ---

# --- ГРА ---
game_over = False
winner = None
you_winner = None
my_id, game_state, buffer, client = connect_to_server()
Thread(target=receive, daemon=True).start()
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
        screen.fill((20, 20, 20))

        if you_winner is None:  # Встановлюємо тільки один раз
            if game_state["winner"] == my_id:
                you_winner = True
            else:
                you_winner = False

        if you_winner:
            text = "Ти переміг!"
        else:
            text = "Пощастить наступним разом!"

        win_text = font_win.render(text, True, (255, 215, 0))
        text_rect = win_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        screen.blit(win_text, text_rect)

        text = font_win.render('К - рестарт', True, (255, 215, 0))
        text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 120))
        screen.blit(text, text_rect)

        display.update()
        continue  # Блокує гру після перемоги

    if game_state:
        # --- ОЧЕРЕДНОСТЬ СЛОЁВ (от дальнего к ближнему) ---

        # 1️⃣ ФОН
        screen.blit(background, (0, 0))

        # 2️⃣ ОСНОВНЫЕ ОБЪЕКТЫ ИГРЫ (платформа и колонны)
        screen.blit(platform_img, (150, 110))
        screen.blit(column1_img, (30, game_state['paddles']['0']))
        screen.blit(column2_img, (WIDTH - 110, game_state['paddles']['1']))

        # 4️⃣ КОТИК
        screen.blit(kitty_img, (225, 315))

        # 5️⃣
        screen.blit(frame_img, (220, 170))

        score_text = font_win.render(f"{game_state['scores'][0]} : {game_state['scores'][1]}", True, (255, 255, 255))
        screen.blit(score_text, (290, 240))

        # 3️⃣ МЯЧ (глаз)
        eye_x = game_state['ball']['x'] - eye_img.get_width() // 2
        eye_y = game_state['ball']['y'] - eye_img.get_height() // 2
        screen.blit(eye_img, (eye_x, eye_y))

        # 7️⃣ ЛОЗЫ (винные ветви — поверх всего)
        screen.blit(vine1_img, (-35, -35))
        screen.blit(vine1_img, (250, -35))
        screen.blit(vine22_img, (140, -70))
        screen.blit(vine3_img, (600, -35))
        screen.blit(vine21_img, (440, -70))
        screen.blit(vine23_img, (430, -70))

        if game_state['sound_event']:
            if game_state['sound_event'] == 'wall_hit':
                # звук відбиття м'ячика від стін
                pass
            if game_state['sound_event'] == 'platform_hit':
                # звук відбиття м'ячика від платформи
                pass

    else:
        wating_text = font_main.render(f"Очікування гравців...", True, (255, 255, 255))
        screen.blit(wating_text, (WIDTH // 2 - 25, 20))

    display.update()
    clock.tick(60)

    keys = key.get_pressed()
    if keys[K_w]:
        client.send(b"UP")
    elif keys[K_s]:
        client.send(b"DOWN")
