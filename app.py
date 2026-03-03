import streamlit as st
import pandas as pd
import glob
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ページ設定
st.set_page_config(page_title="経営ダッシュボード", layout="wide")
st.title("経営ダッシュボード")

# データの読み込み
@st.cache_data
def load_data():
    try:
        # irikomiフォルダ内のcityから始まるすべてのCSVファイルを読み込む
        csv_files = glob.glob("irikomi/city*.csv")
        
        if not csv_files:
            st.warning("irikomiフォルダにCSVファイルが見つかりません。")
            return pd.DataFrame()

        df_list = []
        for file in csv_files:
            # 形式によってはshift_jisでエラーになる場合があるため、必要に応じて変更
            df_temp = pd.read_csv(file, encoding="shift_jis", low_memory=False)
            df_list.append(df_temp)
        
        # すべてのデータを結合
        df = pd.concat(df_list, ignore_index=True)
        
        # 必要なカラムが存在するか確認し、抽出
        required_columns = ['年', '月', '地域名称', '人数']
        if all(col in df.columns for col in required_columns):
            df = df[required_columns]
            
            # 人数カラムを数値型に変換（エラーとなる文字列はNaNに変換し、その後0埋め）
            df['人数'] = pd.to_numeric(df['人数'], errors='coerce').fillna(0)
        else:
            missing = [col for col in required_columns if col not in df.columns]
            st.error(f"必要なカラムが見つかりません: {missing}")
            return pd.DataFrame()
            
        return df
    except Exception as e:
        st.error(f"データの読み込み中にエラーが発生しました: {e}")
        return pd.DataFrame()

@st.cache_data
def load_accommodation_data():
    try:
        df = pd.read_excel('Overnights/2025.xlsx')
        df['月'] = df['月'].astype(str).str.replace('月', '').astype(int)
        
        def clean_num(x):
            if isinstance(x, str):
                return float(x.replace(',', '').replace('施設', '').replace('人泊', '').replace('人', '').replace('室', '').strip())
            return x
            
        cols_to_clean = ['回収施設数合計', '延べ宿泊者数', '実宿泊者数', '外国人延べ宿泊者数', '外国人実宿泊者数', '利用客室数']
        for col in cols_to_clean:
            if col in df.columns:
                df[col] = df[col].apply(clean_num)
                
        if '客室稼働率' in df.columns:
            df['客室稼働率(%)'] = (df['客室稼働率'] * 100).round(1)
        if '定員稼働率' in df.columns:
            df['定員稼働率(%)'] = (df['定員稼働率'] * 100).round(1)
            
        return df
    except Exception as e:
        st.error(f"宿泊データの読み込みエラー: {e}")
        return pd.DataFrame()

@st.cache_data
def load_total_accommodation_data():
    try:
        df = pd.read_csv('Overnights/2025total.csv', encoding='utf-8')
        df['都道県'] = df['市区町村'].str.extract(r'^([^都道府県]+[都道府県])')
        df['市町村名'] = df.apply(lambda row: str(row['市区町村']).replace(str(row['都道県']), '') if pd.notna(row['都道県']) else row['市区町村'], axis=1)
        df['月_num'] = df['月'].str.replace('月', '').astype(int)
        return df
    except Exception as e:
        st.error(f"宿泊者数(2025total)データの読み込みエラー: {e}")
        return pd.DataFrame()

@st.cache_data
def load_total_population_data():
    try:
        # まずは utf-8 を試す
        df = pd.read_csv('irikomi/city2025.csv', encoding='utf-8', low_memory=False)
    except Exception:
        try:
            # 失敗した場合は shift_jis を試す
            df = pd.read_csv('irikomi/city2025.csv', encoding='shift_jis', low_memory=False)
        except Exception as e:
            return pd.DataFrame() # 存在しない場合は空を返す
            
    if not df.empty:
        # カラム名の揺れに対応して前処理
        if '市区町村' in df.columns:
            df['都道県'] = df['市区町村'].str.extract(r'^([^都道府県]+[都道府県])')
            df['市町村名'] = df.apply(lambda row: str(row['市区町村']).replace(str(row['都道県']), '') if pd.notna(row['都道県']) else row['市区町村'], axis=1)
        elif '地域名称' in df.columns:
            df['市町村名'] = df['地域名称']
            if '都道府県名' in df.columns:
                df['都道県'] = df['都道府県名']
            
        if '月' in df.columns:
            if df['月'].dtype == object:
                df['月_num'] = df['月'].str.replace('月', '').astype(int)
            else:
                df['月_num'] = df['月']
        
        # 人数のカラムが存在するか確認し、なければ数値変換
        if '人数' in df.columns:
            df['人数'] = pd.to_numeric(df['人数'], errors='coerce').fillna(0)
            
    return df


