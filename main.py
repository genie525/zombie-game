import time
import random
from PIL import Image, ImageDraw, ImageOps
import config
import hardware

MAP_WIDTH = 720
MAP_HEIGHT = 480

def load_sprite_frames(path, scale=2):
    sheet = Image.open(path).convert("RGBA")
    num_frames = sheet.size[0] // 16
    frames_right, frames_left = [], []
    for i in range(num_frames):
        crop_box = (i * 16, 0, (i + 1) * 16, 16)
        frame = sheet.crop(crop_box).resize((16 * scale, 16 * scale), Image.NEAREST)
        frames_right.append(frame)
        frames_left.append(ImageOps.mirror(frame))
    return frames_right, frames_left

def spawn_human():
    # 720x480 맵 전역(상단 UI 제외 영역)에서 스폰 및 이동 방향 설정
    x = random.randint(40, MAP_WIDTH - 40)
    y = random.randint(config.UI_HEIGHT + 30, MAP_HEIGHT - 40)
    vx = random.choice([-2.2, -1.5, 1.5, 2.2])
    vy = random.uniform(-1.0, 1.0)
    return [x, y, vx, vy]

def main():
    disp = hardware.init_display()
    btns = hardware.init_inputs()

    image = Image.new("RGB", (config.WIDTH, config.HEIGHT))
    draw = ImageDraw.Draw(image)

    # [배경 설정] 720x480 새 배경 파일이 있다면 아래 한 줄의 주석(#)을 풀고 타일링 코드를 지우세요.
    # world_bg = Image.open("assests/background_720x480.png").convert("RGB").resize((MAP_WIDTH, MAP_HEIGHT))

    # 임시: 기존 240x240 배경을 가로 3칸 x 세로 2칸 이어 붙여 720x480 맵 구성
    base_bg = Image.open("assests/background_240.png").convert("RGB").resize((config.WIDTH, config.HEIGHT))
    world_bg = Image.new("RGB", (MAP_WIDTH, MAP_HEIGHT))
    for gx in range(3):
        for gy in range(2):
            world_bg.paste(base_bg, (gx * config.WIDTH, gy * config.HEIGHT))

    # 스프라이트 로드
    scale = 2
    sprite_size = 16 * scale
    zomb_right, zomb_left = load_sprite_frames("assests/newb_zomb_atk.png", scale=scale)
    human_right, human_left = load_sprite_frames("assests/knight_run16.png", scale=scale)

    # 맵 정중앙(360, 240)에서 좀비 시작
    zombie_x = MAP_WIDTH // 2 - sprite_size // 2
    zombie_y = MAP_HEIGHT // 2 - sprite_size // 2
    speed = 6
    facing = "RIGHT"
    walk_tick = 0.0
    walk_idx = 0

    hp = 100
    max_hp = 100
    exp = 0
    stage_names = ["1:NEWBIE", "2:NORMAL", "3:WARRIOR", "4:KING"]
    stage = 0

    human = spawn_human()
    human_tick = 0.0
    human_idx = 0

    attack_timer = 0.0
    attack_duration = 0.24
    attack_cooldown = 0.0
    idle_rest_timer = 0.0   # 1.5초 이상 가만히 있으면 자동 휴식 모드 진입
    is_resting = False
    game_over = False

    prev = time.monotonic()

    while True:
        now = time.monotonic()
        dt = now - prev
        prev = now

        if attack_timer > 0:
            attack_timer -= dt
        if attack_cooldown > 0:
            attack_cooldown -= dt

        if game_over:
            if not btns["CENTER"].value:
                hp = max_hp
                exp = 0
                stage = 0
                zombie_x = MAP_WIDTH // 2 - sprite_size // 2
                zombie_y = MAP_HEIGHT // 2 - sprite_size // 2
                human = spawn_human()
                is_resting = False
                idle_rest_timer = 0.0
                game_over = False
        else:
            moving = False
            if not btns["LEFT"].value:
                zombie_x -= speed
                facing = "LEFT"
                moving = True
            if not btns["RIGHT"].value:
                zombie_x += speed
                facing = "RIGHT"
                moving = True
            if not btns["UP"].value:
                zombie_y -= speed
                moving = True
            if not btns["DOWN"].value:
                zombie_y += speed
                moving = True

            # 720x480 맵 경계 제한
            zombie_x = max(8, min(MAP_WIDTH - sprite_size - 8, zombie_x))
            zombie_y = max(config.UI_HEIGHT + 4, min(MAP_HEIGHT - sprite_size - 8, zombie_y))

            # 이동하거나 공격하면 휴식 해제, 1.5초 이상 제자리 대기 시 휴식 회복
            if moving or not btns["CENTER"].value:
                idle_rest_timer = 0.0
                is_resting = False
            else:
                idle_rest_timer += dt
                if idle_rest_timer >= 1.5:
                    is_resting = True
                    hp = min(max_hp, hp + 10 * dt)  # 휴식 중 초당 10씩 회복

            if moving:
                walk_tick += dt
                if walk_tick >= 0.1:
                    walk_tick = 0.0
                    walk_idx = (walk_idx + 1) % 4
            else:
                walk_idx = 0

            # [사냥(공격)] CENTER 버튼 입력
            if not btns["CENTER"].value and attack_cooldown <= 0:
                attack_timer = attack_duration
                attack_cooldown = 0.45
                zx_center = zombie_x + sprite_size // 2
                zy_center = zombie_y + sprite_size // 2
                if abs(human[0] - zx_center) < 34 and abs(human[1] - zy_center) < 36:
                    exp += 20
                    human = spawn_human()
                    if exp >= 100 and stage == 0:
                        stage = 1
                        max_hp = 130
                        hp = max_hp

            # [시민 이동 및 맵 경계 반사]
            human[0] += human[2]
            human[1] += human[3]
            if human[0] < 24 or human[0] > MAP_WIDTH - 24:
                human[2] *= -1
            if human[1] < config.UI_HEIGHT + 20 or human[1] > MAP_HEIGHT - 24:
                human[3] *= -1

            human_tick += dt
            if human_tick >= 0.08:
                human_tick = 0.0
                human_idx = (human_idx + 1) % len(human_right)

            # [좀비-시민 피격 판정]
            zx_center = zombie_x + sprite_size // 2
            zy_center = zombie_y + sprite_size // 2
            if abs(human[0] - zx_center) < 18 and abs(human[1] - zy_center) < 20:
                damage = 30 if is_resting else 15
                hp = max(0, hp - damage)
                is_resting = False
                idle_rest_timer = 0.0
                human = spawn_human()
                if hp <= 0:
                    hp = 0
                    game_over = True

        # ================= 2D 카메라 위치 계산 (X, Y 모두 추적) =================
        cam_x = int(zombie_x + sprite_size // 2 - config.WIDTH // 2)
        cam_y = int(zombie_y + sprite_size // 2 - config.HEIGHT // 2)
        cam_x = max(0, min(MAP_WIDTH - config.WIDTH, cam_x))
        cam_y = max(0, min(MAP_HEIGHT - config.HEIGHT, cam_y))

        # ================= 화면 그리기 =================
        visible_bg = world_bg.crop((cam_x, cam_y, cam_x + config.WIDTH, cam_y + config.HEIGHT))
        image.paste(visible_bg, (0, 0))

        # 상단 고정 UI
        draw.rectangle((0, 0, config.WIDTH, config.UI_HEIGHT), fill=(30, 35, 45))
        draw.line((0, config.UI_HEIGHT, config.WIDTH, config.UI_HEIGHT), fill=(150, 160, 180))
        draw.text((6, 5), f"HP:{int(hp)}", fill=(255, 100, 100))
        hp_bar_w = int(60 * (hp / max_hp))
        draw.rectangle((52, 6, 52 + hp_bar_w, 14), fill=(220, 50, 50))
        draw.text((125, 5), f"EXP:{exp}", fill=(100, 220, 255))
        draw.text((6, 21), f"STAGE:{stage_names[stage]}", fill=(150, 255, 150))
        # 미니맵/현재 좌표 표시
        draw.text((145, 21), f"({int(zombie_x)},{int(zombie_y)})", fill=(200, 200, 200))

        # 좀비 그리기
        if attack_timer > 0:
            progress = 1.0 - (attack_timer / attack_duration)
            frame_idx = 4 + min(2, int(progress * 3))
        else:
            frame_idx = walk_idx

        current_zomb = zomb_right if facing == "RIGHT" else zomb_left
        zombie_sprite = current_zomb[frame_idx]
        screen_zx = int(zombie_x - cam_x)
        screen_zy = int(zombie_y - cam_y)
        image.paste(zombie_sprite, (screen_zx, screen_zy), zombie_sprite)

        if is_resting:
            draw.rectangle(
                (screen_zx - 3, screen_zy - 3, screen_zx + sprite_size + 3, screen_zy + sprite_size + 3),
                outline=(80, 180, 255), width=2
            )

        # 시민 그리기 (진행 방향에 따라 좌우 반전 적용)
        current_human = human_right if human[2] >= 0 else human_left
        human_sprite = current_human[human_idx]
        screen_hx = int(human[0] - sprite_size // 2 - cam_x)
        screen_hy = int(human[1] - sprite_size // 2 - cam_y)
        if -sprite_size <= screen_hx <= config.WIDTH and -sprite_size <= screen_hy <= config.HEIGHT:
            image.paste(human_sprite, (screen_hx, screen_hy), human_sprite)

        if game_over:
            draw.rectangle((30, 95, config.WIDTH - 30, 155), fill=(0, 0, 0), outline=(255, 60, 60), width=2)
            draw.text((75, 108), "GAME OVER", fill=(255, 60, 60))
            draw.text((52, 128), "Press CENTER to Retry", fill=(220, 220, 220))

        disp.image(image)

        elapsed = time.monotonic() - now
        sleep_time = (1.0 / config.FPS) - elapsed
        if sleep_time > 0:
            time.sleep(sleep_time)

if __name__ == "__main__":
    main()