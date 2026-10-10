# -*- coding: utf-8 -*-
r"""
生成程序图标（透明底）
作者：@wenhao

产出三套图标，用途不同：

1) 桌面 / 安装包 / 便携版 exe 的文件图标 —— icon.ico
   - assets/icon.png  256×256 透明底
   - assets/icon.ico  多尺寸：16/20/24/32/48/64/128/256

2) 程序运行时的窗口图标（系统标题栏左上角 / 任务栏 / 托盘）—— icon_app.ico
   - assets/icon_app.png  256×256 透明底
   - assets/icon_app.ico  多尺寸（与 icon.ico 同源同内容）

3) 主界面顶栏右上角「头像菜单」图标 —— icon_gear.png
   - assets/icon_gear.png  256×256 透明底（中性灰齿轮）
   母图 assets/settings_source.png。**本套从来不跟着换。**

主图标母图有两种，用 ICON_MODE 切换
------------------------------------
"ball"（当前，v1.1.6 起）
    母图 assets/power_source.png —— 用户给的**透明底蓝色电源开关球**。
    本身就是个圆球、圆外已透明，所以**不需要套遮罩**，只要
    「按实测圆心/半径裁一个正方形」即可。见 ball_variant()。

"square"
    母图 assets/desktop_source.jpg —— 早先的白底「时钟 + 电源键」圆角方图。
    要额外套正圆遮罩（v1.1.5 方案），见 circle_variant()。

    ⚠️ 用户对图标形状反复改过：v1.1.4 方形 → v1.1.5 圆形 → v1.1.6 换球体。
    两套都留着，切换只改 ICON_MODE 一个常量，别把另一套删掉。

几何实测（都不是猜的）
----------------------
square 母图：
  · 方块 (94,82)~(1160,1159)，边长 1067，圆角半径 249（扫描 + 最小二乘拟合，RMS 0.3~0.4px）
  · 图案本体包围盒 (260,212,1040,945) → 中心 (650, 578.5)，比方块中心偏右上 (dx+23, dy-42)
  · 圆形裁切以**图案中心**为圆心，半径 480（受「圆心到方块四边最短距离」约束）

ball 母图（1254²，RGBA，四角 alpha=0）：
  · 用「径向 alpha 剖面取中位数半径」避开底部阴影干扰，4 次迭代收敛：
    圆心 (612.72, 614.38)，半径 528.75（直径 1057.5）
  · 径向半径中位 527.2、最小 522.2、最大 537.7（上下略长 1.3%，属母图绘制差异）
  · 直接量 bbox 会被底部阴影骗到（bbox 高 1071 > 宽 1048），所以不能用 bbox 定圆

用法：
    .venv\Scripts\python.exe tools\make_icon.py           # 生成三套图标 + 自查图
    .venv\Scripts\python.exe tools\make_icon.py preview   # 只生成候选对比图
    .venv\Scripts\python.exe tools\make_icon.py probe     # 只做几何自检，不写文件
"""
import math
import os
import sys

from PIL import Image, ImageDraw, ImageEnhance

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ASSETS = os.path.join(ROOT, "assets")

# ---------------------------------------------------------------- 主图标母图模式
ICON_MODE = "ball"          # "ball"（透明底电源开关球）| "square"（白底圆角方图）

BALL_SRC = os.path.join(ASSETS, "power_source.png")        # 透明底圆球母图
SQUARE_SRC = os.path.join(ASSETS, "desktop_source.jpg")    # 白底方图母图
SQUARE_PNG = os.path.join(ASSETS, "desktop_source.png")    # 若已抠好透明底则优先
GEAR_SRC = os.path.join(ASSETS, "settings_source.png")     # 顶栏头像母图

# ---------------------------------------------------------------- square 模式几何（实测）
SQUARE_L, SQUARE_T, SQUARE_R, SQUARE_B = 94, 82, 1160, 1159
PATTERN_BOX = (260, 212, 1040, 945)
PATTERN_CX = (PATTERN_BOX[0] + PATTERN_BOX[2]) / 2.0      # 650.0
PATTERN_CY = (PATTERN_BOX[1] + PATTERN_BOX[3]) / 2.0      # 578.5
CIRCLE_CX = PATTERN_CX
CIRCLE_CY = PATTERN_CY
CIRCLE_R = 480

