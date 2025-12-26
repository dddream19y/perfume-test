# utils/helpers.py
# 只使用 fonts/SourceHanSansTC-Normal.otf 來避免中文變成 □□□
# 提供：
# 1) plot_radar_safe(scores) -> matplotlib Figure
# 2) render_report_image(scores, detailed_feedback, username="你") -> PNG bytes

import os
from io import BytesIO
from datetime import datetime

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm

from PIL import Image, ImageDraw, ImageFont


# -----------------------------
# 固定字型路徑（只認這支）
# -----------------------------
def _project_root() -> str:
    # utils/helpers.py -> utils -> project root
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def get_font_path() -> str:
    """
    回傳專案內固定字型路徑：
      <project_root>/fonts/SourceHanSansTC-Normal.otf
    找不到就直接丟錯，避免默默 fallback 造成 □□□。
    """
    root = _project_root()
    font_path = os.path.join(root, "fonts", "SourceHanSansTC-Normal.otf")
    if not os.path.exists(font_path):
        raise FileNotFoundError(
            "找不到字型檔：fonts/SourceHanSansTC-Normal.otf\n"
            f"目前解析到的路徑是：{font_path}\n"
            "請確認：\n"
            "1) 專案根目錄有 fonts/ 資料夾\n"
            "2) 字型檔名完全一致（含大小寫）\n"
            "3) 部署環境也有帶上這個檔案"
        )
    return font_path


def apply_mpl_font(font_path: str) -> None:
    """
    將固定字型套用到 matplotlib，讓中文軸標籤不會變豆腐字。
    """
    fm.fontManager.addfont(font_path)
    prop = fm.FontProperties(fname=font_path)
    plt.rcParams["font.family"] = prop.get_name()
    plt.rcParams["axes.unicode_minus"] = False


# -----------------------------
# 雷達圖
# -----------------------------
def plot_radar_safe(scores: dict) -> plt.Figure:
    """
    scores: dict trait->value (0-5 or 1-5)
    回傳 matplotlib Figure
    """
    font_path = get_font_path()
    apply_mpl_font(font_path)

    cats = list(scores.keys())
    vals = [float(scores[k]) for k in cats]
    vals = [max(0.0, min(5.0, v)) for v in vals]

    # radar 需要閉合
    vals += vals[:1]
    n = len(cats)

    angles = [i / float(n) * 2 * np.pi for i in range(n)]
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)

    ax.set_ylim(0, 5)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(cats)

    ax.plot(angles, vals, linewidth=2)
    ax.fill(angles, vals, alpha=0.25)

    ax.set_yticks([1, 2, 3, 4, 5])
    ax.set_yticklabels(["1", "2", "3", "4", "5"])

    return fig


# -----------------------------
# 報告圖輸出（Pillow）
# -----------------------------
def render_report_image(scores: dict, detailed_feedback: dict, username: str = "你") -> bytes:
    """
    回傳 PNG bytes：包含雷達圖 + 右側文字摘要
    """
    # 1) 雷達圖先渲染成圖片
    fig = plot_radar_safe(scores)
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=160)
    plt.close(fig)
    buf.seek(0)

    radar_img = Image.open(buf).convert("RGBA")
    r_w, r_h = radar_img.size

    # 2) 建畫布
    canvas_w = r_w + 640
    canvas_h = max(r_h + 220, 920)
    canvas = Image.new("RGBA", (canvas_w, canvas_h), "WHITE")
    canvas.paste(radar_img, (40, 80), radar_img)

    draw = ImageDraw.Draw(canvas)

    # 3) Pillow 字型（固定同一支）
    font_path = get_font_path()
    font_title = ImageFont.truetype(font_path, 30)
    font_header = ImageFont.truetype(font_path, 18)
    font_body = ImageFont.truetype(font_path, 14)

    x_text = r_w + 70
    y_text = 80

    draw.text((x_text, y_text), f"{username} 的香氛人格報告", fill="black", font=font_title)
    y_text += 52

    # 4) 內容
    for trait, info in detailed_feedback.items():
        draw.text(
            (x_text, y_text),
            f"{trait}: {info.get('score', '-') } / 5",
            fill="#222222",
            font=font_header,
        )
        y_text += 24

        who = (info.get("who", "") or "").replace("\n", " ").strip()
        if len(who) > 120:
            who = who[:117] + "..."
        draw.text((x_text, y_text), who, fill="#444444", font=font_body)
        y_text += 38

        jobs = info.get("jobs", []) or []
        if jobs:
            jobs_str = "適合：" + ", ".join(jobs)
            if len(jobs_str) > 120:
                jobs_str = jobs_str[:117] + "..."
            draw.text((x_text, y_text), jobs_str, fill="#333333", font=font_body)
            y_text += 34

        if y_text > canvas_h - 170:
            draw.text((x_text, y_text), "（內容過長，已截斷）", fill="#666666", font=font_body)
            y_text += 20
            break

    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    draw.text((40, canvas_h - 60), f"生成時間：{ts}", fill="#666666", font=font_body)

    out = BytesIO()
    canvas.convert("RGB").save(out, format="PNG")
    out.seek(0)
    return out.getvalue()
