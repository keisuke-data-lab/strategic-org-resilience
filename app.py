import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time

# ページ設定
st.set_page_config(
    page_title="Strategic Org Resilience Simulator Ver.4.1",
    page_icon="🛡️",
    layout="wide"
)

# ==========================================
# 1. シミュレーション・ロジック (Ver.4.0)
# ==========================================

class AdvancedOrgModel:
    """
    レポート「戦略的組織レジリエンスの構築」完全準拠モデル
    Ver.4.0: 生存分析・ヒートマップ対応版
    """
    
    def __init__(self, n_employees, base_turnover, lead_time, hp_ratio, 
                 salary_hp, salary_mp, 
                 ramp_up_months=12, stress_sensitivity=2.0):
        
        self.initial_n = n_employees
        self.base_turnover_rate = base_turnover / 100.0
        self.base_turnover_monthly = self.base_turnover_rate / 12.0
        self.lead_time = lead_time
        self.hp_ratio = hp_ratio / 100.0
        
        self.salary_hp = salary_hp 
        self.salary_mp = salary_mp 
        self.cost_hiring_ratio = 0.35
        self.cost_premium_hp = 0.30
        self.cost_premium_mp = 0.10
        
        self.ramp_up_hp = ramp_up_months 
        self.ramp_up_mp = max(3, int(ramp_up_months * 0.5)) 
        self.sensitivity_hp = stress_sensitivity * 1.5
        self.sensitivity_mp = stress_sensitivity * 1.0
        self.collapse_threshold = 0.70 

    def calculate_effective_capacity(self, tenured_count, new_hires):
        cap_tenured = tenured_count * 1.0
        cap_new = 0
        for hire in new_hires:
            # 習熟度曲線 (S字カーブの簡易版: 線形近似)
            proficiency = min(1.0, 0.2 + 0.8 * (hire['tenure'] / hire['ramp_up_target']))
            cap_new += proficiency
        return cap_tenured + cap_new

    def run_simulation(self, duration_months=36):
        n_hp = int(self.initial_n * self.hp_ratio)
        n_mp = self.initial_n - n_hp
        
        # 初期メンバーの生存数追跡用
        initial_cohort = {'HP': n_hp, 'MP': n_mp}
        
        state = {
            'HP': {'tenured': n_hp, 'new_hires': []}, 
            'MP': {'tenured': n_mp, 'new_hires': []}
        }
        
        vacancies = [] 
        
        initial_capacity_hp = n_hp * 1.0
        initial_capacity_mp = n_mp * 1.0
        total_initial_capacity = initial_capacity_hp + initial_capacity_mp
        
        if total_initial_capacity == 0: total_initial_capacity = 1.0
        
        history = []
        
        cum_actual_cost = 0
        cum_budget_cost = 0
        cum_opp_loss = 0
        
        is_collapsed = False
        collapse_month = None

        for month in range(duration_months):
            # 予算計算
            expected_leavers_hp = self.initial_n * self.hp_ratio * self.base_turnover_monthly
            expected_leavers_mp = self.initial_n * (1 - self.hp_ratio) * self.base_turnover_monthly
            
            monthly_budget_hp = expected_leavers_hp * self.salary_hp * self.cost_hiring_ratio
            monthly_budget_mp = expected_leavers_mp * self.salary_mp * self.cost_hiring_ratio
            cum_budget_cost += (monthly_budget_hp + monthly_budget_mp)

            # 成長プロセス
            for type_ in ['HP', 'MP']:
                promoted_indices = []
                for i, hire in enumerate(state[type_]['new_hires']):
                    hire['tenure'] += 1
                    if hire['tenure'] >= hire['ramp_up_target']:
                        promoted_indices.append(i)
                for i in sorted(promoted_indices, reverse=True):
                    state[type_]['new_hires'].pop(i)
                    state[type_]['tenured'] += 1

            # 能力・負荷計算
            curr_cap_hp = self.calculate_effective_capacity(state['HP']['tenured'], state['HP']['new_hires'])
            curr_cap_mp = self.calculate_effective_capacity(state['MP']['tenured'], state['MP']['new_hires'])
            total_curr_capacity = curr_cap_hp + curr_cap_mp
            cap_ratio = total_curr_capacity / total_initial_capacity
            
            if not is_collapsed and cap_ratio < self.collapse_threshold:
                is_collapsed = True
                collapse_month = month + 1
            
            workload_index = 1.0 / max(0.01, cap_ratio)
            
            # 離職プロセス
            leavers = {'HP': 0, 'MP': 0}
            for type_ in ['HP', 'MP']:
                prob = self.base_turnover_monthly
                stress_factor = max(0, workload_index - 1.0) 
                sensitivity = self.sensitivity_hp if type_ == 'HP' else self.sensitivity_mp
                # ストレスによる離職率の非線形増加
                prob_adjusted = min(1.0, prob * (1 + sensitivity * (stress_factor * 10)**1.5))
                
                # ベテラン離職
                n_tenured = state[type_]['tenured']
                leavers_tenured = np.random.binomial(n_tenured, prob_adjusted)
                state[type_]['tenured'] -= leavers_tenured
                
                # 新人離職 (定着失敗)
                n_new = len(state[type_]['new_hires'])
                leavers_new = np.random.binomial(n_new, min(1.0, prob_adjusted * 1.2))
                if leavers_new > 0:
                    remove_indices = np.random.choice(range(n_new), size=leavers_new, replace=False)
                    for i in sorted(remove_indices, reverse=True):
                        state[type_]['new_hires'].pop(i)

                total_leavers = leavers_tenured + leavers_new
                leavers[type_] = total_leavers
                for _ in range(total_leavers):
                    vacancies.append({'type': type_, 'months_open': 0})
                
                # --- 生存分析用ロジック ---
                current_total = n_tenured + n_new
                if current_total > 0:
                    ratio_initial = initial_cohort[type_] / (current_total + total_leavers)
                    leavers_from_initial = int(total_leavers * ratio_initial)
                    initial_cohort[type_] = max(0, initial_cohort[type_] - leavers_from_initial)

            # 採用プロセス
            filled_vacancies = []
            still_open = []
            for v in vacancies:
                if v['months_open'] >= self.lead_time:
                    filled_vacancies.append(v)
                else:
                    v['months_open'] += 1
                    still_open.append(v)
            vacancies = still_open
            
            monthly_actual_cost = 0
            for v in filled_vacancies:
                type_ = v['type']
                ramp_target = self.ramp_up_hp if type_ == 'HP' else self.ramp_up_mp
                state[type_]['new_hires'].append({'tenure': 0, 'ramp_up_target': ramp_target})
                
                salary = self.salary_hp if type_ == 'HP' else self.salary_mp
                premium = self.cost_premium_hp if type_ == 'HP' else self.cost_premium_mp
                cost = salary * (self.cost_hiring_ratio + premium)
                monthly_actual_cost += cost
            
            cum_actual_cost += monthly_actual_cost
            
            # 機会損失
            total_salary_roll = (n_hp * self.salary_hp + n_mp * self.salary_mp) / 12
            monthly_opp_loss = total_salary_roll * 2 * (1.0 - cap_ratio)
            cum_opp_loss += monthly_opp_loss

            # 現在のヘッドカウント計算
            current_hp = state['HP']['tenured'] + len(state['HP']['new_hires'])
            current_mp = state['MP']['tenured'] + len(state['MP']['new_hires'])

            history.append({
                'month': month + 1,
                'capacity_ratio': cap_ratio * 100,
                'workload_index': workload_index * 100,
                'leavers_total': leavers['HP'] + leavers['MP'],
                'cum_actual_cost': cum_actual_cost,
                'cum_budget_cost': cum_budget_cost,
                'cum_excess_cost': max(0, cum_actual_cost - cum_budget_cost), 
                'cum_opportunity_loss': cum_opp_loss,
                # 生存分析用データ
                'survivors_hp': initial_cohort['HP'],
                'survivors_mp': initial_cohort['MP'],
                'survivor_rate_hp': (initial_cohort['HP'] / n_hp * 100) if n_hp > 0 else 0,
                'survivor_rate_mp': (initial_cohort['MP'] / n_mp * 100) if n_mp > 0 else 0,
                # ヘッドカウント (Tab4用)
                'headcount_hp': current_hp,
                'headcount_mp': current_mp
            })
            
        return pd.DataFrame(history), collapse_month

