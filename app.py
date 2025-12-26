# app.py
# Streamlit：香氛互動式人格測驗（可執行版）
# 重點：不再覆蓋 helpers 的函式；結果圖中文字型可顯示

import streamlit as st
import json
import os
from datetime import datetime
import pandas as pd

from utils.helpers import plot_radar_safe, render_report_image


# ---------- 基本設定 ----------
st.set_page_config(page_title="香氛互動式人格測驗", layout="centered")
DATA_PATH = "data/chapter.json"
RESULTS_DIR = "data"


# ---------- 輔助 ----------
def load_chapters(path=DATA_PATH):
    if not os.path.exists(path):
        st.error(f"找不到題庫檔案：{path}。請確認 data/chapter.json 是否存在。")
        st.stop()
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def transform_score(raw, keyed):
    return 6 - raw if keyed == "minus" else raw


def calc_scores(answers, chapters):
    totals = {"Extraversion": 0, "Agreeableness": 0, "Conscientiousness": 0, "Neuroticism": 0, "Openness": 0}
    counts = {k: 0 for k in totals}

    for ch in chapters:
        for it in ch["items"]:
            qid = str(it["id"])
            if qid in answers:
                raw = int(answers[qid])
                sc = transform_score(raw, it.get("keyed", "plus"))
                trait = it["trait"]
                totals[trait] += sc
                counts[trait] += 1

    final = {}
    for k in totals:
        final[k] = round(totals[k] / counts[k], 2) if counts[k] > 0 else 0
    return final


def generate_detailed_feedback(scores):
    """
    你自己的結果文案：保留在 app.py 沒問題。
    """
    feedback = {}
    for trait, val in scores.items():
        entry = {"score": val, "who": "", "jobs": [], "actions": []}

        if trait == "Extraversion":
            if val >= 4:
                entry["who"] = "你像一瓶前調強烈的香氛，進場即照亮全場。你擅長主動互動、引領議題並在社交場合獲得能量。"
                entry["jobs"] = ["公關/活動企劃", "業務開發", "講師/培訓師", "品牌發言人"]
                entry["actions"] = ["承接一次 5-10 分鐘的公開演說練習表達力。", "每月至少參加一次業界交流擴展人脈。"]
            elif val >= 3:
                entry["who"] = "你在社交場合表現穩定，能在需要時展現熱情但也懂得回收能量。"
                entry["jobs"] = ["專案經理", "客戶顧問", "產品經理"]
                entry["actions"] = ["練習 30 秒電梯簡報以清晰表達重點。", "每週安排短時社交活動，維持人脈溫度。"]
            else:
                entry["who"] = "你內斂且深具觀察力，適合需要專注與深度思考的工作情境。"
                entry["jobs"] = ["研究/分析", "後端工程師", "編輯"]
                entry["actions"] = ["以 1 對 1 形式建立深度人脈。", "練習用 1 分鐘說出一個觀點。"]

        elif trait == "Agreeableness":
            if val >= 4:
                entry["who"] = "你如中調般柔和，具高同理與合作力，擅長團隊溝通與支持他人。"
                entry["jobs"] = ["人資/員工關係", "社工/諮商", "客戶成功"]
                entry["actions"] = ["學習同理式回應技巧。", "每月反思是否過度遷就，學習設立界限。"]
            elif val >= 3:
                entry["who"] = "你能兼顧合作與原則，適合協作型角色。"
                entry["jobs"] = ["產品協調", "服務設計"]
                entry["actions"] = ["用 '描述—感受—建議' 的方式提出改進意見。"]
            else:
                entry["who"] = "你偏向直言與堅持原則，適合需判斷力與決策的工作。"
                entry["jobs"] = ["風險管理", "品質管理", "策略分析"]
                entry["actions"] = ["練習以建設性語句提出批評（先肯定→再建議）。"]

        elif trait == "Conscientiousness":
            if val >= 4:
                entry["who"] = "你像基調穩定的香料，可靠、具責任感並注重細節。"
                entry["jobs"] = ["專案經理", "資料分析師", "供應鏈管理"]
                entry["actions"] = ["使用 sprint 拆解大型專案並逐步檢核。"]
            elif val >= 3:
                entry["who"] = "你有良好執行力與規劃性，能平衡彈性與紀律。"
                entry["jobs"] = ["操作管理", "產品協調"]
                entry["actions"] = ["為關鍵任務設定里程碑並檢核。"]
            else:
                entry["who"] = "你偏好彈性與創意，適合需要適應力與即興的職務。"
                entry["jobs"] = ["創意職位", "研究與概念開發"]
                entry["actions"] = ["採時間盒（time-boxing）提升專注度。"]

        elif trait == "Neuroticism":
            if val >= 4:
                entry["who"] = "你情緒較敏感、警覺性高，這讓你能提前察覺風險。"
                entry["jobs"] = ["風險管理（配合支援）", "品質把關"]
                entry["actions"] = ["建立情緒日誌以辨識壓力來源。", "每日 5-10 分鐘腹式呼吸/正念。"]
            elif val >= 3:
                entry["who"] = "情緒波動在可控範圍，建議持續使用壓力管理技巧。"
                entry["jobs"] = ["多數專業職務（有支援）"]
                entry["actions"] = ["模擬重要場合以降低焦慮感。"]
            else:
                entry["who"] = "你情緒穩定，是團隊的穩定力量。"
                entry["jobs"] = ["管理職", "高壓判斷角色"]
                entry["actions"] = ["維持情緒管理習慣並與團隊分享。"]

        elif trait == "Openness":
            if val >= 4:
                entry["who"] = "你充滿好奇與創意，適合跨領域與概念驅動的工作。"
                entry["jobs"] = ["創意總監", "產品設計", "研究創新"]
                entry["actions"] = ["建立靈感庫並定期回顧做組合創新。"]
            elif val >= 3:
                entry["who"] = "你具開放性與探索力，能在實務中帶入創意。"
                entry["jobs"] = ["產品企劃", "設計研究"]
                entry["actions"] = ["每周閱讀一篇跨領域文章並做摘要。"]
            else:
                entry["who"] = "你偏好結構化與深耕，適合需要專精的工作。"
                entry["jobs"] = ["技術研發", "流程改善"]
                entry["actions"] = ["用結構化方法（PDCA）導入改良。"]

        feedback[trait] = entry

    return feedback