# ---------------------------------------------------------------- ball 模式几何（实测）
BALL_CX, BALL_CY, BALL_R = 612.72, 614.38, 528.75
# 球体直径占画布边长的比例。1.00 = 球刚好顶满画布；留 6% 让球外还有一圈呼吸空间，
# 大尺寸不会显得「撑到边上」，小尺寸的柔和外缘也不会被画布硬边切掉。
BALL_FILL = 0.94

ICON_SIZES = [16, 20, 24, 32, 48, 64, 128, 256]

# 小尺寸增强：只作用于 RGB，**不动 alpha**（否则会把圆球的柔和外缘推成硬边）
#   ≤32px 球体缩到这么小时白色电源图案会发糊，加对比 + 锐化最有效（放大 9 倍对比过）
#   ≤64px 只加一点锐化
ENHANCE_STRONG = 32
ENHANCE_MID = 64


# ================================================================ 通用工具
def _square_rgb():
    if os.path.exists(SQUARE_PNG):
        return Image.open(SQUARE_PNG).convert("RGB")
    return Image.open(SQUARE_SRC).convert("RGB")


def _circle_mask(side, ss=4):
    """正圆遮罩，4 倍超采样抗锯齿。"""
    m = Image.new("L", (side * ss, side * ss), 0)
    ImageDraw.Draw(m).ellipse((0, 0, side * ss - 1, side * ss - 1), fill=255)
    return m.resize((side, side), Image.LANCZOS)


def _enhance_rgb_only(im, contrast=1.0, sharpness=1.0):
    """只增强 RGB，保持 alpha 不变。

    为什么不直接 ImageEnhance.Contrast(im)：PIL 对 RGBA 会把常数图混合到
    **所有**通道（含 alpha），半透明边缘会被推向两端 —— 这里的圆球外缘本来
    就是柔和渐隐，硬推会切出一道生硬的边。
    """
    r, g, b, a = im.split()
    rgb = Image.merge("RGB", (r, g, b))
    if contrast != 1.0:
        rgb = ImageEnhance.Contrast(rgb).enhance(contrast)
    if sharpness != 1.0:
        rgb = ImageEnhance.Sharpness(rgb).enhance(sharpness)
    r2, g2, b2 = rgb.split()
    return Image.merge("RGBA", (r2, g2, b2, a))


def icon_at(size, src=None):
    """缩放到指定尺寸；小尺寸做 RGB 增强，保证可辨识。"""
    src = src if src is not None else current_variant()
    icon = src.resize((size, size), Image.LANCZOS)
    if size <= ENHANCE_STRONG:
        icon = _enhance_rgb_only(icon, contrast=1.10, sharpness=1.30)
    elif size <= ENHANCE_MID:
        icon = _enhance_rgb_only(icon, sharpness=1.12)
    return icon


def _save_ico(frames, path):
    try:
        frames[-1].save(path, format="ICO",
                        sizes=[(f.width, f.height) for f in frames],
                        append_images=frames[:-1])
    except TypeError:
        frames[-1].save(path, format="ICO", sizes=[(f.width, f.height) for f in frames])
    print("%s -> %s %s" % (os.path.basename(path), path,
                           [(f.width, f.height) for f in frames]))


# ================================================================ ball 模式（当前）
def ball_variant(cx=None, cy=None, r=None, fill=None):
    """把透明底圆球母图裁成正方形画布（球居中、四周留一点余量）。

    母图本身已是圆球 + 圆外透明，所以**不需要套遮罩**，
    裁切方框的四边中点刚好落在球外的透明区（已由 probe 断言）。
    """
    cx = BALL_CX if cx is None else cx
    cy = BALL_CY if cy is None else cy
    r = BALL_R if r is None else r
    fill = BALL_FILL if fill is None else fill
    half = r / fill
    left = int(round(cx - half))
    top = int(round(cy - half))
    side = int(round(2 * half))
    im = Image.open(BALL_SRC).convert("RGBA")
    return im.crop((left, top, left + side, top + side))


