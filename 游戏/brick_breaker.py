"""
砖块破坏者 - 竖屏
球从顶部随机掉落 → 挡板接住弹回 → 打红色砖块 → 变蓝砖向下掉
蓝砖撞挡板 → 变两个白球弹回
灰色=城墙永久反弹  红色→蓝色→白球
"""
import sys
import random
import math
import pygame

pygame.init()

SW, SH = 500, 900
screen = pygame.display.set_mode((SW, SH))
pygame.display.set_caption("砖块破坏者")
clock = pygame.time.Clock()

# 颜色
BG = (15, 18, 45)
WHITE = (240, 240, 240)
GRAY = (110, 115, 130)
GRAY_D = (80, 85, 100)
GRAY_L = (140, 145, 160)
RED = (210, 45, 45)
RED_D = (170, 30, 30)
RED_L = (240, 70, 60)
BLUE = (50, 120, 220)
BLUE_D = (30, 90, 180)
BLUE_L = (80, 150, 255)
YELLOW = (240, 200, 40)
YELLOW_D = (200, 160, 20)
YELLOW_L = (255, 230, 80)


def font(sz, bold=False):
    for n in ['simhei', 'microsoftyahei']:   
        return pygame.font.SysFont(n, sz, bold=bold)            
    return pygame.font.Font(None, sz)


