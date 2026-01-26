import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import time

# ページ設定
st.set_page_config(
    page_title="Strategic Org Resilience Simulator Ver.3.2",
    page_icon="📉",
    layout="wide"
)

# ==========================================
# 1. シミュレーション・ロジック (Ver.3.2)
# ==========================================

class AdvancedOrgModel:
    """
    レポート「戦略的組織レジリエンスの構築」完全準拠モデル
    Ver.3.2: 小規模組織対応版
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
            proficiency = min(1.0, 0.2 + 0.8 * (hire['tenure'] / hire['ramp_up_target']))
            cap_new += proficiency
        return cap_tenured + cap_new

    def run_simulation(self, duration_months=36):
        n_hp = int(self.initial_n * self.hp_ratio)
        n_mp = self.initial_n - n_hp
        
        state = {
            'HP': {'tenured': n_hp, 'new_hires': []}, 
            'MP': {'tenured': n_mp, 'new_hires': []}
        }
        
        vacancies = [] 
        
        initial_capacity_hp = n_hp * 1.0
        initial_capacity_mp = n_mp * 1.0
        total_initial_capacity = initial_capacity_hp + initial_capacity_mp
        
        # 小規模組織でのゼロ除算エラー回避
        if total_initial_capacity == 0:
            total_initial_capacity = 1.0
        
        history = []
        
        cum_actual_cost = 0
        cum_budget_cost = 0
        cum_opp_loss = 0
        
        is_collapsed = False
        collapse_month = None

        for month in range(duration_months):
            # 予算コスト計算
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
                prob_adjusted = min(1.0, prob * (1 + sensitivity * (stress_factor * 10)**1.5))
                
                n_tenured = state[type_]['tenured']
                leavers_tenured = np.random.binomial(n_tenured, prob_adjusted)
                state[type_]['tenured'] -= leavers_tenured
                
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

            history.append({
                'month': month + 1,
                'capacity_ratio': cap_ratio * 100,
                'workload_index': workload_index * 100,
                'leavers': leavers['HP'] + leavers['MP'],
                'cum_actual_cost': cum_actual_cost,
                'cum_budget_cost': cum_budget_cost,
                'cum_excess_cost': max(0, cum_actual_cost - cum_budget_cost), 
                'cum_opportunity_loss': cum_opp_loss,
                'headcount_hp': state['HP']['tenured'] + len(state['HP']['new_hires']),
                'headcount_mp': state['MP']['tenured'] + len(state['MP']['new_hires']),
            })
            
        return pd.DataFrame(history), collapse_month

# ==========================================
# 2. UI コンポーネント (修正版)
# ==========================================

def main():
    with st.sidebar:
        st.header("⚙️ Settings (Ver.3.2)")
        
        st.subheader("1. 組織設定")
        # 【修正箇所】 min_value=10, step=10 に設定変更し、1000名以下も入力可能に
        n_employees = st.number_input("従業員数 (名)", min_value=10, value=1000, step=10,
                                      help="最小10名からシミュレーション可能です。")
        
        hp_ratio = st.slider("ハイパフォーマー比率 (%)", 10, 50, 20)
        
        st.subheader("2. 年収設定 (損益分岐用)")
        salary_hp = st.number_input("HP 年収 (万円)", value=1000, step=50)
        salary_mp = st.number_input("MP/LP 年収 (万円)", value=600, step=50)

        st.subheader("3. 市場環境")
        base_turnover = st.slider("基準離職率 (%, 年率)", 5.0, 30.0, 12.0)
        lead_time = st.slider("採用リードタイム (ヶ月)", 1, 12, 6)
        ramp_up = st.slider("HP戦力化期間 (ヶ月)", 3, 24, 12)
        stress_sensitivity = st.slider("組織のストレス感度", 0.5, 3.0, 1.5)
        
        run_btn = st.button("シミュレーション実行", type="primary")
        
        st.markdown("---")
        st.markdown("**Ver.3.2 (Small Org Support)**")
        st.markdown("Created by: Keisuke Nakamura")

    st.title("📉 Strategic Org Resilience Simulator Ver.3.2")
    st.markdown("""
    本シミュレーターは、単なるコスト総額ではなく、**「通常の離職・採用サイクルであればかからなかったはずの超過コスト（真の損失）」**を可視化します。
    100名以下の中小規模組織から、大企業まで幅広く分析可能です。
    """)

    if run_btn:
        with st.spinner('Calculating Budget vs Actual...'):
            model = AdvancedOrgModel(
                n_employees, base_turnover, lead_time, hp_ratio, 
                salary_hp, salary_mp,
                ramp_up_months=ramp_up, stress_sensitivity=stress_sensitivity
            )
            df, collapse_month = model.run_simulation(duration_months=36)
            time.sleep(0.5)

        last = df.iloc[-1]
        
        if collapse_month:
            st.error(f"⚠️ **組織崩壊**: {collapse_month}ヶ月目に機能不全ラインを突破しました。")
        
        st.markdown("### 📊 3年間の経済インパクト分析 (Budget vs Actual)")
        
        col1, col2, col3 = st.columns(3)
        
        # 0除算対策: 予算コストが極めて小さい場合のハンドリング
        excess_loss = last['cum_excess_cost'] / 10000
        budget_cost = last['cum_budget_cost'] / 10000
        actual_cost = last['cum_actual_cost'] / 10000
        
        if budget_cost > 0:
            pct_diff = ((actual_cost / budget_cost) - 1) * 100
            delta_str = f"予算比 +{pct_diff:.0f}%"
        else:
            delta_str = "予算設定なし"

        with col1:
            st.metric("財務超過損失 (Excess Loss)", 
                      f"{excess_loss:.1f}億円", 
                      delta_str,
                      delta_color="inverse")
            st.caption(f"採用費実績: {actual_cost:.1f}億 - 通常予算: {budget_cost:.1f}億")
            
        opp_loss = last['cum_opportunity_loss'] / 10000
        with col2:
            st.metric("機会損失 (Opportunity Loss)", 
                      f"{opp_loss:.1f}億円",
                      "売上・付加価値の未達分",
                      delta_color="inverse")

        total_impact = excess_loss + opp_loss
        with col3:
            st.metric("推定経済損失総額", 
                      f"{total_impact:.1f}億円",
                      delta="要・経営介入",
                      delta_color="inverse")

        st.markdown("---")

        tab1, tab2 = st.tabs(["💰 コスト構造の分解", "📉 組織状態"])
        
        with tab1:
            st.subheader("何が無駄な出費（損失）なのか？")
            fig_cost = go.Figure()
            
            fig_cost.add_trace(go.Scatter(
                x=df['month'], y=df['cum_budget_cost']/10000,
                mode='lines', name='通常採用予算 (Budget)',
                line=dict(color='gray', dash='dash'),
                stackgroup='one'
            ))
            
            fig_cost.add_trace(go.Scatter(
                x=df['month'], y=df['cum_excess_cost']/10000,
                mode='lines', name='超過財務コスト (Excess)',
                line=dict(color='#d62728'),
                stackgroup='one'
            ))
            
            fig_cost.add_trace(go.Scatter(
                x=df['month'], y=df['cum_opportunity_loss']/10000,
                mode='lines', name='機会損失 (Opp. Loss)',
                line=dict(color='#ff7f0e'),
                stackgroup='one'
            ))
            
            fig_cost.update_layout(
                title="累積コストの内訳推移 (億円)",
                xaxis_title="経過月数", yaxis_title="累積額 (億円)",
                height=450
            )
            st.plotly_chart(fig_cost, use_container_width=True)

        with tab2:
            fig_cap = go.Figure()
            total_headcount = df['headcount_hp'] + df['headcount_mp']
            # 人数が0の場合は0除算回避
            if n_employees > 0:
                norm_headcount = (total_headcount / n_employees) * 100
            else:
                norm_headcount = 0
            
            fig_cap.add_trace(go.Scatter(x=df['month'], y=norm_headcount, name='人数推移(%)', line=dict(color='gray', dash='dot')))
            fig_cap.add_trace(go.Scatter(x=df['month'], y=df['capacity_ratio'], name='有効能力(%)', line=dict(color='blue', width=3)))
            fig_cap.add_hrect(y0=0, y1=70, fillcolor="red", opacity=0.1, annotation_text="崩壊ライン")
            
            st.plotly_chart(fig_cap, use_container_width=True)

if __name__ == "__main__":
    main()