# ---------- 主程式 ----------
def main():
    st.title("香氛互動式人格測驗")
    st.caption("本測驗僅參考使用，非專業心理評估。如有需求請尋求專業協助。")

    chapters = load_chapters()
    total_chapters = len(chapters)

    # session state init
    if "page_idx" not in st.session_state:
        st.session_state["page_idx"] = 0
    if "answers" not in st.session_state:
        st.session_state["answers"] = {}
    if "global_spices" not in st.session_state:
        st.session_state["global_spices"] = []
    if "started_at" not in st.session_state:
        st.session_state["started_at"] = datetime.utcnow().isoformat()

    # 完成後直接顯示結果（不再繼續跑章節 UI）
    # ---------- 美編報告卡範本（貼到完成頁） ----------
    if "completed_at" in st.session_state:
        scores = calc_scores(st.session_state["answers"], chapters)
        detailed = generate_detailed_feedback(scores)

    # 產生 PNG bytes（高解析）
        img_bytes = render_report_image(scores, detailed, username="你的名字")

    # 頂部：標題 + metadata
        st.markdown("<div style='display:flex; justify-content:space-between; align-items:center;'>"
                    f"<h2 style='margin:0;'>你的香氛人格報告</h2>"
                    f"<div style='color:#666;'>生成時間：{st.session_state.get('completed_at')}</div>"
                    "</div>",
                    unsafe_allow_html=True)
        st.markdown("<hr/>", unsafe_allow_html=True)

    # 主體欄：雷達圖 + 詳細卡片
        colL, colR = st.columns([1,1.2])
        with colL:
            st.image(img_bytes, width=560)  # 大圖，讓使用者可直接截圖
            st.caption("雷達圖顯示你的五大人格分布（1-5）")

        with colR:
        # 將每個 trait 顯示成卡片（小箱子）
            for trait, info in detailed.items():
                card_html = f"""
                <div style="background:#F4E9DF; padding:12px; border-radius:8px; margin-bottom:10px;">
                <h4 style="margin:0 0 6px 0;">{trait} — {info['score']} / 5</h4>
                <p style="margin:0 0 6px 0; color:#333;">{info['who']}</p>
                <p style="margin:0 0 6px 0;"><strong>建議：</strong>{' '.join(info['actions'][:2])}</p>
                <p style="margin:0; color:#666;"><em>適合：</em> {', '.join(info['jobs'][:3])}</p>
                </div>
                """
                st.markdown(card_html, unsafe_allow_html=True)

        st.markdown("<hr/>", unsafe_allow_html=True)
        st.markdown("<div style='display:flex; justify-content:space-between; align-items:center;'>"
                    "<div></div>"
                    "<div>"
                    "<a style='background:#8B5E3C;color:white;padding:10px 16px;border-radius:6px;text-decoration:none;' href='#' onclick=''>分享/儲存提示</a>"
                    "</div>"
                    "</div>",
                    unsafe_allow_html=True)

    # 下載按鈕（PNG）
        if img_bytes:
            st.download_button(
                label="下載高解析報告（PNG）",
                data=img_bytes,
                file_name="perfume_personality_report.png",
                mime="image/png"
            )
        st.stop()