# アプリのメイン処理
def main():
    st.subheader("データの読み込みステータス")
    with st.spinner('データを読み込んでいます...'):
        df_all = load_data()

    if not df_all.empty:
        # 高山市のみを対象に絞り込み
        target_city = "高山市"
        df_takayama = df_all[df_all['地域名称'] == target_city].copy()
        
        st.success("データの読み込みが完了しました。")
        
        col_h1, col_h2 = st.columns([7, 3])
        with col_h1:
            st.header("【I．現状】", anchor="genjyo")
        with col_h2:
            st.markdown("<div style='text-align: right; margin-top: 25px;'>"
                        "<a href='#doukou' style='text-decoration: none; padding: 5px 15px; margin-right: 5px; background-color: #f0f2f6; border-radius: 5px; color: #31333F; font-weight: bold;'>⬇ Ⅱ．今後の動向</a>"
                        "<a href='#other_regions' style='text-decoration: none; padding: 5px 15px; background-color: #f0f2f6; border-radius: 5px; color: #31333F; font-weight: bold;'>⬇ Ⅲ．他地域の動向</a>"
                        "</div>", unsafe_allow_html=True)
            
        st.markdown(f"### 月別人数推移 ({target_city}) <span style='font-size: 14px; font-weight: normal; color: gray;'>出典 デジタル観光統計(日本観光振興協会)</span>", unsafe_allow_html=True)
        if not df_takayama.empty:
            # 1. 年月で集計 (同じ月・年に複数のエントリがある場合を考慮して合計)
            df_g = df_takayama.groupby(['年', '月'], as_index=False)['人数'].sum()
            
            # グラフ表示用の年を選択するUI
            st.markdown("**表示する年を選択してください:**")
            available_years = sorted(df_g['年'].unique())
            # 2021〜2025に限定する場合
            available_years = [y for y in available_years if 2021 <= y <= 2025]
            
            # デフォルトで最新2年（例：2024, 2025）を選択状態にする
            default_years = []
            if len(available_years) >= 2:
                default_years = [int(available_years[len(available_years)-2]), int(available_years[len(available_years)-1])]
            else:
                default_years = [int(y) for y in available_years]
            
            # 横並びのチェックボックスを作成
            cols = st.columns(len(available_years))
            selected_years = []
            for i, year in enumerate(available_years):
                with cols[i]:
                    y_int = int(year)
                    is_default = False
                    for dy in default_years:
                        if y_int == dy:
                            is_default = True
                            
                    if st.checkbox(str(year), value=is_default):
                        selected_years.append(y_int)
            
            if not selected_years:
                st.warning("少なくとも1つの年を選択してください。")
                return

            # 表示する内容を選択するUI
            st.markdown("**表示するデータを選択してください:**")
            col_data1, col_data2, _ = st.columns([1, 1, 3])
            with col_data1:
                show_population = st.checkbox("人数", value=True)
            with col_data2:
                show_yoy = st.checkbox("対前年比", value=True)
                
            if not show_population and not show_yoy:
                st.warning("「人数」または「対前年比」のいずれかを選択してください。")
                return

            # Plotlyで折れ線グラフを描画
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            
            # 対前年比の最大・最小を保存するリスト（Y軸のスケール調整用）
            all_yoy_values = []
            
            # 全国の集計データもあらかじめ計算しておく
            df_all_g = df_all.groupby(['年', '月'], as_index=False)['人数'].sum()
            
            # 各年ごとのデータを描画
            colors = {2021: '#1f77b4', 2022: '#ff7f0e', 2023: '#2ca02c', 2024: '#d62728', 2025: '#9467bd'}
            
            for year in sorted(selected_years):
                df_year = df_g[df_g['年'] == year].copy()
                df_prev = df_g[df_g['年'] == year - 1].copy()
                
                # 前年データを結合して対前年比を計算
                df_prev = df_prev.rename(columns={'人数': '前年人数'})
                df_prev['年'] = year
                df_merged_year = pd.merge(df_year, df_prev[['年', '月', '前年人数']], on=['年', '月'], how='left')
                df_merged_year['対前年比'] = (df_merged_year['人数'] / df_merged_year['前年人数'] * 100).round(1)
                
                def create_label(row):
                    if pd.notna(row['対前年比']):
                        return f"{row['対前年比']}%"
                    return ""
                
                df_merged_year['text'] = df_merged_year.apply(create_label, axis=1)
                
                # 人数の折れ線グラフ
                if show_population:
                    fig.add_trace(
                        go.Scatter(
                            x=df_merged_year['月'],
                            y=df_merged_year['人数'],
                            mode='lines+markers',
                            name=f'{year}年 人数 ({target_city})',
                            marker={"size": 10, "color": colors.get(year, '#333333')},
                            line={"width": 3}
                        ),
                        secondary_y=False
                    )
                
                # ------ 全国のデータ計算 ------
                df_all_year = df_all_g[df_all_g['年'] == year].copy()
                df_all_prev = df_all_g[df_all_g['年'] == year - 1].copy()
                df_all_prev = df_all_prev.rename(columns={'人数': '全国前年人数'})
                df_all_prev['年'] = year
                df_all_merged_year = pd.merge(df_all_year, df_all_prev[['年', '月', '全国前年人数']], on=['年', '月'], how='left')
                df_all_merged_year['全国対前年比'] = (df_all_merged_year['人数'] / df_all_merged_year['全国前年人数'] * 100).round(1)
                
                def create_all_label(row):
                    if pd.notna(row['全国対前年比']):
                        return f"{row['全国対前年比']}%"
                    return ""
                
                df_all_merged_year['全国text'] = df_all_merged_year.apply(create_all_label, axis=1)
                
                # 対前年比の折れ線グラフ（textとして数値を表示）
                if show_yoy:
                    fig.add_trace(
                        go.Scatter(
                            x=df_merged_year['月'],
                            y=df_merged_year['対前年比'],
                            mode='lines+markers+text',
                            name=f'{year}年 対前年比 ({target_city})',
                            text=df_merged_year['text'],
                            textposition='top center',
                            marker={"size": 8, "color": colors.get(year, '#333333')},
                            line={"width": 2, "dash": 'dash'}
                        ),
                        secondary_y=True
                    )
                    
                    fig.add_trace(
                        go.Scatter(
                            x=df_all_merged_year['月'],
                            y=df_all_merged_year['全国対前年比'],
                            mode='lines+markers+text',
                            name=f'{year}年 対前年比 (全国)',
                            text=df_all_merged_year['全国text'],
                            textposition='bottom center',
                            marker={"size": 6, "color": colors.get(year, '#333333')},
                            line={"width": 1.5, "dash": 'dot'}
                        ),
                        secondary_y=True
                    )
                    
                    all_yoy_values.extend(df_all_merged_year['全国対前年比'].dropna().tolist())
                
                all_yoy_values.extend(df_merged_year['対前年比'].dropna().tolist())
            
            # ---- 以前の全国比較・四半期分析用のデータ準備 (2025年ベース) ----
            # 分析セクションは引き続き2025年ベースで動作するようにデータを保持
            df_2025 = df_g[df_g['年'] == 2025].copy()
            df_2024 = df_g[df_g['年'] == 2024].copy().rename(columns={'人数': '前年人数'})
            df_2024['年'] = 2025
            df_merged = pd.merge(df_2025, df_2024[['年', '月', '前年人数']], on=['年', '月'], how='left')
            df_merged['対前年比'] = (df_merged['人数'] / df_merged['前年人数'] * 100).round(1)
            
            df_all_2025 = df_all_g[df_all_g['年'] == 2025].copy()
            df_all_2024 = df_all_g[df_all_g['年'] == 2024].copy().rename(columns={'人数': '全国前年人数'})
            df_all_2024['年'] = 2025
            df_all_merged = pd.merge(df_all_2025, df_all_2024[['年', '月', '全国前年人数']], on=['年', '月'], how='left')
            df_all_merged['全国対前年比'] = (df_all_merged['人数'] / df_all_merged['全国前年人数'] * 100).round(1)
            
            df_merged = pd.merge(df_merged, df_all_merged[['月', '全国対前年比']], on='月', how='left')
            
            # --- グラフのレイアウト調整 ---
            y2_range = [0, 200]
            if all_yoy_values:
                yoy_min = min(all_yoy_values)
                yoy_max = max(all_yoy_values)
                margin = (yoy_max - yoy_min) * 0.1 if yoy_max != yoy_min else 5
                y2_range = [yoy_min - margin, yoy_max + margin]
            
            title_text = f"{target_city} 月別 "
            if show_population and show_yoy:
                title_text += "人数推移 と 対前年比比較"
            elif show_population:
                title_text += "人数推移"
            elif show_yoy:
                title_text += "対前年比比較"
                
            title_text += " <span style='font-size: 12px; color: gray; font-weight: normal;'>出典 デジタル観光統計(日本観光振興協会)</span>"
            
            fig.update_layout(
                title=title_text,
                xaxis={"title": "月", "tickmode": 'linear', "dtick": 1, "tick0": 1, "range": [0.5, 12.5]},
                margin={"t": 50, "b": 50, "l": 50, "r": 50},
                height=600,
                legend={"orientation": "h", "yanchor": "bottom", "y": 1.05, "xanchor": "right", "x": 1}
            )
            
            if show_population:
                fig.update_yaxes(title_text="人数", secondary_y=False)
            if show_yoy:
                fig.update_yaxes(title_text="対前年比 (%)", range=y2_range, secondary_y=True)
            
            st.plotly_chart(fig, use_container_width=True)
            
            # --- 検索トレンドデータの追加 (グラフ等の分析用としてデータのみ保持) ---
            # 高山_観光 の検索トレンド（2025年単年分）
            trend_data_2025 = [35, 41, 44, 49, 56, 46, 48, 61, 71, 56, 52, 33]
            df_merged['検索トレンド（相対値）'] = trend_data_2025
            
            # takayama の検索トレンド（2025年単年分）
            takayama_data_2025 = [50, 42, 56, 86, 74, 42, 48, 52, 72, 99, 88, 58]
            df_merged['takayama検索数'] = takayama_data_2025
            
            # --- 宿泊データのグラフ表示 ---
            df_acc = load_accommodation_data()
            if not df_acc.empty:
                st.markdown("### 🏨 宿泊動向 (2025年) <span style='font-size: 14px; font-weight: normal; color: gray;'>出典 宿泊観光統計(観光庁)</span>", unsafe_allow_html=True)
                # 表示項目から「月」「元の稼働率」などを除く
                acc_columns = [c for c in df_acc.columns if c not in ['月', '客室稼働率', '定員稼働率']]
                selected_acc_cols = st.multiselect("表示する項目を選択してください:", acc_columns, default=['延べ宿泊者数', '外国人延べ宿泊者数'])
                
                if selected_acc_cols:
                    fig_acc = make_subplots(specs=[[{"secondary_y": True}]])
                    
                    has_secondary = False
                    for col in selected_acc_cols:
                        is_rate = '(%)' in col
                        if is_rate: has_secondary = True
                        fig_acc.add_trace(go.Scatter(
                            x=df_acc['月'], y=df_acc[col], mode='lines+markers', name=col,
                        ), secondary_y=is_rate)
                        
                    fig_acc.update_layout(
                        xaxis={"title": "月", "tickmode": 'linear', "dtick": 1, "tick0": 1, "range": [0.5, 12.5]},
                        margin={"t": 30, "b": 30, "l": 50, "r": 50},
                        height=400,
                        legend={"orientation": "h", "yanchor": "bottom", "y": 1.05, "xanchor": "right", "x": 1}
                    )
                    
                    fig_acc.update_yaxes(title_text="人数 / 室数", secondary_y=False)
                    if has_secondary:
                        fig_acc.update_yaxes(title_text="稼働率 (%)", range=[0, 100], secondary_y=True)
                        
                    st.plotly_chart(fig_acc, use_container_width=True)

            st.markdown("### 🔍 検索トレンド分析 (2022年〜2025年) <span style='font-size: 14px; font-weight: normal; color: gray;'>出典 Google Trend</span>", unsafe_allow_html=True)
            
            # --- takayama検索トレンドデータ ---
            takayama_trend_2022_2025 = [
                10, 10, 9, 10, 10, 9, 8, 9, 11, 10, 15, 30,      # 2022
                24, 24, 28, 58, 42, 31, 38, 42, 46, 72, 66, 50,  # 2023
                35, 38, 60, 78, 66, 42, 46, 55, 58, 100, 86, 56, # 2024
                50, 42, 56, 86, 74, 42, 48, 52, 72, 99, 88, 58   # 2025
            ]
            
            # --- 高山_観光検索トレンドデータ ---
            takayama_kanko_trend_2022_2025 = [
                34, 36, 50, 81, 78, 66, 70, 100, 76, 85, 58, 40, # 2022
                40, 49, 58, 65, 83, 77, 62, 76, 96, 76, 74, 53,  # 2023
                40, 43, 49, 67, 63, 47, 65, 78, 69, 61, 49, 34,  # 2024
                35, 41, 44, 49, 56, 46, 48, 61, 71, 56, 52, 33   # 2025
            ]
            
            # 折れ線グラフ（検索トレンド）
            fig_trend = go.Figure()
            
            dates_48 = pd.date_range(start='2022-01-01', periods=48, freq='MS')
            
            # takayama (2022-2025)
            fig_trend.add_trace(go.Scatter(
                x=dates_48, y=takayama_trend_2022_2025, mode='lines+markers+text',
                name='takayama 検索数', text=[str(v) for v in takayama_trend_2022_2025], textposition='top center',
                line={"color": '#1f77b4', "width": 3}, marker={"size": 6}
            ))

            # 高山_観光 (2022-2025)
            fig_trend.add_trace(go.Scatter(
                x=dates_48, y=takayama_kanko_trend_2022_2025, mode='lines+markers+text',
                name='高山_観光 検索数', text=[str(v) for v in takayama_kanko_trend_2022_2025], textposition='top center',
                line={"color": '#ff7f0e', "width": 3}, marker={"size": 8}
            ))
            
            fig_trend.update_layout(
                xaxis={"title": "年月", "tickformat": "%Y-%m"},
                yaxis={"title": "検索トレンド（相対値）", "range": [0, 100]},
                margin={"t": 30, "b": 30, "l": 50, "r": 50},
                height=350,
                legend={"orientation": "h", "yanchor": "bottom", "y": 1.05, "xanchor": "right", "x": 1}
            )
            st.plotly_chart(fig_trend, use_container_width=True)
            
            # 散布図（左右に並べる）
            col_s1, col_s2 = st.columns(2)
            
            with col_s1:
                # 散布図1（高山_観光 検索トレンド vs 人数）
                fig_scatter1 = go.Figure()
                fig_scatter1.add_trace(go.Scatter(
                    x=df_merged['検索トレンド（相対値）'], y=df_merged['人数'], mode='markers+text',
                    name='2025年', text=df_merged['月'].astype(str) + "月", textposition='top right',
                    marker={"size": 10, "color": '#1f77b4'}
                ))
                fig_scatter1.update_layout(
                    title="【高山_観光】検索数 vs 人数",
                    xaxis={"title": "高山_観光 検索数（相対値）", "range": [0, 100]},
                    yaxis={"title": "人数"},
                    margin={"t": 40, "b": 40, "l": 50, "r": 50},
                    height=450,
                    legend={"orientation": "h", "yanchor": "bottom", "y": 1.05, "xanchor": "right", "x": 1}
                )
                st.plotly_chart(fig_scatter1, use_container_width=True)
                
            with col_s2:
                # 散布図2（takayama 検索トレンド vs 外国人延べ宿泊者数）
                lag_options = ["差分無し（X=Y）", "1か月前の検索数", "2か月前の検索数", "3か月前の検索数", "4か月前の検索数"]
                selected_lag = st.selectbox("検索トレンドのラグを選択:", lag_options)
                lag_index = lag_options.index(selected_lag)
                
                fig_scatter2 = go.Figure()
                
                # 2025年分プロット
                if not df_acc.empty and '外国人延べ宿泊者数' in df_acc.columns:
                    y_fgn_2025 = list(df_acc['外国人延べ宿泊者数'])
                    if len(y_fgn_2025) == 12:
                        x_takayama_2025 = [takayama_trend_2022_2025[i] for i in range(36 - lag_index, 48 - lag_index)]
                        fig_scatter2.add_trace(go.Scatter(
                            x=x_takayama_2025, y=y_fgn_2025, mode='markers+text',
                            name='2025年', text=[f"{m}月" for m in range(1, 13)], textposition='top right',
                            marker={"size": 10, "color": '#2ca02c'}
                        ))
                
                fig_scatter2.update_layout(
                    title="【takayama】検索数 vs 外国人宿泊数",
                    xaxis={"title": "「takayama」検索数(X月)", "range": [0, 100]},
                    yaxis={"title": "外国人延べ宿泊者数(Y月)"},
                    margin={"t": 40, "b": 40, "l": 50, "r": 50},
                    height=450,
                    legend={"orientation": "h", "yanchor": "bottom", "y": 1.05, "xanchor": "right", "x": 1}
                )
                st.plotly_chart(fig_scatter2, use_container_width=True)

            st.markdown("### �📊 四半期ごとの総合トレンド分析")
            
            # 四半期の列を作成
            df_merged['四半期'] = ((df_merged['月'] - 1) // 3) + 1
            df_all_merged['四半期'] = ((df_all_merged['月'] - 1) // 3) + 1
            
            for q in sorted(df_merged['四半期'].dropna().unique()):
                df_q_taka = df_merged[df_merged['四半期'] == q]
                df_q_all = df_all_merged[df_all_merged['四半期'] == q]
                
                taka_this = df_q_taka['人数'].sum()
                taka_prev = df_q_taka['前年人数'].sum()
                all_this = df_q_all['人数'].sum()
                all_prev = df_q_all['全国前年人数'].sum()
                
                if taka_prev > 0 and all_prev > 0:
                    yoy_taka = round((taka_this / taka_prev) * 100, 1)
                    yoy_all = round((all_this / all_prev) * 100, 1)
                    diff = round(yoy_taka - yoy_all, 1)
                    
                    # 検索トレンドの四半期平均を計算
                    q_trend_avg = round(df_q_taka['検索トレンド（相対値）'].mean(), 1)
                    
                    q_int = int(q)
                    start_month = (q_int - 1) * 3 + 1
                    end_month = q_int * 3
                    
                    if q_int == 1:
                        macro_comment = "【国内マクロ・為替相場】物価高による節約志向等で個人消費が力強さに欠け、輸入増などで実質GDPはマイナス成長（－0.2%）と国内は厳しい環境でした。為替は円安傾向を背景に、輸入物価を通じた食料品などの価格上昇圧力が続きました。"
                        inbound_comment = "【インバウンド】1月に単月過去最高（378万人）、3月に最速で累計1,000万人突破と、海外からの需要は記録的な爆発力を見せました。"
                        climate_comment = "【天候の状況】2月に飛騨地方の山地を中心に記録的大雪がありましたが、平均気温・降水量・日照時間などは全体的に平年並の推移でした。"
                        trend_comment = f"【ネット検索動向】国内向け検索（高山_観光）は平均 {q_trend_avg}（35〜44）と春に向けて着実に上昇しています。一方、海外向け「takayama」検索数は1月に50から始まり、春の訪日シーズン（桜の時期等）に向けて3月には56と上昇の兆しを見せています。"
                        stay_comment = "【宿泊の動向】客室稼働率は平均60%台で堅調に推移し、特に1月から2月にかけて外国人を中心とした宿泊実績が全体の過半数を占める形で高稼働を牽引しました。"
                        if yoy_taka >= yoy_all:
                            local_comment = f"【高山市の全体考察】全国平均を **{diff}ポイント上回りました**。国内の消費が冷え込む逆風や大雪の影響があったものの、記録的ペースのインバウンド客をうまく取り込み、牽引したと推測されます。"
                        else:
                            local_comment = f"【高山市の全体考察】全国平均を **{abs(diff)}ポイント下回りました**。インバウンドは絶好調でしたが、大雪による交通アクセス面の制約や国内客の旅行控えの下押し圧力を受けた可能性があります。"
                    elif q_int == 2:
                        macro_comment = "【国内マクロ・為替相場】外需寄与で実質GDPは小幅プラス（＋0.3%）に復帰したものの、国内の内需本格回復はまだ遅れている状況でした。為替相場は円安が進行し、輸出企業の業績を押し上げる一方で、輸入コスト増による国内消費の下押し圧力ともなりました。"
                        inbound_comment = "【インバウンド】4月に390万人という凄まじい記録を叩き出し、上半期で最速の累計2,000万人超えを達成しました。"
                        climate_comment = "【天候の状況】5月中旬と異例の早さで梅雨入りし、6月に大雨が降りましたが、6月下旬に早くも梅雨明けとなり、気温は記録的に高くなりました。"
                        trend_comment = f"【ネット検索動向】国内向け検索は5月に56まで上昇（四半期平均 {q_trend_avg}）し、GWや初夏にかけての注目度が鮮明に表れています。一方、「takayama」検索数は4月に一時「86」まで急騰し、春のビッグウェーブとなるインバウンドの強い関心を牽引しています。"
                        stay_comment = "【宿泊の動向】4月〜5月は外国人宿泊客数が大きく貢献し、客室稼働率は70%を超える高い水準を記録しました。6月は閑散期傾向が出ています。"
                        if yoy_taka >= yoy_all:
                            local_comment = f"【高山市の全体考察】全国平均を **{diff}ポイント上回りました**。国内需要の弱さをGWの集客と絶好調のインバウンド需要でカバーし、早い梅雨明けによる好天も好影響を与えたと考えられます。"
                        else:
                            local_comment = f"【高山市の全体考察】全国平均を **{abs(diff)}ポイント下回りました**。早い梅雨入りや6月の大雨の影響に加えて、訪日客数が他の大都市圏へ集中した影響などから客足が伸び悩んだ可能性があります。"
                    elif q_int == 3:
                        macro_comment = "【国内マクロ・為替相場】トランプ関税リスク等で再びマイナス成長（－0.4%）となりましたが、賃上げ効果で個人の消費マインド自体は持ち直しつつありました。為替は150円台と業績想定より円安で推移し、輸出企業やインバウンド消費の追い風となりました。"
                        inbound_comment = "【インバウンド】夏場も月340万人規模を維持し、9月には過去最速で累計3,000万人を達成する異次元の活況ぶりでした。"
                        climate_comment = "【天候の状況】7月・8月は記録的猛暑かつ日照時間も過去最高となり、局地的な雷雨もありました。9月は前半に台風15号による大雨がありましたが、後半は晴れが続きました。"
                        trend_comment = f"【ネット検索動向】国内向け検索は8月の61から9月はなんと71まで急伸し（平均 {q_trend_avg}）、年間で最もネット上の国内関心が爆発した時期です。「takayama」検索数も夏場は落ち着きを見せつつも、9月には「72」へと急伸しており、秋のピークに向けた外国人の関心の高まりが伺えます。"
                        stay_comment = "【宿泊の動向】8月の夏休み需要で全体の延べ宿泊者数が13万人泊を超えピークとなりました。この時期は国内客の割合が高く、客室稼働率も71%と好調でした。"
                        if yoy_taka >= yoy_all:
                            local_comment = f"【高山市の全体考察】全国平均を **{diff}ポイント上回りました**。猛暑や局地的大雨の中でも、検索関心の異常なほどの高まりや国内外の根強い需要が噛み合い、マクロの停滞を跳ね除けました。"
                        else:
                            local_comment = f"【高山市の全体考察】全国平均を **{abs(diff)}ポイント下回りました**。検索関心等への盛り上がりは強かったものの、記録的猛暑や台風等の天候要因が遠方への旅行の手控えに直結した可能性があります。"
                    elif q_int == 4:
                        macro_comment = "【国内マクロ・為替相場】個人消費の増加等でプラス成長（＋0.1%）に回復。物価上昇率も鈍化し、内需を後押しする環境が整い始めました。為替の円安による企業収益の好調が全体を下支えしつつも、物価高動向への注視が続く局面となりました。"
                        inbound_comment = "【インバウンド】10月に389万人と秋の紅葉シーズン需要が爆発し、年間を通じ記録的推移が続きました。"
                        climate_comment = "【天候の状況】10月は台風接近などで前線が停滞し雨が多くなりましたが、11月中旬以降は晴れる日が多く、12月は一時的に冬型の気圧配置で寒気の影響を受けました。"
                        trend_comment = f"【ネット検索動向】国内向けは10月（56）から12月（33）へとピークを越えて急激に落ち着きを見せました（平均 {q_trend_avg}）。しかし、「takayama」検索数は10月に年間最高値の「99」を記録、11月も「88」と非常に高い水準を維持し、秋の紅葉・祭りシーズンにおける桁違いのインバウンド関心と需要の爆発を裏付けています。"
                        stay_comment = "【宿泊の動向】10月〜11月の秋の観光シーズンにおいて、客室稼働率は年間を通じ最高の75%前後をマークしました。"
                        if yoy_taka >= yoy_all:
                            local_comment = f"【高山市の全体考察】全国平均を **{diff}ポイント上回りました**。10月に雨が多い傾向はありましたが、紅葉需要や国内の消費回復トレンドという追い風を受け、宿泊施設の高稼働もそれを裏付けています。"
                        else:
                            local_comment = f"【高山市の全体考察】全国平均を **{abs(diff)}ポイント下回りました**。10月の長雨・台風の影響によるキャンセルや、検索トレンドの急落が示す通りピーク以降の散発的な反動減に引っ張られた懸念があります。"
                    else:
                        macro_comment = "【国内マクロ・為替相場】統計データ上の特記事項はありません。"
                        inbound_comment = "【インバウンド】特記事項はありません。"
                        climate_comment = "【天候の状況】特記事項はありません。"
                        trend_comment = "【ネット検索動向】特記事項はありません。"
                        stay_comment = "【宿泊の動向】特記事項はありません。"
                        local_comment = f"【高山市の全体考察】全国平均との差は {diff}ポイント でした。"
                    
                    st.info(
                        f"**第{q_int}四半期（{start_month}〜{end_month}月）インサイト:**\n\n"
                        f"高山市の対前年比は **{yoy_taka}%**（前年同期: {int(taka_prev):,}人 → 本年: {int(taka_this):,}人）、"
                        f"全国の対前年比は **{yoy_all}%** となりました。\n\n"
                        f"1) {macro_comment}\n"
                        f"2) {inbound_comment}\n"
                        f"3) {climate_comment}\n"
                        f"4) {trend_comment}\n"
                        f"5) {stay_comment}\n\n"
                        f"6) {local_comment}"
                    )
            
            st.caption("出典　 1.【国内マクロ・為替相場】内閣府政策統括官、2025年度日本経済レポートならびにMUFG、2025／2026年度短期経済見通し、2.【インバウンド】JNTO、訪日外客統計、3.【天候の状況】岐阜地方気象台、令和7(2025)年の岐阜県の天候、4.【検索動向】Google Trend（キーワード：高山＿観光）、5.【宿泊の動向】観光庁、宿泊観光統計をもとにAIで要約した。6.【高山市の全体考察】は、1～5の情報をAIで集約した。")
            
            st.subheader("集計データテーブル (2025年観光客数ならびに検索数トレンド)")
            # 表示用のテーブルを整形 (不要な列を除外、欠損値を補完)
            df_display = df_merged.drop(columns=['text', '全国text', '年', '四半期'], errors='ignore').fillna({'前年人数': '-', '対前年比': '-', '全国対前年比': '-'})
            st.dataframe(df_display, hide_index=True)
            
            if not df_acc.empty:
                st.subheader("宿泊の動向 データテーブル (2025年)")
                st.dataframe(df_acc.fillna({'客室稼働率(%)': '-', '定員稼働率(%)': '-'}), hide_index=True)
                
            col_d1, col_d2 = st.columns([7, 3])
            with col_d1:
                st.header("【Ⅱ．今後の動向】", anchor="doukou")
            with col_d2:
                st.markdown("<div style='text-align: right; margin-top: 25px;'>"
                            "<a href='#genjyo' style='text-decoration: none; padding: 5px 15px; margin-right: 5px; background-color: #f0f2f6; border-radius: 5px; color: #31333F; font-weight: bold;'>⬆ I．現状</a>"
                            "<a href='#other_regions' style='text-decoration: none; padding: 5px 15px; background-color: #f0f2f6; border-radius: 5px; color: #31333F; font-weight: bold;'>⬇ Ⅲ．他地域の動向</a>"
                            "</div>", unsafe_allow_html=True)

            # ====== 回帰分析による将来推計 ======
            try:
                from sklearn.linear_model import LinearRegression
                import numpy as np
                
                st.markdown("### 📈 回帰分析による将来推計（検索トレンドと人数・宿泊数の予測）")
                
                col_reg1, col_reg2 = st.columns(2)
                
                with col_reg1:
                    st.markdown("#### 【モデルA】 高山入込者数の将来推計")
                    # 目的変数(y): 人数
                    # 説明変数(X): 検索トレンド（相対値） -> 高山_観光, 9月ダミー
                    trend_a = df_merged['検索トレンド（相対値）'].values
                    months_a = df_merged['月'].values
                    dummy_9_a = np.where(months_a == 9, 1, 0)
                    X_train = np.column_stack((trend_a, dummy_9_a))
                    y_train = df_merged['人数'].values
                    
                    model = LinearRegression()
                    model.fit(X_train, y_train)
                    
                    coef = model.coef_
                    r2 = model.score(X_train, y_train)
                    
                    # t値の手動計算
                    y_pred_train = model.predict(X_train)
                    n_a = len(y_train)
                    k_a = X_train.shape[1]
                    mse = np.sum((y_train - y_pred_train) ** 2) / (n_a - k_a - 1)
                    
                    X_design_a = np.column_stack((np.ones(n_a), X_train))
                    var_b_a = mse * np.diag(np.linalg.pinv(X_design_a.T @ X_design_a))
                    se_coef = np.sqrt(var_b_a)[1:]
                    
                    t_values_a = np.zeros(k_a)
                    for i in range(k_a):
                        if se_coef[i] > 0:
                            t_values_a[i] = coef[i] / se_coef[i]
                    
                    # 評価結果の表示
                    st.write(f"**【分析結果】** 決定係数 ($R^2$): `{r2:.3f}`")
                    st.write(
                        f"<span style='font-size: 13.5px;'>**係数／t値** [検索:`{coef[0]:,.1f}` (`{t_values_a[0]:.2f}`)] [9月:`{coef[1]:,.1f}` (`{t_values_a[1]:.2f}`)]</span>", 
                        unsafe_allow_html=True
                    )
                    
                    # 将来予測スライダー
                    st.markdown("**【未来データの生成】** 翌12か月の実績ベース乗数")
                    multiplier_1 = st.slider("「高山_観光」検索トレンド変動", min_value=0.5, max_value=1.5, value=1.0, step=0.05, key="reg_sim_1")
                    
                    # 予測データ生成
                    future_X = X_train.copy()
                    future_X[:, 0] = future_X[:, 0] * multiplier_1
                    future_y_pred = model.predict(future_X)
                    
                    fig_pred1 = go.Figure()
                    fig_pred1.add_trace(go.Scatter(
                        x=[f"{m}月" for m in df_merged['月']], y=y_train, mode='lines+markers+text',
                        name='実績 (2025年)', text=[f"{int(v):,}" for v in y_train], textposition='bottom center',
                        line={"color": '#1f77b4', "width": 3}, marker={"size": 8}
                    ))
                    
                    # 対2025年比の計算とテキスト作成
                    ratio_text = [f"{int(pred):,} ({int(pred/act * 100)}%)" if act > 0 else f"{int(pred):,}" for pred, act in zip(future_y_pred, y_train)]
                    
                    fig_pred1.add_trace(go.Scatter(
                        x=[f"{m}月" for m in df_merged['月']], y=future_y_pred, mode='lines+markers+text',
                        name='予測値 (対25年比)', text=ratio_text, textposition='top center',
                        line={"color": '#ff7f0e', "width": 3, "dash": 'dash'}, marker={"size": 8}
                    ))
                    fig_pred1.update_layout(
                        title=f"入込者数推計（検索トレンド {multiplier_1:.2f}倍想定）",
                        xaxis={"title": "時期"},
                        yaxis={"title": "人数 (推計値)", "rangemode": "tozero"},
                        height=430,
                        margin={"t": 40, "b": 40, "l": 50, "r": 50},
                        legend={"orientation": "h", "yanchor": "bottom", "y": 1.05, "xanchor": "right", "x": 1}
                    )
                    st.plotly_chart(fig_pred1, use_container_width=True)
                
                with col_reg2:
                    st.markdown("#### 【モデルB】 外国人延べ宿泊者数の将来推計")
                    if not df_acc.empty and '外国人延べ宿泊者数' in df_acc.columns:
                        # 目的変数(y): 外国人延べ宿泊者数
                        y_train_fgn = df_acc['外国人延べ宿泊者数'].values
                        
                        # 説明変数(X): takayama検索数, 1・2月ダミー, 9月ダミー
                        takayama_trend = df_merged['takayama検索数'].values
                        months = df_merged['月'].values
                        dummy_1_2 = np.where((months == 1) | (months == 2), 1, 0)
                        dummy_9 = np.where(months == 9, 1, 0)
                        
                        X_train_fgn = np.column_stack((takayama_trend, dummy_1_2, dummy_9))
                        
                        model_fgn = LinearRegression()
                        model_fgn.fit(X_train_fgn, y_train_fgn)
                        
                        coef_fgn = model_fgn.coef_
                        r2_fgn = model_fgn.score(X_train_fgn, y_train_fgn)
                        
                        # t値の手動計算 (多重回帰)
                        y_pred_fgn_train = model_fgn.predict(X_train_fgn)
                        n = len(y_train_fgn)
                        k = X_train_fgn.shape[1]
                        mse_fgn = np.sum((y_train_fgn - y_pred_fgn_train) ** 2) / (n - k - 1)
                        
                        X_design = np.column_stack((np.ones(n), X_train_fgn))
                        var_b = mse_fgn * np.diag(np.linalg.pinv(X_design.T @ X_design))
                        se_fgn = np.sqrt(var_b)[1:] # 最初の要素は切片なので除外
                        
                        t_values_fgn = np.zeros(k) # se=0時の回避
                        for i in range(k):
                            if se_fgn[i] > 0:
                                t_values_fgn[i] = coef_fgn[i] / se_fgn[i]
                                
                        # 評価結果の表示
                        st.write(f"**【分析結果】** 決定係数 ($R^2$): `{r2_fgn:.3f}`")
                        st.write(
                            f"<span style='font-size: 13.5px;'>**係数／t値** [検索:`{coef_fgn[0]:,.1f}` (`{t_values_fgn[0]:.2f}`)] [1･2月:`{coef_fgn[1]:,.1f}` (`{t_values_fgn[1]:.2f}`)] [9月:`{coef_fgn[2]:,.1f}` (`{t_values_fgn[2]:.2f}`)]</span>", 
                            unsafe_allow_html=True
                        )
                        
                        # 将来予測スライダー
                        st.markdown("**【未来データの生成】** 翌12か月の実績ベース乗数")
                        multiplier_2 = st.slider("「takayama」検索トレンド変動", min_value=0.5, max_value=1.5, value=1.0, step=0.05, key="reg_sim_2")
                        
                        # 予測データ生成 (新しい検索トレンド * 倍率、ダミー変数は来期も同じ月を想定)
                        future_X_fgn = X_train_fgn.copy()
                        future_X_fgn[:, 0] = future_X_fgn[:, 0] * multiplier_2
                        future_y_pred_fgn = model_fgn.predict(future_X_fgn)
                        
                        fig_pred2 = go.Figure()
                        fig_pred2.add_trace(go.Scatter(
                            x=[f"{m}月" for m in df_merged['月']], y=y_train_fgn, mode='lines+markers+text',
                            name='実績 (2025年)', text=[f"{int(v):,}" for v in y_train_fgn], textposition='bottom center',
                            line={"color": '#2ca02c', "width": 3}, marker={"size": 8}
                        ))
                        
                        # 対2025年比の計算とテキスト作成
                        ratio_text_fgn = [f"{int(pred):,} ({int(pred/act * 100)}%)" if act > 0 else f"{int(pred):,}" for pred, act in zip(future_y_pred_fgn, y_train_fgn)]
                        
                        fig_pred2.add_trace(go.Scatter(
                            x=[f"{m}月" for m in df_merged['月']], y=future_y_pred_fgn, mode='lines+markers+text',
                            name='予測値 (対25年比)', text=ratio_text_fgn, textposition='top center',
                            line={"color": '#d62728', "width": 3, "dash": 'dash'}, marker={"size": 8}
                        ))
                        fig_pred2.update_layout(
                            title=f"外国人延べ宿泊数推計（トレンド {multiplier_2:.2f}倍想定）",
                            xaxis={"title": "時期"},
                            yaxis={"title": "外国人延べ宿泊数 (推計値)", "rangemode": "tozero"},
                            height=430,
                            margin={"t": 40, "b": 40, "l": 50, "r": 50},
                            legend={"orientation": "h", "yanchor": "bottom", "y": 1.05, "xanchor": "right", "x": 1}
                        )
                        st.plotly_chart(fig_pred2, use_container_width=True)
                    else:
                        st.warning("外国人延べ宿泊者数のデータが存在しません。")
                
            except ImportError:
                st.warning("scikit-learnライブラリがインストールされていないため、回帰分析を実行できません。")
            except Exception as e:
                st.error(f"回帰分析の実行中にエラーが発生しました: {e}")
            # ========================================

            st.info("""
**1) 【国内マクロ】**
2026年度は総合経済対策が追い風となり、内需主導で景気が拡大する見通しです。2027年度には消費税減税や輸出の持ち直しを受け、さらなる成長の加速が見込まれます。高水準の賃上げも伴い、底堅い経済成長が期待されます。

**2) 【為替】**
日米の金融政策の方向感により変動しつつも、実質金利の低さが意識されるなかで円高圧力は引き続き限定的であり、おおむね1ドル＝150円台の円安水準が継続する見通しです。

**3) 【天候】**
今後の気温は、暖かい空気に覆われやすいため、3月から5月にかけて全体的に「高い」見込みです（特に4月と5月は平年より高い確率が50〜60%）。
天気については数日の周期で変わりますが、岐阜県山間部（高山市を含む）における3月の天候は、平年と同様に曇りや雪または雨の日が多いでしょう。4月および5月については、平年と同様に晴れの日が多くなる見込みです。降水量は向こう3か月でほぼ平年並となると予想されています。
            """)
            
            st.caption("出典　 1) 【国内マクロ-みずほリサーチ＆テクノロジーズ株、2026・2027年内外経済見通し】 2) 【為替-みずほリサーチ＆テクノロジーズ(株)】3）【天候の状況-名古屋地方気象台、向こう３か月の天候の見通し－東海地方(3月～5月)】をAIで集約")
            
            # --- Ⅲ．他地域の動向 ---
            st.markdown("---")
            col_t1, col_t2 = st.columns([7, 3])
            with col_t1:
                st.header("【Ⅲ．他地域の動向】", anchor="other_regions")
            with col_t2:
                st.markdown("<div style='text-align: right; margin-top: 25px;'>"
                            "<a href='#genjyo' style='text-decoration: none; padding: 5px 15px; margin-right: 5px; background-color: #f0f2f6; border-radius: 5px; color: #31333F; font-weight: bold;'>⬆ I．現状</a>"
                            "<a href='#doukou' style='text-decoration: none; padding: 5px 15px; background-color: #f0f2f6; border-radius: 5px; color: #31333F; font-weight: bold;'>⬆ Ⅱ．今後の動向</a>"
                            "</div>", unsafe_allow_html=True)
                            
            df_tot = load_total_accommodation_data()
            if not df_tot.empty:
                st.markdown("### 対象地域（他地域）の選択とトレンド比較")
                st.markdown("比較する市区町村を最大2つまで選択できます。")
                
                # プルダウンメニュー
                prefectures = sorted(df_tot['都道県'].dropna().unique().tolist())
                
                st.markdown("**対象地域 1**")
                col_sel1_1, col_sel1_2 = st.columns(2)
                with col_sel1_1:
                    sel_pref1 = st.selectbox("都道府県 1:", ["指定なし"] + prefectures, index=0, key="pref1")
                with col_sel1_2:
                    if sel_pref1 != "指定なし":
                        cities_in_pref1 = sorted(df_tot[df_tot['都道県'] == sel_pref1]['市町村名'].dropna().unique().tolist())
                        sel_city1 = st.selectbox("市区町村 1:", ["指定なし"] + cities_in_pref1, index=0, key="city1")
                    else:
                        st.selectbox("市区町村 1:", ["指定なし"], index=0, disabled=True, key="city1_dummy")
                        sel_city1 = "指定なし"
                    
                st.markdown("**対象地域 2 (比較用・省略可)**")
                col_sel2_1, col_sel2_2 = st.columns(2)
                with col_sel2_1:
                    sel_pref2 = st.selectbox("都道府県 2:", ["指定なし"] + prefectures, index=0, key="pref2")
                with col_sel2_2:
                    if sel_pref2 != "指定なし":
                        cities_in_pref2 = sorted(df_tot[df_tot['都道県'] == sel_pref2]['市町村名'].dropna().unique().tolist())
                        sel_city2 = st.selectbox("市区町村 2:", ["指定なし"] + cities_in_pref2, index=0, key="city2")
                    else:
                        st.selectbox("市区町村 2:", ["指定なし"], index=0, disabled=True, key="city2_dummy")
                        sel_city2 = "指定なし"
                        
                if sel_city1:
                    # 2025年の1〜12月の月ごとの1月比インデックス計算関数
                    def make_index_series(s: pd.Series) -> pd.Series:
                        v_base = float(s.iloc[0]) if len(s) > 0 else 0.0
                        if v_base > 0:
                            return (s / v_base * 100).round(1).fillna(0)
                        return s * 0
                        
                    def create_text(s):
                        return s.apply(lambda x: str(x) if x > 0 else "")

                    all_months = pd.DataFrame({'月': range(1, 13)})
                    
                    # ---- 【人数】データの準備 (city2025total.csvを使用) ----
                    df_pop_tot = load_total_population_data()
                    
                    if not df_pop_tot.empty:
                        # 対象地域（選択された都道府県・市町村）の人数
                        df_sel_pop = None
                        if sel_city1 != "指定なし" and sel_pref1 != "指定なし":
                            if '都道県' in df_pop_tot.columns:
                                df_sel_pop = df_pop_tot[(df_pop_tot['都道県'] == sel_pref1) & (df_pop_tot['市町村名'] == sel_city1)].groupby('月_num', as_index=False)['人数'].sum().rename(columns={'月_num': '月'})
                            else:
                                df_sel_pop = df_pop_tot[df_pop_tot['市町村名'] == sel_city1].groupby('月_num', as_index=False)['人数'].sum().rename(columns={'月_num': '月'})
                                
                            df_sel_pop = pd.merge(all_months, df_sel_pop, on='月', how='left').fillna({'人数': 0})
                            df_sel_pop['index'] = make_index_series(df_sel_pop['人数'])
                            df_sel_pop['text'] = create_text(df_sel_pop['index'])
                        
                        df_sel2_pop = None
                        if sel_city2 != "指定なし" and sel_pref2 != "指定なし":
                            if '都道県' in df_pop_tot.columns:
                                df_sel2_pop = df_pop_tot[(df_pop_tot['都道県'] == sel_pref2) & (df_pop_tot['市町村名'] == sel_city2)].groupby('月_num', as_index=False)['人数'].sum().rename(columns={'月_num': '月'})
                            else:
                                df_sel2_pop = df_pop_tot[df_pop_tot['市町村名'] == sel_city2].groupby('月_num', as_index=False)['人数'].sum().rename(columns={'月_num': '月'})
                                
                            df_sel2_pop = pd.merge(all_months, df_sel2_pop, on='月', how='left').fillna({'人数': 0})
                            df_sel2_pop['index'] = make_index_series(df_sel2_pop['人数'])
                            df_sel2_pop['text'] = create_text(df_sel2_pop['index'])
                        
                        # 全国の人数代表値（合計値）
                        df_all_pop_g = df_pop_tot.groupby('月_num', as_index=False)['人数'].sum().rename(columns={'月_num': '月'})
                        df_all_pop = pd.merge(all_months, df_all_pop_g, on='月', how='left').fillna({'人数': 0})
                        df_all_pop['index'] = make_index_series(df_all_pop['人数'])
                        df_all_pop['text'] = create_text(df_all_pop['index'])
                        
                        # 高山市の人数
                        if '都道県' in df_pop_tot.columns:
                            df_taka_pop = df_pop_tot[(df_pop_tot['都道県'] == '岐阜県') & (df_pop_tot['市町村名'] == '高山市')].groupby('月_num', as_index=False)['人数'].sum().rename(columns={'月_num': '月'})
                        else:
                            df_taka_pop = df_pop_tot[df_pop_tot['市町村名'] == '高山市'].groupby('月_num', as_index=False)['人数'].sum().rename(columns={'月_num': '月'})
                            
                        df_taka_pop = pd.merge(all_months, df_taka_pop, on='月', how='left').fillna({'人数': 0})
                        df_taka_pop['index'] = make_index_series(df_taka_pop['人数'])
                        df_taka_pop['text'] = create_text(df_taka_pop['index'])
                        
                        has_pop_data = True
                    else:
                        st.warning("※ 人数のグラフを表示するには、`irikomi` フォルダ内に `city2025.csv` を配置してください。")
                        has_pop_data = False
                    
                    # ---- 【宿泊者数】データの準備 (df_totを使用) ----
                    df_sel_acc = None
                    if sel_city1 != "指定なし" and sel_pref1 != "指定なし":
                        df_sel_acc = df_tot[(df_tot['都道県'] == sel_pref1) & (df_tot['市町村名'] == sel_city1)].groupby('月_num', as_index=False)['延べ宿泊者数'].sum().rename(columns={'月_num': '月'})
                        df_sel_acc = pd.merge(all_months, df_sel_acc, on='月', how='left').fillna({'延べ宿泊者数': 0})
                        df_sel_acc['index'] = make_index_series(df_sel_acc['延べ宿泊者数'])
                        df_sel_acc['text'] = create_text(df_sel_acc['index'])
                    
                    df_sel2_acc = None
                    if sel_city2 != "指定なし" and sel_pref2 != "指定なし":
                        df_sel2_acc = df_tot[(df_tot['都道県'] == sel_pref2) & (df_tot['市町村名'] == sel_city2)].groupby('月_num', as_index=False)['延べ宿泊者数'].sum().rename(columns={'月_num': '月'})
                        df_sel2_acc = pd.merge(all_months, df_sel2_acc, on='月', how='left').fillna({'延べ宿泊者数': 0})
                        df_sel2_acc['index'] = make_index_series(df_sel2_acc['延べ宿泊者数'])
                        df_sel2_acc['text'] = create_text(df_sel2_acc['index'])
                    
                    # 全国の宿泊者数代表値（合計値）
                    df_all_acc_g = df_tot.groupby('月_num', as_index=False)['延べ宿泊者数'].sum().rename(columns={'月_num': '月'})
                    df_all_acc = pd.merge(all_months, df_all_acc_g, on='月', how='left').fillna({'延べ宿泊者数': 0})
                    df_all_acc['index'] = make_index_series(df_all_acc['延べ宿泊者数'])
                    df_all_acc['text'] = create_text(df_all_acc['index'])
                    
                    # 高山市の宿泊者数
                    df_taka_acc = df_tot[(df_tot['都道県'] == '岐阜県') & (df_tot['市町村名'] == '高山市')].groupby('月_num', as_index=False)['延べ宿泊者数'].sum().rename(columns={'月_num': '月'})
                    df_taka_acc = pd.merge(all_months, df_taka_acc, on='月', how='left').fillna({'延べ宿泊者数': 0})
                    df_taka_acc['index'] = make_index_series(df_taka_acc['延べ宿泊者数'])
                    df_taka_acc['text'] = create_text(df_taka_acc['index'])

                    # グラフ1: 人数
                    if has_pop_data:
                        t1_str = sel_city1 if sel_city1 != '指定なし' else ''
                        t2_str = sel_city2 if sel_city2 != '指定なし' else ''
                        join_str = ' と ' if t1_str and t2_str else ''
                        cities_title = f"{t1_str}{join_str}{t2_str}"
                        title_pop = f"#### 🚌 {cities_title + ' ' if cities_title else ''}人数 トレンド (2025年)"
                        st.markdown(title_pop + "<span style='font-size: 0.6em; color: gray; margin-left:15px;'>出典：デジタル観光統計（日本観光振興協会）</span>", unsafe_allow_html=True)
                        fig_pop = go.Figure()
                        if df_sel_pop is not None:
                            fig_pop.add_trace(go.Scatter(
                                x=df_sel_pop['月'], y=df_sel_pop['index'], mode='lines+markers+text',
                                name=f'{sel_city1} 人数', text=df_sel_pop['text'], textposition='top center',
                                line={"color": '#1f77b4', "width": 3}, marker={"size": 8}
                            ))
                        if df_sel2_pop is not None:
                            fig_pop.add_trace(go.Scatter(
                                x=df_sel2_pop['月'], y=df_sel2_pop['index'], mode='lines+markers+text',
                                name=f'{sel_city2} 人数', text=df_sel2_pop['text'], textposition='top left',
                                line={"color": '#e377c2', "width": 3}, marker={"size": 8}
                            ))
                        fig_pop.add_trace(go.Scatter(
                            x=df_all_pop['月'], y=df_all_pop['index'], mode='lines+markers+text',
                            name='全国 代表値 (人数計)', text=df_all_pop['text'], textposition='bottom center', 
                            line={"color": '#ff7f0e', "width": 2, "dash": 'dash'}, marker={"size": 6}
                        ))
                        fig_pop.add_trace(go.Scatter(
                            x=df_taka_pop['月'], y=df_taka_pop['index'], mode='lines+markers+text',
                            name='高山市 人数', text=df_taka_pop['text'], textposition='top right', 
                            line={"color": '#9467bd', "width": 2, "dash": 'dot'}, marker={"size": 6}
                        ))
                        fig_pop.update_layout(
                            title=f"人数トレンド比較 (1月を100とした場合の各月の比率)",
                            xaxis={"title": "月", "tickmode": 'linear', "dtick": 1, "tick0": 1, "range": [0.5, 12.5]},
                            yaxis={"title": "比率 (1月=100)"},
                            margin={"t": 50, "b": 50, "l": 50, "r": 50},
                            height=500,
                            legend={"orientation": "h", "yanchor": "bottom", "y": 1.05, "xanchor": "right", "x": 1}
                        )
                        st.plotly_chart(fig_pop, use_container_width=True)

                    # グラフ2: 宿泊者数
                    t1_str = sel_city1 if sel_city1 != '指定なし' else ''
                    t2_str = sel_city2 if sel_city2 != '指定なし' else ''
                    join_str = ' と ' if t1_str and t2_str else ''
                    cities_title = f"{t1_str}{join_str}{t2_str}"
                    title_acc = f"#### 🏨 {cities_title + ' ' if cities_title else ''}宿泊者数 トレンド (2025年)"
                    st.markdown(title_acc + "<span style='font-size: 0.6em; color: gray; margin-left:15px;'>出典：宿泊旅行統計（観光庁）</span>", unsafe_allow_html=True)
                    fig_acc = go.Figure()
                    if df_sel_acc is not None:
                        fig_acc.add_trace(go.Scatter(
                            x=df_sel_acc['月'], y=df_sel_acc['index'], mode='lines+markers+text',
                            name=f'{sel_city1} 宿泊者数', text=df_sel_acc['text'], textposition='top center',
                            line={"color": '#2ca02c', "width": 3}, marker={"size": 8}
                        ))
                    if df_sel2_acc is not None:
                        fig_acc.add_trace(go.Scatter(
                            x=df_sel2_acc['月'], y=df_sel2_acc['index'], mode='lines+markers+text',
                            name=f'{sel_city2} 宿泊者数', text=df_sel2_acc['text'], textposition='top left',
                            line={"color": '#bcbd22', "width": 3}, marker={"size": 8}
                        ))
                    fig_acc.add_trace(go.Scatter(
                        x=df_all_acc['月'], y=df_all_acc['index'], mode='lines+markers+text',
                        name='全国 代表値 (宿泊者数合計)', text=df_all_acc['text'], textposition='bottom center', 
                        line={"color": '#d62728', "width": 2, "dash": 'dash'}, marker={"size": 6}
                    ))
                    fig_acc.add_trace(go.Scatter(
                        x=df_taka_acc['月'], y=df_taka_acc['index'], mode='lines+markers+text',
                        name='高山市 宿泊者数', text=df_taka_acc['text'], textposition='top right', 
                        line={"color": '#9467bd', "width": 2, "dash": 'dot'}, marker={"size": 6}
                    ))
                    fig_acc.update_layout(
                        title=f"宿泊者数トレンド比較 (1月を100とした場合の各月の比率)",
                        xaxis={"title": "月", "tickmode": 'linear', "dtick": 1, "tick0": 1, "range": [0.5, 12.5]},
                        yaxis={"title": "比率 (1月=100)"},
                        margin={"t": 50, "b": 50, "l": 50, "r": 50},
                        height=500,
                        legend={"orientation": "h", "yanchor": "bottom", "y": 1.05, "xanchor": "right", "x": 1}
                    )
                    st.plotly_chart(fig_acc, use_container_width=True)

        else:
            st.warning(f"{target_city}のデータは見つかりませんでした。")
    else:
        st.error("データが存在しません。ファイルやデータ形式を確認してください。")

if __name__ == "__main__":
    main()