# ================================================================ square 模式（备选）
def circle_variant(cx=None, cy=None, r=None):
    """把白底圆角方图裁成圆形（圆外透明），图案在圆内居中。"""
    cx = CIRCLE_CX if cx is None else cx
    cy = CIRCLE_CY if cy is None else cy
    r = CIRCLE_R if r is None else r
    src = _square_rgb()
    left = int(round(cx - r))
    top = int(round(cy - r))
    im = src.crop((left, top, left + 2 * r, top + 2 * r)).convert("RGBA")
    im.putalpha(_circle_mask(im.width))
    return im


def current_variant():
    return ball_variant() if ICON_MODE == "ball" else circle_variant()


def mode_desc():
    return "透明底电源开关球（ball）" if ICON_MODE == "ball" else "白底方图裁圆（square）"


# ================================================================ 顶栏头像（不变）
def gear_variant():
    """顶栏右上角「头像菜单」用的设置齿轮。

    母图 assets/settings_source.png 本身就是透明底 + 中性灰齿轮，
    直接按 alpha 内容框裁成正方形即可。保留中性灰：浅色/深色顶栏下都能看清。
    """
    if not os.path.exists(GEAR_SRC):
        return None
    im = Image.open(GEAR_SRC).convert("RGBA")
    box = im.split()[3].getbbox()
    if box is None:
        return im
    im = im.crop(box)
    side = max(im.size)
    pad = max(1, int(side * 0.02))
    out_side = side + pad * 2
    canvas = Image.new("RGBA", (out_side, out_side), (0, 0, 0, 0))
    canvas.paste(im, ((out_side - im.width) // 2, (out_side - im.height) // 2), im)
    return canvas


# ================================================================ 几何自检
def _probe_ball(verbose=True):
    """ball 模式自检：确认圆心/半径测得准、裁切不越界、球没被切。"""
    ok = True
    lines = []

    def add(flag, text):
        nonlocal ok
        if not flag:
            ok = False
        lines.append(("  " if flag else "! ") + text)

    if not os.path.exists(BALL_SRC):
        add(False, "缺少母图 %s" % BALL_SRC)
        if verbose:
            for ln in lines:
                print(ln)
        return ok, lines

    im = Image.open(BALL_SRC).convert("RGBA")
    W, H = im.size
    alpha = im.getchannel("A")

    # ① 母图必须是透明底（四角 alpha = 0），否则别指望图标没有白框
    corners = [alpha.getpixel(p) for p in ((0, 0), (W - 1, 0), (0, H - 1), (W - 1, H - 1))]
    add(max(corners) == 0, "母图 %dx%d 四角 alpha=%s（全 0 才说明是透明底）" % (W, H, corners))

    # ② 径向 alpha 剖面：中位半径要与实测半径一致（标定是否还成立）
    px = im.load()
    radii = []
    for i in range(0, 360, 2):
        a = math.radians(i)
        ca, sa = math.cos(a), math.sin(a)
        lo, hi = 0.0, float(max(W, H))
        r = 0.0
        hit = False
        while r < max(W, H):
            x, y = int(round(BALL_CX + ca * r)), int(round(BALL_CY + sa * r))
            inside = (0 <= x < W and 0 <= y < H and px[x, y][3] >= 128)
            if not inside:
                hi = r
                hit = True
                break
            lo = r
            r += 1.0
        if not hit:
            continue
        for _ in range(18):
            mid = (lo + hi) / 2.0
            x, y = int(round(BALL_CX + ca * mid)), int(round(BALL_CY + sa * mid))
            if 0 <= x < W and 0 <= y < H and px[x, y][3] >= 128:
                lo = mid
            else:
                hi = mid
        radii.append((lo + hi) / 2.0)
    if radii:
        radii_sorted = sorted(radii)
        med = radii_sorted[len(radii_sorted) // 2]
        dev = abs(med - BALL_R) / BALL_R
        add(dev <= 0.02,
            "径向中位半径 %.1f px vs 标定 R=%.2f（偏差 %.2f%% ≤ 2%%）"
            % (med, BALL_R, dev * 100))
        spread = (radii_sorted[-1] - radii_sorted[0]) / med
        add(spread <= 0.06,
            "径向半径极差 %.1f~%.1f（占中位 %.1f%%，≤6%% 说明确实是个圆）"
            % (radii_sorted[0], radii_sorted[-1], spread * 100))
    else:
        add(False, "径向剖面未采集到有效半径，圆心可能标错了")

    # ③ 裁切方框必须完全落在画布内
    half = BALL_R / BALL_FILL
    left, top = BALL_CX - half, BALL_CY - half
    add(left >= 0 and top >= 0 and left + 2 * half <= W and top + 2 * half <= H,
        "裁切方框 %.1f,%.1f 边长 %.1f 落在画布 %dx%d 内"
        % (left, top, 2 * half, W, H))

    # ④ 方框四边中点应当落在球外的透明区（既证明球没被切，也证明确实留了余量）
    mid_a = []
    for x, y in ((int(left), int(BALL_CY)), (int(left + 2 * half) - 1, int(BALL_CY)),
                 (int(BALL_CX), int(top)), (int(BALL_CX), int(top + 2 * half) - 1)):
        if 0 <= x < W and 0 <= y < H:
            mid_a.append(px[x, y][3])
    add(len(mid_a) == 4 and max(mid_a) < 128,
        "裁切方框四边中点 alpha=%s（<128 说明四边都留出了余量、球没被切）" % mid_a)

    # ⑤ 球在方框内居中（由构造保证：方框中心 = 圆心），仅作展示
    add(True, "球体直径 %.1f px，占画布 %.1f%%（留白 %.1f%%）"
        % (2 * BALL_R, BALL_FILL * 100, (1 - BALL_FILL) * 100))
    add(True, "母图模式：%s" % mode_desc())
    add(True, "球边缘 左%.1f 右%.1f 上%.1f 下%.1f；到画布余量 左%.1f 右%.1f 上%.1f 下%.1f"
        % (BALL_CX - BALL_R, BALL_CX + BALL_R, BALL_CY - BALL_R, BALL_CY + BALL_R,
           BALL_CX - BALL_R, W - (BALL_CX + BALL_R),
           BALL_CY - BALL_R, H - (BALL_CY + BALL_R)))

    if verbose:
        for ln in lines:
            print(ln)
    return ok, lines


def _probe_square(verbose=True):
    """square 模式自检（v1.1.5 方案，保留）。"""
    src = _square_rgb()
    ok = True
    lines = []

    def add(flag, text):
        nonlocal ok
        if not flag:
            ok = False
        lines.append(("  " if flag else "! ") + text)

    cx, cy = CIRCLE_CX, CIRCLE_CY
    add(SQUARE_L < cx < SQUARE_R and SQUARE_T < cy < SQUARE_B,
        "圆心 (%.1f, %.1f) 在方块 %d,%d~%d,%d 内"
        % (cx, cy, SQUARE_L, SQUARE_T, SQUARE_R, SQUARE_B))

    bad = []
    for deg in range(0, 360, 2):
        a = math.radians(deg)
        x = int(round(cx + CIRCLE_R * math.cos(a)))
        y = int(round(cy + CIRCLE_R * math.sin(a)))
        if not (0 <= x < src.width and 0 <= y < src.height):
            bad.append((deg, "越界"))
            continue
        r, g, b = src.getpixel((x, y))
        if r > 170 and g > 170 and b > 170:
            bad.append((deg, "白(%d,%d,%d)" % (r, g, b)))
    add(not bad, "圆边界 180 点采样全部在蓝色方块内"
                 + ("" if not bad else " —— 异常 %s" % bad[:5]))

    margins = {"左": cx - CIRCLE_R - SQUARE_L, "右": SQUARE_R - (cx + CIRCLE_R),
               "上": cy - CIRCLE_R - SQUARE_T, "下": SQUARE_B - (cy + CIRCLE_R)}
    add(all(v > 0 for v in margins.values()),
        "圆到方块四边余量 " + " ".join("%s%.0f" % (k, v) for k, v in margins.items()))

    # 注意：不能用 PATTERN_BOX 的四个角去判 —— 图案是「圆形分布」，
    # 包围盒四角本来就是空白，拿四角算距离会得出 535px 的假报警。
    px0, py0, px1, py1 = PATTERN_BOX
    maxd, worst = 0.0, None
    for y in range(py0, py1 + 1, 2):
        for x in range(px0, px1 + 1, 2):
            rr, gg, bb = src.getpixel((x, y))
            if rr > 195 and gg > 195 and bb > 195:
                d = math.hypot(x - cx, y - cy)
                if d > maxd:
                    maxd, worst = d, (x, y)
    add(maxd <= CIRCLE_R,
        "最远图案像素 %.1fpx @%s ≤ 半径 %.0fpx（图案不被切）" % (maxd, worst, CIRCLE_R))

    p_margins = {"左": px0 - (cx - CIRCLE_R), "右": (cx + CIRCLE_R) - px1,
                 "上": py0 - (cy - CIRCLE_R), "下": (cy + CIRCLE_R) - py1}
    add(True, "图案在圆内余量 " + " ".join("%s%.0f" % (k, v) for k, v in p_margins.items()))
    add(True, "母图模式：%s" % mode_desc())

    if verbose:
        for ln in lines:
            print(ln)
    return ok, lines


def probe(verbose=True):
    return _probe_ball(verbose) if ICON_MODE == "ball" else _probe_square(verbose)


# ================================================================ 自查图
def _ui_font(size=13, bold=False):
    from PIL import ImageFont
    names = (["msyhbd.ttc", "msyh.ttc"] if bold else ["msyh.ttc", "msyhbd.ttc"]) + \
            ["simhei.ttf", "simsun.ttc", "arial.ttf"]
    for n in names:
        p = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts", n)
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return None


def _checker(size, cell=12):
    bg = Image.new("RGB", size, (245, 246, 248))
    d = ImageDraw.Draw(bg)
    for y in range(0, size[1], cell):
        for x in range(0, size[0], cell):
            if (x // cell + y // cell) % 2 == 0:
                d.rectangle((x, y, x + cell - 1, y + cell - 1), fill=(226, 229, 233))
    return bg


def check_sheet(variants, sizes, out_name, title=""):
    """把若干变体在多个尺寸下的效果拼成一张棋盘底对比图（棋盘格＝透明区域）。"""
    f_big = _ui_font(16, bold=True)
    f_small = _ui_font(14)
    cell = max(132, max(sizes) + 28)
    pad = 16
    W = pad * 2 + len(sizes) * cell
    H = pad * 2 + len(variants) * (cell + 10) + 30
    sheet = _checker((W, H))
    d = ImageDraw.Draw(sheet)
    if title:
        d.text((pad, pad), title, fill=(35, 40, 48), font=f_big)
    for ri, (name, im) in enumerate(variants):
        y0 = pad + 30 + ri * (cell + 10)
        d.text((pad, y0), name, fill=(30, 34, 40), font=f_big)
        for ci, s in enumerate(sizes):
            icon = im.resize((s, s), Image.LANCZOS)
            x = pad + ci * cell + (cell - s) // 2
            y = y0 + 22 + (cell - s) // 2
            sheet.paste(icon, (x, y), icon)
            d.text((pad + ci * cell + cell // 2 - 16, y0),
                   "%d" % s, fill=(100, 110, 124), font=f_small)
    out = os.path.join(ASSETS, out_name)
    scale = 1.0 if max(sizes) > 128 else 1.5
    sheet.resize((int(W * scale), int(H * scale)), Image.LANCZOS).save(out)
    print("%s -> %s" % (out_name, out))
    return out


def preview():
    """候选裁切方案对比（棋盘格＝透明区域），便于确认取哪个方案。"""
    if ICON_MODE == "ball":
        variants = [
            ("A 球顶满画布 fill=100%", ball_variant(fill=1.00)),
            ("B fill=94%（本轮采用）", ball_variant()),
            ("C fill=88%", ball_variant(fill=0.88)),
        ]
    else:
        bx = (SQUARE_L + SQUARE_R) / 2.0
        by = (SQUARE_T + SQUARE_B) / 2.0
        variants = [
            ("A 方块内切圆 r=528（图案会偏右上）", circle_variant(bx, by, 528)),
            ("B 图案居中 r=%d（v1.1.5 采用）" % CIRCLE_R, circle_variant()),
            ("C 折中 r=505", circle_variant(bx, (by + PATTERN_CY) / 2.0, 505)),
        ]
    return check_sheet(variants, [16, 24, 32, 48, 64, 128, 256],
                       "icon_preview.png", "图标裁切候选对比（棋盘格＝透明区域）")


# ================================================================ 主流程
def main():
    need = BALL_SRC if ICON_MODE == "ball" else SQUARE_SRC
    if not os.path.exists(need) and not (ICON_MODE == "square" and os.path.exists(SQUARE_PNG)):
        print("缺少母图:", need)
        return 1

    print("---- 几何自检（%s）----" % mode_desc())
    ok, _ = probe()
    if not ok:
        print("!! 自检未通过，请先按上面的提示重测圆心/半径（标定常量在文件顶部）。")
        return 1

    variant = current_variant()

    # ---- ① 桌面 / 安装包 / 便携版 exe 文件图标
    png = os.path.join(ASSETS, "icon.png")
    icon_at(256, variant).save(png)
    print("icon.png ->", png)
    _save_ico([icon_at(s, variant) for s in ICON_SIZES],
              os.path.join(ASSETS, "icon.ico"))

    # ---- ② 窗口图标（标题栏 / 任务栏 / 托盘）—— 与 ① 同源同内容
    app_png = os.path.join(ASSETS, "icon_app.png")
    icon_at(256, variant).save(app_png)
    print("icon_app.png ->", app_png)
    _save_ico([icon_at(s, variant) for s in ICON_SIZES],
              os.path.join(ASSETS, "icon_app.ico"))

    # ---- ③ 顶栏头像：设置齿轮（从来不跟着换）
    gear = gear_variant()
    if gear is not None:
        gear_png = os.path.join(ASSETS, "icon_gear.png")
        gear.resize((256, 256), Image.LANCZOS).save(gear_png)
        print("icon_gear.png -> %s（保持不变）" % gear_png)
    else:
        print("!! 缺少顶栏头像母图（assets/settings_source.png），跳过 icon_gear.png")

    # ---- 各尺寸自查图（棋盘格 = 透明区域）
    tag = "v1.1.6 换成电源开关球" if ICON_MODE == "ball" else "v1.1.5 改回圆形"
    check_sheet([("桌面 / 安装包 / 便携版 exe 文件图标", variant)],
                [16, 20, 24, 32, 48, 64, 128, 256],
                "icon_check.png", "① 桌面图标（%s）" % tag)
    check_sheet([("窗口左上角 / 任务栏 / 托盘 · 同一张图", variant)],
                [16, 20, 24, 32, 48, 64, 128, 256],
                "icon_app_check.png", "② 程序运行时图标（%s）" % tag)
    if gear is not None:
        check_sheet([("主界面顶栏右上角头像菜单 · 设置齿轮", gear)],
                    [16, 20, 24, 32, 48, 64],
                    "icon_gear_check.png", "③ 顶栏头像图标（保持不变）")

    preview()
    return 0


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "preview":
        raise SystemExit(0 if preview() else 1)
    if len(sys.argv) > 1 and sys.argv[1] == "probe":
        _ok, _ = probe()
        raise SystemExit(0 if _ok else 1)
    raise SystemExit(main())