# ==========================================
# 2. UI コンポーネント (Ver.4.0)
# ==========================================

def main():
    with st.sidebar:
        st.header("⚙️ Settings")
        
        st.subheader("1. 組織設定")
        n_employees = st.number_input("従業員数 (名)", min_value=10, value=1000, step=10)
        hp_ratio = st.slider("ハイパフォーマー比率 (%)", 10, 50, 20)
        
        st.subheader("2. 年収設定")
        salary_hp = st.number_input("HP 年収 (万円)", value=1000, step=50)
        salary_mp = st.number_input("MP/LP 年収 (万円)", value=600, step=50)

        st.subheader("3. 市場環境")
        base_turnover = st.slider("基準離職率 (%, 年率)", 5.0, 30.0, 12.0)
        lead_time = st.slider("採用リードタイム (ヶ月)", 1, 12, 6)
        ramp_up = st.slider("HP戦力化期間 (ヶ月)", 3, 24, 12)
        stress_sensitivity = st.slider("組織のストレス感度", 0.5, 3.0, 1.5)
        
        run_btn = st.button("シミュレーション実行", type="primary")
        
        st.markdown("---")
        st.markdown("**Ver.4.1 (Actionable Insights)**")
        st.markdown("Created by: Keisuke Nakamura")

    st.title("🛡️ Strategic Org Resilience Simulator Ver.4.1")
    st.markdown("""
    **「生存分析」「リスクヒートマップ」「ティッピングポイント」**を実装したDSSプロトタイプです。
    組織崩壊の「時期」と「構造」を多角的に診断します。
    """)

    if run_btn:
        with st.spinner('Calculating Advanced Analytics...'):
            model = AdvancedOrgModel(
                n_employees, base_turnover, lead_time, hp_ratio, 
                salary_hp, salary_mp,
                ramp_up_months=ramp_up, stress_sensitivity=stress_sensitivity
            )
            df, collapse_month = model.run_simulation(duration_months=36)
            time.sleep(0.5) # UXのための演出

        last = df.iloc[-1]
        
        # --- アラート: ティッピングポイント (最優先表示) ---
        if collapse_month:
            st.error(f"⚠️ **Tipping Point Alert**: {collapse_month}ヶ月目に「組織崩壊ライン(有効能力70%未満)」を突破しました。即時の介入が必要です。")
        else:
            st.success("✅ **Stable**: 36ヶ月間、組織は健全性を維持しました。")
        
        st.markdown("### 📊 3年間の経済インパクト分析")
        
        col1, col2, col3 = st.columns(3)
        
        excess_loss = last['cum_excess_cost'] / 10000
        budget_cost = last['cum_budget_cost'] / 10000
        actual_cost = last['cum_actual_cost'] / 10000
        
        if budget_cost > 0:
            pct_diff = ((actual_cost / budget_cost) - 1) * 100
            delta_str = f"予算比 +{pct_diff:.0f}%"
        else:
            delta_str = "予算設定なし"

        with col1:
            st.metric("財務超過損失 (Excess Loss)", f"{excess_loss:.1f}億円", delta_str, delta_color="inverse")
            
        opp_loss = last['cum_opportunity_loss'] / 10000
        with col2:
            st.metric("機会損失 (Opportunity Loss)", f"{opp_loss:.1f}億円", "Value Destruction", delta_color="inverse")

        total_impact = excess_loss + opp_loss
        with col3:
            st.metric("推定経済損失総額", f"{total_impact:.1f}億円", delta="Critical", delta_color="inverse")

        st.markdown("---")

        # ========================================================
        # Advanced Visualizations Tabs
        # ========================================================
        tab1, tab2, tab3, tab4 = st.tabs(["🔥 リスク・ヒートマップ", "📉 生存曲線 (Survival)", "💰 コスト構造", "⚡ 組織状態"])
        
        # 1. リスク・ヒートマップ
        with tab1:
            st.subheader("複合リスクの時系列ヒートマップ")
            
            # データの正規化 (0-1スケール)
            norm_workload = df['workload_index'] / df['workload_index'].max()
            norm_leavers = df['leavers_total'] / df['leavers_total'].max()
            norm_loss = (df['cum_excess_cost'] + df['cum_opportunity_loss'])
            max_loss = norm_loss.max()
            if max_loss > 0:
                norm_loss = norm_loss / max_loss
            else:
                norm_loss = norm_loss * 0
            
            # ヒートマップ用データ作成
            heatmap_z = [
                norm_workload.tolist(),
                norm_leavers.tolist(),
                norm_loss.tolist()
            ]
            
            # ホバー用の実数値テキスト
            text_workload = [f"{v:.0f}%" for v in df['workload_index']]
            text_leavers = [f"{v}名" for v in df['leavers_total']]
            text_loss = [f"{(v/10000):.1f}億" for v in (df['cum_excess_cost'] + df['cum_opportunity_loss'])]
            
            heatmap_text = [text_workload, text_leavers, text_loss]
            
            fig_heat = go.Figure(data=go.Heatmap(
                z=heatmap_z,
                x=df['month'],
                y=['労働負荷', '月次離職数', '累積損失'],
                colorscale='RdYlGn_r', # 緑(低) -> 赤(高)
                text=heatmap_text,
                texttemplate="", 
                hovertemplate='月: %{x}<br>%{y}: %{text}<extra></extra>'
            ))
            
            if collapse_month:
                fig_heat.add_vline(x=collapse_month, line_width=3, line_dash="dash", line_color="black")
                fig_heat.add_annotation(x=collapse_month, y=0, text="崩壊点", showarrow=True, arrowhead=1, yshift=10)

            fig_heat.update_layout(height=350, xaxis_title="経過月数", margin=dict(l=50, r=50, t=30, b=30))
            st.plotly_chart(fig_heat, use_container_width=True)
            
            # --- 解説テキスト挿入 ---
            # 最も負荷が高かった月を特定
            peak_load_idx = df['workload_index'].idxmax()
            peak_load_month = df.iloc[peak_load_idx]['month']
            action_deadline = max(1, peak_load_month - lead_time)
            
            st.info(f"""
            **💡 分析とアクション:**
            このヒートマップはリスクの「連鎖」を示しています。シミュレーションでは **{peak_load_month}ヶ月目** に労働負荷がピークに達しています。
            ここでの組織崩壊を防ぐためには、採用リードタイム({lead_time}ヶ月)を考慮し、遅くとも **{action_deadline}ヶ月目** までに人員補充を完了させる必要があります。
            """)

        # 2. 生存曲線
        with tab2:
            st.subheader("初期メンバーの生存分析 (Survival Analysis)")
            
            fig_surv = go.Figure()
            
            # HP Survival
            fig_surv.add_trace(go.Scatter(
                x=df['month'], y=df['survivor_rate_hp'],
                mode='lines', name='ハイパフォーマー(HP) 残存率',
                line=dict(color='#d62728', width=3)
            ))
            
            # MP Survival
            fig_surv.add_trace(go.Scatter(
                x=df['month'], y=df['survivor_rate_mp'],
                mode='lines', name='一般社員(MP) 残存率',
                line=dict(color='#1f77b4', width=2)
            ))
            
            fig_surv.add_hline(y=50, line_dash="dot", annotation_text="Danger Line (50%)", annotation_position="bottom right")
            
            fig_surv.update_layout(
                yaxis_title="残存率 (%)", xaxis_title="経過月数",
                yaxis_range=[0, 105], height=350,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_surv, use_container_width=True)

            # --- 解説テキスト挿入 ---
            final_hp_rate = last['survivor_rate_hp']
            drop_rate = 100 - final_hp_rate
            
            if drop_rate > 30:
                advice_msg = f"初期HPの **{drop_rate:.1f}%** が流出しており、組織の「暗黙知」が失われています。リテンション施策（昇給・環境改善）の優先度を上げてください。"
                advice_type = "error" # 赤枠
            else:
                advice_msg = f"HPの流出は **{drop_rate:.1f}%** に留まっており、比較的安定しています。"
                advice_type = "success" # 緑枠
            
            if advice_type == "error":
                st.error(f"**💡 警告:** {advice_msg}")
            else:
                st.success(f"**💡 分析:** {advice_msg}")

        # 3. コスト構造
        with tab3:
            st.subheader("コスト構造の分解")
            fig_cost = go.Figure()
            
            fig_cost.add_trace(go.Scatter(
                x=df['month'], y=df['cum_budget_cost']/10000,
                mode='lines', name='通常予算 (Budget)',
                line=dict(color='gray', dash='dash'), stackgroup='one'
            ))
            
            fig_cost.add_trace(go.Scatter(
                x=df['month'], y=df['cum_excess_cost']/10000,
                mode='lines', name='超過コスト (Excess)',
                line=dict(color='#d62728'), stackgroup='one'
            ))
            
            fig_cost.add_trace(go.Scatter(
                x=df['month'], y=df['cum_opportunity_loss']/10000,
                mode='lines', name='機会損失 (Opp. Loss)',
                line=dict(color='#ff7f0e'), stackgroup='one'
            ))
            
            if collapse_month:
                fig_cost.add_vline(x=collapse_month, line_width=1, line_dash="dot", line_color="black")

            fig_cost.update_layout(xaxis_title="経過月数", yaxis_title="累積額 (億円)", height=350)
            st.plotly_chart(fig_cost, use_container_width=True)

            # --- 解説テキスト挿入 ---
            excess_total = excess_loss + opp_loss
            st.info(f"""
            **💡 コスト分析:**
            グレーの領域は「必要な投資」ですが、その上の赤とオレンジの領域は、対応の遅れによって生じた **合計{excess_total:.1f}億円 の損失** です。
            この損失額の20-30%（約{(excess_total * 0.3):.1f}億円）を事前の「採用単価アップ」や「教育」に投資することで、最終的な総コストを圧縮できる可能性があります。
            """)

        # 4. 組織状態
        with tab4:
            st.subheader("有効能力と人員構成")
            fig_cap = go.Figure()
            
            total_headcount = df['headcount_hp'] + df['headcount_mp']
            if n_employees > 0:
                norm_headcount = (total_headcount / n_employees) * 100
            else:
                norm_headcount = 0
            
            fig_cap.add_trace(go.Scatter(x=df['month'], y=norm_headcount, name='在籍人数(対期初比%)', line=dict(color='gray', dash='dot')))
            fig_cap.add_trace(go.Scatter(x=df['month'], y=df['capacity_ratio'], name='有効能力(%)', line=dict(color='blue', width=3)))
            
            fig_cap.add_hrect(y0=0, y1=70, fillcolor="red", opacity=0.1, annotation_text="機能不全エリア")
            
            if collapse_month:
                fig_cap.add_annotation(
                    x=collapse_month, y=70, text="Tipping Point",
                    showarrow=True, arrowhead=1, bgcolor="red", bordercolor="white", font=dict(color="white")
                )
            
            fig_cap.update_layout(height=350)
            st.plotly_chart(fig_cap, use_container_width=True)

            # --- 解説テキスト挿入 ---
            if collapse_month:
                st.error(f"""
                **💡 警告:** グラフは「人数（点線）」と「実力（青線）」の乖離を示しています。
                シミュレーションでは **{collapse_month}ヶ月目** に組織能力が限界を迎えています。
                点線が戻っても青線が戻らない期間が、組織の「脆弱性」です。
                """)
            else:
                st.success("""
                **💡 良好:** 36ヶ月間、組織能力は崩壊ラインを維持できています。
                ただし、点線と青線のギャップ（＝戦力不足期間）が大きい時期は、現場の疲弊に注意してください。
                """)

if __name__ == "__main__":
    main()