# 砖块参数       
BS = 13
BP = 1
CELL = BS + BP
COLS = SW // CELL
GW = COLS * CELL
GL = (SW - GW) // 2
GT = 8
ROWS = (SH // 2 - GT) // CELL

EMPTY, WALL, BRICK, BLUE_BRICK = 0, 1, 2, 3


def brect(r, c):
    return pygame.Rect(GL + c * CELL, GT + r * CELL, BS, BS)


# 爱心轮廓（小号版，下方开口）
def heart_outline():
    tpl = [
        "  xxxxxx  xxxxxx  ",
        " xxxxxxxxxxxxxxxx ",
        "xxxxxxxxxxxxxxxxxx",
        "xxxxxxxxxxxxxxxxxx",
        "xxxxxxxxxxxxxxxxxx",
        "xxxxxxxxxxxxxxxxxx",
        " xxxxxxxxxxxxxxxx ",
        "  xxxxxxxxxxxxxx  ",
        "   xxxxxxxxxxxx   ",
        "    xxxxxxxxxx    ",
        "     xxxxxxxx     ",
        "      xxxxxx      ",
        "       xxxx       ",
        "        xx        ",
    ]
    all_c = set()
    sr, sc = 3, 3
    for r, row in enumerate(tpl):
        for c, ch in enumerate(row):
            if ch == 'x':
                all_c.add((sr + r, sc + c))

    full_outline = set()
    for (r, c) in all_c:
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            if (r + dr, c + dc) not in all_c:
                full_outline.add((r, c))
                break

    # 下方开口：只保留上半部分轮廓
    heart_top = min(r for r, _ in all_c)
    heart_bot = max(r for r, _ in all_c)
    open_start = heart_top + (heart_bot - heart_top) * 2 // 3

    outline = set()
    for (r, c) in full_outline:
        if r < open_start:
            outline.add((r, c))

    return outline, all_c


# 音效
def beep(f, d, v):
    sr = 22050
    n = max(512, int(sr * d / 1000))
    buf = bytearray(n * 2)
    for i in range(n):
        t = i / sr
        env = max(0, 1 - t / (d / 1000))
        val = int(v * 32767 * math.sin(2 * math.pi * f * t) * env)
        val = max(-32768, min(32767, val))
        buf[i * 2] = val & 0xFF
        buf[i * 2 + 1] = (val >> 8) & 0xFF
    return pygame.mixer.Sound(buffer=bytes(buf))


s_hit = beep(520, 30, 0.1)
s_break = beep(780, 35, 0.12)
s_wall = beep(200, 25, 0.08)
s_die = beep(180, 150, 0.15)
s_spawn = beep(1000, 50, 0.08)


# ========== 网格 ==========
class Grid:
    def __init__(self):
        self.cells = self._make()

    def _make(self):
        # 全部填红色砖块
        g = [[BRICK] * COLS for _ in range(ROWS)]
        ol, al = heart_outline()

        # 爱心上半部分轮廓变灰色墙
        for r, c in ol:
            if 0 <= r < ROWS and 0 <= c < COLS:
                g[r][c] = WALL

        # 爱心底部到最底行：竖着的灰色通道（中间2格宽）
        heart_bot = max(r for r, _ in al)
        mid = COLS // 2
        for r in range(heart_bot + 1, ROWS - 1):
            g[r][mid - 1] = WALL
            g[r][mid + 2] = WALL
            g[r][mid] = EMPTY
            g[r][mid + 1] = EMPTY

        # 底部墙壁 + 洞口（2格宽，对齐通道）
        for c in range(COLS):
            g[ROWS - 1][c] = WALL
        g[ROWS - 1][mid] = EMPTY
        g[ROWS - 1][mid + 1] = EMPTY

        return g

    def get(self, r, c):
        if 0 <= r < ROWS and 0 <= c < COLS:
            return self.cells[r][c]
        return -1

    def remove(self, r, c):
        self.cells[r][c] = EMPTY

    def count(self):
        return sum(1 for r in range(ROWS) for c in range(COLS) if self.cells[r][c] == BRICK)

    def draw(self, s):
        for r in range(ROWS):
            for c in range(COLS):
                v = self.cells[r][c]
                if v == EMPTY:
                    continue
                rc = brect(r, c)
                if v == WALL:
                    pygame.draw.rect(s, GRAY, rc)
                    pygame.draw.rect(s, GRAY_D, rc, 1)
                    pygame.draw.line(s, GRAY_L, rc.topleft, rc.topright)
                    pygame.draw.line(s, GRAY_L, rc.topleft, rc.bottomleft)
                else:
                    pygame.draw.rect(s, RED, rc)
                    pygame.draw.rect(s, RED_D, rc, 1)
                    pygame.draw.line(s, RED_L, rc.topleft, rc.topright)
                    pygame.draw.line(s, RED_L, rc.topleft, rc.bottomleft)


# ========== 球 ==========
class Ball:
    def __init__(self, x, y, dx=0, dy=0):
        self.x, self.y = x, y
        self.dx, self.dy = dx, dy
        self.r = 5
        self.trail = []
        self.attached = True  # 贴在挡板上等待发射

    def update(self, dt, paddle_x=None, paddle_y=None):
        if self.attached and paddle_x is not None:
            self.x = paddle_x
            self.y = paddle_y - self.r - 2
            return
        self.trail.append((self.x, self.y))
        if len(self.trail) > 10:
            self.trail.pop(0)
        self.x += self.dx * dt
        self.y += self.dy * dt

        if self.x - self.r < 0:
            self.x = self.r
            self.dx = abs(self.dx)
        elif self.x + self.r > SW:
            self.x = SW - self.r
            self.dx = -abs(self.dx)
        if self.y - self.r < 0:
            self.y = self.r
            self.dy = abs(self.dy)

    def draw(self, s):
        for i, (tx, ty) in enumerate(self.trail):
            a = (i + 1) / len(self.trail)
            sz = max(2, int(3 * a))
            c = int(180 * a)
            pygame.draw.rect(s, (c, c, c), (int(tx) - sz // 2, int(ty) - sz // 2, sz, sz))
        pygame.draw.rect(s, WHITE, (int(self.x) - self.r, int(self.y) - self.r, self.r * 2, self.r * 2))


# ========== 挡板 ==========
class Paddle:
    def __init__(self):
        self.w, self.h = 130, 14
        self.x = SW / 2 - self.w / 2
        self.y = SH * 3 // 4

    def update(self, mx):
        self.x = mx - self.w / 2
        self.x = max(0, min(SW - self.w, self.x))

    def draw(self, s):
        r = pygame.Rect(int(self.x), int(self.y), self.w, self.h)
        pygame.draw.rect(s, WHITE, r)
        pygame.draw.rect(s, GRAY, (r.x, r.bottom - 3, r.w, 3))


# ========== 下落砖块（蓝色/黄色） ==========
class FallingBrick:
    def __init__(self, x, y, color='blue'):
        self.x, self.y = x, y
        self.origin_x, self.origin_y = x, y  # 原始红砖位置
        self.w, self.h = BS, BS
        self.dy = 180
        self.color = color
        self.ball_count = 3 if color == 'blue' else 5

    def update(self, dt):
        self.y += self.dy * dt

    def rect(self):
        return pygame.Rect(int(self.x - self.w // 2), int(self.y - self.h // 2), self.w, self.h)

    def draw(self, s):
        r = self.rect()
        if self.color == 'blue':
            pygame.draw.rect(s, BLUE, r)
            pygame.draw.rect(s, BLUE_D, r, 1)
            pygame.draw.line(s, BLUE_L, r.topleft, r.topright)
            pygame.draw.line(s, BLUE_L, r.topleft, r.bottomleft)
        else:
            pygame.draw.rect(s, YELLOW, r)
            pygame.draw.rect(s, YELLOW_D, r, 1)
            pygame.draw.line(s, YELLOW_L, r.topleft, r.topright)
            pygame.draw.line(s, YELLOW_L, r.topleft, r.bottomleft)


# ========== 游戏 ==========
class Game:
    def __init__(self):
        self.state = 'menu'
        self.score = 0
        self.reset()

    def reset(self):
        self.score = 0
        self.grid = Grid()
        self.paddle = Paddle()
        self.balls = []
        self.blue_bricks = []
        self.cheat_held = False
        self.spawn_ball()
        self.state = 'playing'

    @property
    def hole_pos(self):
        """洞口中心坐标（2格宽）"""
        mid = COLS // 2
        hx = GL + mid * CELL + CELL / 2
        hy = GT + (ROWS - 1) * CELL + BS / 2
        return hx, hy

    def spawn_ball(self):
        """球贴在挡板上等待发射"""
        x = self.paddle.x + self.paddle.w / 2
        y = self.paddle.y
        self.balls.append(Ball(x, y))

    def events(self):
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return False
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    return False
                if e.key == pygame.K_SPACE:
                    self.cheat_held = True
                if self.state == 'menu' and e.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self.reset()
                if self.state == 'playing' and e.key in (pygame.K_SPACE, pygame.K_UP):
                    for b in self.balls:
                        if b.attached:
                            b.attached = False
                            b.dy = -300
                            b.dx = random.uniform(-100, 100)
            if e.type == pygame.KEYUP:
                if e.key == pygame.K_SPACE:
                    self.cheat_held = False
            if e.type == pygame.MOUSEBUTTONDOWN:
                if self.state == 'menu':
                    self.reset()
                elif self.state == 'playing':
                    for b in self.balls:
                        if b.attached:
                            b.attached = False
                            b.dy = -300
                            b.dx = random.uniform(-100, 100)
        return True

    def collide(self, ball):
        """
        碰撞检测：灰色优先推开，红色才消除
        返回: None=无/灰墙, (x,y,'blue')=红色被消除位置
        """
        c1 = int((ball.x - ball.r - GL) / CELL)
        c2 = int((ball.x + ball.r - GL) / CELL)
        r1 = int((ball.y - ball.r - GT) / CELL)
        r2 = int((ball.y + ball.r - GT) / CELL)

        # 第一轮：只查灰色墙
        for r in range(max(0, r1), min(ROWS, r2 + 1)):
            for c in range(max(0, c1), min(COLS, c2 + 1)):
                if self.grid.get(r, c) != WALL:
                    continue
                rc = brect(r, c)
                if (ball.x + ball.r <= rc.left or ball.x - ball.r >= rc.right or
                        ball.y + ball.r <= rc.top or ball.y - ball.r >= rc.bottom):
                    continue

                ol = (ball.x + ball.r) - rc.left
                orr = rc.right - (ball.x - ball.r)
                ot = (ball.y + ball.r) - rc.top
                ob = rc.bottom - (ball.y - ball.r)
                mn = min(ol, orr, ot, ob)

                if mn == ol:
                    ball.x = rc.left - ball.r - 1
                    if ball.dx > 0: ball.dx = -ball.dx
                elif mn == orr:
                    ball.x = rc.right + ball.r + 1
                    if ball.dx < 0: ball.dx = -ball.dx
                elif mn == ot:
                    ball.y = rc.top - ball.r - 1
                    if ball.dy > 0: ball.dy = -ball.dy
                elif mn == ob:
                    ball.y = rc.bottom + ball.r + 1
                    if ball.dy < 0: ball.dy = -ball.dy

                s_wall.play()
                return None

        # 第二轮：只查红色砖块
        for r in range(max(0, r1), min(ROWS, r2 + 1)):
            for c in range(max(0, c1), min(COLS, c2 + 1)):
                if self.grid.get(r, c) != BRICK:
                    continue
                rc = brect(r, c)
                if (ball.x + ball.r <= rc.left or ball.x - ball.r >= rc.right or
                        ball.y + ball.r <= rc.top or ball.y - ball.r >= rc.bottom):
                    continue

                ol = (ball.x + ball.r) - rc.left
                orr = rc.right - (ball.x - ball.r)
                ot = (ball.y + ball.r) - rc.top
                ob = rc.bottom - (ball.y - ball.r)
                mn = min(ol, orr, ot, ob)
                if mn == ol or mn == orr:
                    ball.dx = -ball.dx
                if mn == ot or mn == ob:
                    ball.dy = -ball.dy

                self.grid.cells[r][c] = EMPTY
                self.score += 10
                s_break.play()
                return (rc.centerx, rc.centery, 'blue')

        return None

    def update(self, dt):
        if self.state != 'playing':
            return

        mx, _ = pygame.mouse.get_pos()
        self.paddle.update(mx)

        new_balls = []
        for ball in self.balls[:]:
            ball.update(dt, self.paddle.x + self.paddle.w / 2, self.paddle.y)

            if ball.attached:
                continue

            # 挡板反弹
            pr = pygame.Rect(int(self.paddle.x), int(self.paddle.y), self.paddle.w, self.paddle.h)
            if (ball.dy > 0 and
                    ball.y + ball.r >= pr.top and ball.y + ball.r <= pr.bottom + 8 and
                    ball.x >= pr.left - 2 and ball.x <= pr.right + 2):
                speed = max(math.sqrt(ball.dx ** 2 + ball.dy ** 2), 280)

                if self.cheat_held:
                    # 开挂：瞄准洞口飞去
                    hx, hy = self.hole_pos
                    dx = hx - ball.x
                    dy = hy - ball.y
                    dist = math.sqrt(dx * dx + dy * dy)
                    if dist > 0:
                        ball.dx = speed * dx / dist
                        ball.dy = speed * dy / dist
                else:
                    # 正常反弹
                    hit = (ball.x - pr.centerx) / (pr.w / 2)
                    hit = max(-0.95, min(0.95, hit))
                    ball.dx = speed * math.sin(hit * 1.15)
                    ball.dy = -speed * math.cos(hit * 1.15)

                ball.y = pr.top - ball.r
                s_hit.play()

            # 网格碰撞
            hit_result = self.collide(ball)
            if hit_result and len(self.balls) + len(new_balls) < 50:
                hx, hy, htype = hit_result
                if htype == 'blue':
                    # 红砖变下落砖块（随机蓝或黄）
                    color = random.choice(['blue', 'yellow'])
                    self.blue_bricks.append(FallingBrick(hx, hy, color))
                    s_spawn.play()

            # 掉出底部
            if ball.y - ball.r > SH:
                self.balls.remove(ball)
                s_die.play()

        self.balls.extend(new_balls)

        # 白球之间的碰撞
        for i in range(len(self.balls)):
            for j in range(i + 1, len(self.balls)):
                a, b = self.balls[i], self.balls[j]
                if a.attached or b.attached:
                    continue
                dx = b.x - a.x
                dy = b.y - a.y
                dist = math.sqrt(dx * dx + dy * dy)
                min_dist = a.r + b.r
                if dist < min_dist and dist > 0:
                    # 弹性碰撞：交换速度分量
                    nx, ny = dx / dist, dy / dist
                    dvx = a.dx - b.dx
                    dvy = a.dy - b.dy
                    dvn = dvx * nx + dvy * ny
                    if dvn > 0:
                        a.dx -= dvn * nx
                        a.dy -= dvn * ny
                        b.dx += dvn * nx
                        b.dy += dvn * ny
                    # 分开两个球
                    overlap = (min_dist - dist) / 2
                    a.x -= overlap * nx
                    a.y -= overlap * ny
                    b.x += overlap * nx
                    b.y += overlap * ny

        # 更新下落砖块
        pr = pygame.Rect(int(self.paddle.x), int(self.paddle.y), self.paddle.w, self.paddle.h)
        for bb in self.blue_bricks[:]:
            bb.update(dt)
            # 下落砖块撞到挡板
            if bb.rect().colliderect(pr):
                self.blue_bricks.remove(bb)
                speed = 300
                if bb.color == 'blue':
                    # 蓝色：在挡板位置分裂
                    sx, sy = bb.x, pr.top - 6
                else:
                    # 黄色：在原红砖位置分裂
                    sx, sy = bb.origin_x, bb.origin_y
                for _ in range(bb.ball_count):
                    a = random.uniform(-1.0, 1.0)
                    nb = Ball(sx, sy, speed * math.sin(a), -abs(speed * math.cos(a)))
                    nb.attached = False
                    self.balls.append(nb)
                s_hit.play()
            # 下落砖块掉出底部
            elif bb.y > SH + 20:
                self.blue_bricks.remove(bb)

        # 判断胜负
        if not self.balls:
            if self.grid.count() > 0:
                self.state = 'over'
            else:
                self.state = 'win'
        elif self.grid.count() <= 0:
            self.state = 'win'

    def draw(self):
        screen.fill(BG)

        if self.state == 'menu':
            self._menu()
        else:
            self.grid.draw(screen)
            for b in self.balls:
                b.draw(screen)
            for bb in self.blue_bricks:
                bb.draw(screen)
            self.paddle.draw(screen)
            fh = font(14)
            screen.blit(fh.render(str(self.score), True, WHITE), (6, 6))

            # 开挂模式提示
            if self.cheat_held:
                cheat_text = font(16, True).render("[开挂中] 瞄准洞口!", True, (255, 210, 60))
                screen.blit(cheat_text, cheat_text.get_rect(center=(SW / 2, SH - 30)))

            if self.state == 'over':
                self._overlay("GAME OVER", f"得分: {self.score}")
            elif self.state == 'win':
                self._overlay("YOU WIN!", f"得分: {self.score}")

        pygame.display.flip()

    def _menu(self):
        t1 = font(42, True).render("砖块破坏者", True, (255, 210, 60))
        screen.blit(t1, t1.get_rect(center=(SW / 2, 200)))
        t2 = font(18).render("球从顶部掉落，挡板接住弹回", True, WHITE)
        screen.blit(t2, t2.get_rect(center=(SW / 2, 260)))
        t3 = font(18).render("红砖→蓝(3球)或黄(5球)向下掉", True, GRAY)
        screen.blit(t3, t3.get_rect(center=(SW / 2, 300)))
        t4 = font(18).render("鼠标控制挡板", True, GRAY)
        screen.blit(t4, t4.get_rect(center=(SW / 2, 340)))
        t5 = font(18).render("按住空格键开挂：球瞄准洞口", True, (255, 210, 60))
        screen.blit(t5, t5.get_rect(center=(SW / 2, 380)))
        if int(pygame.time.get_ticks() / 500) % 2:
            t5 = font(22).render("按回车或点击开始", True, WHITE)
            screen.blit(t5, t5.get_rect(center=(SW / 2, 500)))

    def _overlay(self, t1, t2):
        ov = pygame.Surface((SW, SH), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 150))
        screen.blit(ov, (0, 0))
        screen.blit(font(42, True).render(t1, True, (255, 210, 60)),
                     font(42, True).get_rect(center=(SW / 2, SH / 2 - 20)))
        screen.blit(font(20).render(t2, True, WHITE),
                     font(20).get_rect(center=(SW / 2, SH / 2 + 25)))

    def run(self):
        ok = True
        while ok:
            dt = min(clock.tick(60) / 1000.0, 0.04)
            ok = self.events()
            self.update(dt)
            self.draw()
        pygame.quit()
        sys.exit()


Game().run()
