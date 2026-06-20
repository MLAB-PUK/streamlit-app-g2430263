import streamlit as st
import pandas as pd
import streamlit.components.v1 as components

# 1. 画面の設定
st.set_page_config(page_title="F研PA表印刷ツール", page_icon="🎛️", layout="wide")
st.title("🖨️ F研PA表印刷ツール")
st.caption("CSVに日付がなくても大丈夫！画面上でバンドを日にちごとに仕分けて、別々に印刷できます。")

# 2. CSVファイルのアップロード
st.subheader("📋 1. 全エントリーCSVをアップロード")
uploaded_file = st.file_uploader("Googleフォーム等からダウンロードしたCSVファイルを選択してください", type=["csv"])

if uploaded_file is not None:
    # データの初期化処理
    if "df_master" not in st.session_state or st.sidebar.button("🔄 データを最初からやり直す"):
        df = pd.read_csv(uploaded_file, dtype=str)
        df.columns = df.columns.str.strip().str.replace('\n', '').str.replace('\r', '')
        for col in df.columns:
            df[col] = df[col].astype(str).str.strip()
        
        # 自分で調整するための「日程」列と「出演順」列を初期状態で追加
        df.insert(0, "出演順", range(1, len(df) + 1))
        df.insert(0, "日程", "1日目")  # 初期値はすべて1日目
        st.session_state.df_master = df
        st.session_state.available_dates = ["1日目", "2日目"]  # 初期の日程選択肢

    # 日程の追加・削除コントロール
    st.subheader("📅 日程枠の管理")
    col_add, col_del, _ = st.columns([1, 1, 4])
    with col_add:
        if st.button("➕ 日程を増やす"):
            next_day = f"{len(st.session_state.available_dates) + 1}日目"
            st.session_state.available_dates.append(next_day)
            st.rerun()
    with col_del:
        if st.button("🗑️ 最後の日にちを消す") and len(st.session_state.available_dates) > 1:
            removed_day = st.session_state.available_dates.pop()
            # 消された日にいたバンドは1日目に強制送還
            st.session_state.df_master.loc[st.session_state.df_master["日程"] == removed_day, "日程"] = "1日目"
            st.rerun()

    # 3. 画面上での日程仕分けと出演順調整
    st.subheader("🔄 2. バンドの日程振り分け ＆ 出演順の調整")
    st.info("💡 使い方:\n1. 「日程」の項目をクリックして、バンドを何日目にするか選択してください。\n2. 「出演順」の数字を書き換えてください。\n3. 最後に列名の「日程」や「出演順」をクリックすると、綺麗に並び替わって確認しやすくなります。")

    # データエディタで「日程」をプルダウン選択できるように設定
    edited_df = st.data_editor(
        st.session_state.df_master,
        use_container_width=True,
        hide_index=True,
        column_config={
            "日程": st.column_config.SelectboxColumn(
                "日程",
                options=st.session_state.available_dates,
                required=True,
                help="ライブの何日目に出演するか選んでください"
            ),
            "出演順": st.column_config.NumberColumn(
                "出演順",
                min_value=1,
                step=1,
                required=True,
                help="その日の中での出演順番を入力してください"
            )
        }
    )
    # 編集結果をマスターに保存
    st.session_state.df_master = edited_df

    # 4. 印刷する日程の選択
    st.subheader("🖨️ 3. PA表の生成と印刷")
    print_target_date = st.selectbox("👉 いまから印刷したい日程を選択してください", st.session_state.available_dates)

    if st.button(f"🔥 【{print_target_date}】の一覧表を生成する", type="primary"):
        
        # 選択された日のバンドだけを抽出し、出演順でソート
        df_filtered = edited_df[edited_df["日程"] == print_target_date].copy()
        df_filtered["出演順"] = pd.to_numeric(df_filtered["出演順"])
        df_sorted = df_filtered.sort_values(by="出演順")
        
        if df_sorted.empty:
            st.warning(f"⚠️ 【{print_target_date}】に割り当てられているバンドが1つもありません。上の表で日程を選んでください。")
        else:
            html_rows = ""
            cols = df_sorted.columns
            
            # 列名の自動検出
            band_col = [c for c in cols if 'バンド' in c or '名' in c]
            di_col = [c for c in cols if 'DI' in c or 'di' in c]
            mic_col = [c for c in cols if 'マイク' in c or 'mic' in c]
            note_col = [c for c in cols if '備考' in c or 'コメント' in c or 'その他' in c]
            
            b_name = band_col[0] if band_col else (cols[3] if len(cols) > 3 else cols[2])
            d_name = di_col[0] if di_col else None
            m_name = mic_col[0] if mic_col else None
            n_name = note_col[0] if note_col else None

            for _, row in df_sorted.iterrows():
                b_val = str(row.get(b_name, '')).replace('\n', ' ').replace('\r', ' ').strip()
                d_val = str(row.get(d_name, '')).replace('\n', ' ').replace('\r', ' ').strip() if d_name else ""
                m_val = str(row.get(m_name, '')).replace('\n', ' ').replace('\r', ' ').strip() if m_name else ""
                n_val = str(row.get(n_name, '')).replace('\n', ' ').replace('\r', ' ').strip() if n_name else ""
                
                if not b_val or b_val == "nan": b_val = "（不明）"
                if not d_val or d_val == "nan": d_val = "-"
                if not m_val or m_val == "nan": m_val = "-"
                if not n_val or n_val == "nan": n_val = "-"

                # 翻訳完全ブロック用の属性付き行
                html_rows += f"""
                <tr translate="no" class="notranslate">
                    <td class="text-center"><b>{row['出演順']}</b></td>
                    <td>
                        <div class="time-container">
                            <div class="time-line"></div> 〜 <div class="time-line"></div>
                        </div>
                    </td>
                    <td class="band-name-cell">{b_val}</td>
                    <td class="pre-wrap">{d_val}</td>
                    <td class="pre-wrap">{m_val}</td>
                    <td class="pre-wrap">{n_val}</td>
                </tr>
                """
                
            st.session_state.pa_html_result = html_rows
            st.session_state.current_printed_date = print_target_date
            st.success(f"✨ 【{print_target_date}】用の印刷用一覧表が下に完成しました！")

    # 5. 結果の表示と印刷ボタン
    if "pa_html_result" in st.session_state and "current_printed_date" in st.session_state:
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="ja" translate="no" class="notranslate">
        <head>
            <meta charset="UTF-8">
            <meta name="google" content="notranslate">
            <title>PA表</title>
            <style>
                body {{ font-family: sans-serif; padding: 10px; color: #111; background-color: #fff; }}
                .container {{ max-width: 100%; box-sizing: border-box; }}
                
                h1 {{ font-size: 22px; text-align: center; margin-bottom: 15px; color: #000; border-bottom: 3px solid #000; padding-bottom: 5px; }}
                
                table {{ border-collapse: collapse; width: 100%; table-layout: fixed; }}
                th, td {{ border: 2px solid #000; padding: 10px 8px; font-size: 14px; word-wrap: break-word; overflow-wrap: break-word; vertical-align: middle; }}
                th {{ background-color: #f0f0f0; font-weight: bold; text-align: center; }}
                
                .text-center {{ text-align: center; }}
                .pre-wrap {{ white-space: pre-wrap; }}
                .band-name-cell {{ font-weight: bold; font-size: 15px; }}
                
                .time-container {{ display: flex; align-items: center; justify-content: center; }}
                .time-line {{ width: 42px; border-bottom: 1px dashed #444; height: 18px; display: inline-block; }}
                
                .btn-container {{ margin-bottom: 20px; }}
                .print-btn {{ padding: 12px 24px; background-color: #ff4b4b; color: white; border: none; border-radius: 5px; font-size: 16px; font-weight: bold; cursor: pointer; box-shadow: 0 2px 5px rgba(0,0,0,0.2); }}
                .print-btn:hover {{ background-color: #e04343; }}
                
                @media print {{ 
                    .btn-container {{ display: none; }} 
                    body {{ padding: 0; }} 
                    .container {{ width: 100%; }} 
                }}
            </style>
        </head>
        <body>
            <div class="btn-container">
                <button class="print-btn" onclick="window.print()">🖨️ この一覧表({st.session_state.current_printed_date})を紙に印刷 / PDF保存する</button>
            </div>
            <div class="container">
                <h1>_________  __日目　PA表 ({st.session_state.current_printed_date})</h1>
                <table>
                    <tr>
                        <th style="width: 7%;">出演順</th>
                        <th style="width: 15%;">時間枠 (手書き)</th>
                        <th style="width: 23%;">バンド名</th>
                        <th style="width: 15%;">DI</th>
                        <th style="width: 20%;">マイク</th>
                        <th style="width: 20%;">備考</th>
                    </tr>
                    {st.session_state.pa_html_result}
                </table>
            </div>
        </body>
        </html>
        """
        
        st.markdown(f"### 📊 生成されたPA一覧表：【{st.session_state.current_printed_date}】分")
        components.html(html_content, height=900, scrolling=True)
        