# ---------- 結束報告卡 ----------


    # ---------- 正常章節流程 ----------
    # 首頁：全局香料選單（只在 page_idx == 0 顯示）
    if st.session_state["page_idx"] == 0:
        st.sidebar.header("測驗說明")
        st.sidebar.write("48 題，分 12 章情境式互動。請先選擇 1-3 種你偏好的香料（作為互動紀錄）。")

        st.subheader("全域香料選單（請在此選擇一次）")

        all_options = {}
        for ch in chapters:
            for s in ch.get("spice_options", []):
                all_options[s["code"]] = s

        codes = list(all_options.keys())
        chosen_global = st.multiselect(
            label="選擇 1 到 3 種香料",
            options=codes,
            format_func=lambda c: all_options[c]["label"] + " — " + all_options[c].get("desc", ""),
            default=st.session_state.get("global_spices", [])[:3],
        )

        if len(chosen_global) == 0:
            st.info("建議選 1 到 3 種香料作為偏好紀錄。")
        elif len(chosen_global) > 3:
            st.warning("請至多選 3 種，系統會僅記錄前 3 種。")

        st.session_state["global_spices"] = chosen_global[:3]

    page = st.session_state["page_idx"]
    chapter = chapters[page]

    st.header(f"章節 {page+1}/{total_chapters}：{chapter['title']}")
    st.write(chapter.get("context", ""))
    st.progress((page + 1) / total_chapters)

    # 顯示全局香料
    if st.session_state.get("global_spices"):
        st.markdown("**你選擇的香料（全局）**: " + ", ".join(st.session_state["global_spices"]))
    else:
        st.markdown("*尚未選擇香料（首頁可選）*")

    st.markdown("---")
    st.subheader("情境對話與問題")

    with st.form(key=f"form_{chapter['chapter_id']}"):
        for it in chapter["items"]:
            qid = str(it["id"])
            st.write(f"**{it['question_theme']}**")

            prev = st.session_state["answers"].get(qid)
            default_index = (prev - 1) if prev else 2

            ans = st.radio(
                label="你的回應：",
                options=[1, 2, 3, 4, 5],
                format_func=lambda x: {1: "非常不同意", 2: "不同意", 3: "中立", 4: "同意", 5: "非常同意"}[x],
                index=default_index,
                key=f"ans_{qid}",
            )

        submit = st.form_submit_button("送出本章")
        if submit:
            for it in chapter["items"]:
                qid = str(it["id"])
                st.session_state["answers"][qid] = st.session_state.get(f"ans_{qid}")
            st.success("本章答案已儲存。")

            if st.session_state["page_idx"] < total_chapters - 1:
                st.session_state["page_idx"] += 1
                st.rerun()
            else:
                st.session_state["completed_at"] = datetime.utcnow().isoformat()
                st.rerun()

    # 底部操作
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("上一章") and st.session_state["page_idx"] > 0:
            st.session_state["page_idx"] -= 1
            st.rerun()
    with col2:
        if st.button("跳到最後章節"):
            st.session_state["page_idx"] = total_chapters - 1
            st.rerun()
    with col3:
        if st.button("儲存並離開"):
            os.makedirs(RESULTS_DIR, exist_ok=True)
            save_path = os.path.join(RESULTS_DIR, "last_saved_session.json")
            to_save = {
                "started_at": st.session_state.get("started_at"),
                "saved_at": datetime.utcnow().isoformat(),
                "page_idx": st.session_state.get("page_idx"),
                "answers": st.session_state.get("answers"),
                "global_spices": st.session_state.get("global_spices"),
            }
            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(to_save, f, ensure_ascii=False, indent=2)
            st.success(f"已儲存進度到 {save_path}")


if __name__ == "__main__":
    main()
