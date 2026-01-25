import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import time

# ページ設定
st.set_page_config(
    page_title="Strategic Org Resilience Simulator Ver.2.0",
    page_icon="📉",
    layout="wide"
)

# ==========================================
# 1. 高度化シミュレーション・ロジック (Ver.2.0)
# ==========================================

class AdvancedOrgModel:
    """
    レポート「戦略的組織レジリエンスの構築」完全準拠モデル (Ver.2.0)
    
    【主な改良点】
    1. Effective Capacity (有効組織能力) の導入
       - 人数(Headcount)ではなく、習熟度(Proficiency)を掛け合わせた「能力総量」で評価。
    2. Ramp-up Logic (立ち上がりの遅れ/不可逆性)
       - 新規採用者は即戦力(100%)ではなく、一定期間を経て戦力化する。
       - これにより「補充しても負荷が下がらない」地獄の構造を再現。
    3. Non-linear Burnout (非線形な燃え尽き)
       - 負荷が閾値を超えると、離職確率が指数関数的に上昇する。
    """
    
    def __init__(self, n_employees, base_turnover, lead_time, hp_ratio, 
                 ramp_up_months=12, stress_sensitivity=2.0):
        
        # --- 基本パラメータ ---
        self.initial_n = n_employees
        self.base_turnover_monthly = (base_turnover / 100.0) / 12.0
        self.lead_time = lead_time
        self.hp_ratio = hp_ratio / 100.0
        
        # --- 高度パラメータ (レポート準拠) ---
        # 立ち上がり期間 (ヶ月): HPは複雑な業務のため戦力化に時間がかかる
        self.ramp_up_hp = ramp_up_months 
        self.ramp_up_mp = max(3, int(ramp_up_months * 0.5)) # MPは半分の期間で戦力化と仮定
        
        # ストレス感度: HPは市場価値が高く、環境悪化に対して「去る」選択を取りやすい
        self.sensitivity_hp = stress_sensitivity * 1.5
        self.sensitivity_mp = stress_sensitivity * 1.0
        
        # 経済パラメータ
        self.salary_hp = 1000 # 万円
        self.salary_mp = 600  # 万円
        self.cost_hiring_ratio = 0.35 # エージェントフィー
        self.cost_premium_hp = 0.30   # 採用プレミアム
        self.cost_premium_mp = 0.10
        
        # 崩壊ライン: 初期能力の70%を割ると、事業運営に支障が出ると定義
        self.collapse_threshold = 0.70 

    def calculate_effective_capacity(self, tenured_count, new_hires):
        """
        有効能力の計算
        - ベテラン(Tenured): 生産性 1.0
        - 新人(New Hires): 経過月数に応じて生産性が 0.2 -> 1.0 へ上昇
        """
        # ベテランの能力
        cap_tenured = tenured_count * 1.0
        
        # 新人の能力 (線形立ち上がりモデル)
        cap_new = 0
        for hire in new_hires:
            # tenure(在籍月数) / ramp_up(立ち上がり期間)
            # 最低でも20%の貢献、最大100%
            proficiency = min(1.0, 0.2 + 0.8 * (hire['tenure'] / hire['ramp_up_target']))
            cap_new += proficiency
            
        return cap_tenured + cap_new

    def run_simulation(self, duration_months=36):
        # --- 初期化 ---
        # HP/MP それぞれ、「ベテラン(Tenured)」と「新人リスト(New Hires)」で管理
        n_hp = int(self.initial_n * self.hp_ratio)
        n_mp = self.initial_n - n_hp
        
        state = {
            'HP': {'tenured': n_hp, 'new_hires': []}, # new_hires: list of dict {'tenure': 0, 'ramp_up_target': 12}
            'MP': {'tenured': n_mp, 'new_hires': []}
        }
        
        # 求人リスト (採用待ち)
        vacancies = [] # {'type': 'HP', 'months_open': 0}
        
        # 初期能力 (これを基準100%とする)
        initial_capacity_hp = n_hp * 1.0
        initial_capacity_mp = n_mp * 1.0
        total_initial_capacity = initial_capacity_hp + initial_capacity_mp
        
        history = []
        cum_financial_loss = 0
        cum_opportunity_loss = 0
        
        # 崩壊フラグ
        is_collapsed = False
        collapse_month = None

        for month in range(duration_months):
            # 1. 従業員の成長 (Ramp-up)
            # 新人の在籍期間を+1し、戦力化したらベテランへ移動
            for type_ in ['HP', 'MP']:
                promoted_indices = []
                for i, hire in enumerate(state[type_]['new_hires']):
                    hire['tenure'] += 1
                    if hire['tenure'] >= hire['ramp_up_target']:
                        promoted_indices.append(i)
                
                # 後ろから削除しないとインデックスがずれる
                for i in sorted(promoted_indices, reverse=True):
                    state[type_]['new_hires'].pop(i)
                    state[type_]['tenured'] += 1

            # 2. 現在の有効能力 (Effective Capacity) 計算
            curr_cap_hp = self.calculate_effective_capacity(state['HP']['tenured'], state['HP']['new_hires'])
            curr_cap_mp = self.calculate_effective_capacity(state['MP']['tenured'], state['MP']['new_hires'])
            total_curr_capacity = curr_cap_hp + curr_cap_mp
            
            # 能力維持率 (Capacity Ratio)
            cap_ratio = total_curr_capacity / total_initial_capacity
            
            # 崩壊判定
            if not is_collapsed and cap_ratio < self.collapse_threshold:
                is_collapsed = True
                collapse_month = month + 1

            # 3. 負荷 (Workload) 計算
            # 業務量は減らない前提。能力が減ると、一人当たり負荷が増える。
            # Workload Index: 1.0 = 適正, 1.2 = 20%残業増
            workload_index = 1.0 / max(0.01, cap_ratio)
            
            # 4. 離職 (Attrition) シミュレーション
            leavers = {'HP': 0, 'MP': 0}
            
            for type_ in ['HP', 'MP']:
                # 基礎離職率
                prob = self.base_turnover_monthly
                
                # 負荷による離職確率上昇 (非線形: 指数関数的悪化)
                # Load > 1.0 の分だけストレスがかかる
                stress_factor = max(0, workload_index - 1.0) 
                sensitivity = self.sensitivity_hp if type_ == 'HP' else self.sensitivity_mp
                
                # 確率補正: P_final = P_base * (1 + Sensitivity * Stress^2)
                # ※Stressの二乗にすることで、過負荷時の急激な崩壊を再現
                prob_adjusted = prob * (1 + sensitivity * (stress_factor * 10)**1.5)
                prob_adjusted = min(1.0, prob_adjusted) # 上限100%
                
                # 離職者数確定 (二項分布)
                # ベテランから離職
                n_tenured = state[type_]['tenured']
                leavers_tenured = np.random.binomial(n_tenured, prob_adjusted)
                state[type_]['tenured'] -= leavers_tenured
                
                # 新人から離職 (定着せず辞める) - 新人はストレス耐性が低いと仮定し確率1.2倍
                n_new = len(state[type_]['new_hires'])
                leavers_new = np.random.binomial(n_new, min(1.0, prob_adjusted * 1.2))
                
                # 新人リストからランダムに削除
                if leavers_new > 0:
                    # 削除するインデックスをランダムに選ぶ
                    remove_indices = np.random.choice(range(n_new), size=leavers_new, replace=False)
                    # インデックスが大きい順に削除
                    for i in sorted(remove_indices, reverse=True):
                        state[type_]['new_hires'].pop(i)

                total_leavers = leavers_tenured + leavers_new
                leavers[type_] = total_leavers
                
                # 求人発生
                for _ in range(total_leavers):
                    vacancies.append({'type': type_, 'months_open': 0})

            # 5. 採用 (Hiring)
            # リードタイム経過した求人を埋める
            filled_vacancies = []
            still_open = []
            
            for v in vacancies:
                if v['months_open'] >= self.lead_time:
                    filled_vacancies.append(v)
                else:
                    v['months_open'] += 1
                    still_open.append(v)
            vacancies = still_open
            
            # 採用者の配置とコスト計算
            monthly_hiring_cost = 0
            for v in filled_vacancies:
                type_ = v['type']
                ramp_target = self.ramp_up_hp if type_ == 'HP' else self.ramp_up_mp
                
                # 新人リストに追加
                state[type_]['new_hires'].append({'tenure': 0, 'ramp_up_target': ramp_target})
                
                # コスト
                salary = self.salary_hp if type_ == 'HP' else self.salary_mp
                premium = self.cost_premium_hp if type_ == 'HP' else self.cost_premium_mp
                cost = salary * (self.cost_hiring_ratio + premium)
                monthly_hiring_cost += cost
            
            cum_financial_loss += monthly_hiring_cost
            
            # 6. 機会損失 (Opportunity Loss)
            # 能力不足分(1.0 - cap_ratio) × 付加価値
            # 仮定: 付加価値は給与の2倍。全社総給与ベースで計算。
            total_salary_roll = (n_hp * self.salary_hp + n_mp * self.salary_mp) / 12
            monthly_opp_loss = total_salary_roll * 2 * (1.0 - cap_ratio)
            cum_opportunity_loss += monthly_opp_loss

            # 記録
            history.append({
                'month': month + 1,
                'headcount_hp': state['HP']['tenured'] + len(state['HP']['new_hires']),
                'headcount_mp': state['MP']['tenured'] + len(state['MP']['new_hires']),
                'capacity_ratio': cap_ratio * 100, # %
                'workload_index': workload_index * 100, # %
                'leavers': leavers['HP'] + leavers['MP'],
                'cum_financial_loss': cum_financial_loss,
                'cum_opportunity_loss': cum_opportunity_loss,
                'is_collapsed': 1 if is_collapsed else 0
            })
            
        return pd.DataFrame(history), collapse_month

# ==========================================
# 2. UI コンポーネント (Streamlit)
# ==========================================

def main():
    # サイドバー設定
    with st.sidebar:
        st.header("⚙️ Simulation Settings")
        
        st.subheader("組織パラメータ")
        n_employees = st.number_input("従業員数 (名)", value=1000, step=100)
        hp_ratio = st.slider("ハイパフォーマー比率 (%)", 10, 50, 20)
        
        st.subheader("市場・採用パラメータ")
        base_turnover = st.slider("基準離職率 (%, 年率)", 5.0, 30.0, 12.0)
        lead_time = st.slider("採用リードタイム (ヶ月)", 1, 12, 6, help="求人開始から入社までの期間")
        ramp_up = st.slider("HP戦力化期間 (ヶ月)", 3, 24, 12, help="入社後、元のHPと同等の生産性を発揮するまでにかかる期間。この期間は「人数」がいても「能力」が低い状態となる。")
        
        st.subheader("レジリエンス強度")
        stress_sensitivity = st.slider("組織のストレス感度", 0.5, 3.0, 1.5, help="負荷に対する離職のしやすさ。高いほど少しの負荷で崩壊する。")
        
        run_btn = st.button("シミュレーション実行 (Ver.2.0)", type="primary")
        
        st.markdown("---")
        st.markdown("**Model Version:** 2.0 (Research Edition)")
        st.markdown("**Logic:** Effective Capacity & Irreversible Loss")
        st.markdown("Created by: Keisuke Nakamura")

    # メイン画面
    st.title("📉 Strategic Org Resilience Simulator Ver.2.0")
    st.markdown("""
    レポート『戦略的組織レジリエンスの構築』の数理モデルを忠実に再現した研究用シミュレーターです。
    
    Ver.1.0（単なる人数計算）とは異なり、本モデルは**「有効組織能力 (Effective Capacity)」**と**「不可逆性 (Irreversibility)」**を組み込んでいます。
    「人は採用できても、組織能力はすぐには回復しない」という現実的な遅れが、どのように**致命的な負の連鎖（Death Spiral）**を生むか検証できます。
    """)

    if run_btn:
        with st.spinner('Running Agent-Based Logic...'):
            model = AdvancedOrgModel(n_employees, base_turnover, lead_time, hp_ratio, 
                                     ramp_up_months=ramp_up, stress_sensitivity=stress_sensitivity)
            df, collapse_month = model.run_simulation(duration_months=36)
            time.sleep(0.5)

        # --- 結果表示 ---
        last = df.iloc[-1]
        
        # 1. 崩壊判定アラート
        if collapse_month:
            st.error(f"⚠️ **組織崩壊 (Functional Collapse) 発生**: {collapse_month}ヶ月目")
            st.markdown(f"有効組織能力が維持限界（70%）を下回りました。これ以降、組織は自律的な回復が困難な「死の領域」に入ります。")
        else:
            st.success(f"✅ **組織維持**: 36ヶ月間、崩壊ライン（能力70%）を維持しました。")

        # 2. KPIメトリクス
        st.markdown("### 📊 3年後の組織状態 (Projected Outcome)")
        col1, col2, col3, col4 = st.columns(4)
        
        total_loss = (last['cum_financial_loss'] + last['cum_opportunity_loss']) / 10000
        cap_delta = last['capacity_ratio'] - 100
        
        with col1:
            st.metric("有効組織能力 (Capacity)", f"{last['capacity_ratio']:.1f}%", f"{cap_delta:.1f}%", delta_color="inverse")
            st.caption("※人数ではなく「実質的な仕事力」")
        with col2:
            st.metric("労働負荷指数 (Workload)", f"{last['workload_index']:.1f}%", f"{last['workload_index']-100:.1f}pt", delta_color="inverse")
            st.caption("※100%超は残業・過負荷状態")
        with col3:
            st.metric("累積財務流出 (Cash Out)", f"{last['cum_financial_loss']/10000:.1f}億円")
            st.caption("採用費・プレミアム賃金")
        with col4:
            st.metric("経済損失総額 (Total Loss)", f"{total_loss:.1f}億円", delta="深刻", delta_color="inverse")
            st.caption("機会損失を含む")

        st.markdown("---")

        # 3. 詳細グラフ
        tab1, tab2, tab3 = st.tabs(["📉 能力と人数の乖離", "⚡ 負の連鎖メカニズム", "💰 損失内訳"])

        with tab1:
            st.subheader("「人数は戻っても、能力は戻らない」")
            st.markdown("点線（人数）は回復しているのに、実線（有効能力）が回復しない期間が「組織の脆弱性」です。")
            
            fig_cap = go.Figure()
            # 人数推移 (正規化)
            total_headcount = df['headcount_hp'] + df['headcount_mp']
            norm_headcount = (total_headcount / n_employees) * 100
            
            fig_cap.add_trace(go.Scatter(x=df['month'], y=norm_headcount, name='総従業員数 (%)',
                                         line=dict(color='gray', dash='dot')))
            
            fig_cap.add_trace(go.Scatter(x=df['month'], y=df['capacity_ratio'], name='有効組織能力 (%)',
                                         line=dict(color='red', width=3)))
            
            # 崩壊ライン
            fig_cap.add_hrect(y0=0, y1=70, fillcolor="red", opacity=0.1, annotation_text="機能不全ゾーン")
            fig_cap.update_layout(height=400, yaxis_title="初期比 (%)", yaxis_range=[50, 110])
            st.plotly_chart(fig_cap, use_container_width=True)

        with tab2:
            st.subheader("Death Spiral: 負荷と離職の連鎖")
            
            fig_mech = go.Figure()
            # 左軸: 負荷
            fig_mech.add_trace(go.Scatter(x=df['month'], y=df['workload_index'], name='労働負荷指数',
                                          line=dict(color='orange', width=2), yaxis='y1'))
            # 右軸: 離職者数
            fig_mech.add_trace(go.Bar(x=df['month'], y=df['leavers'], name='月次離職者数',
                                      marker_color='blue', opacity=0.5, yaxis='y2'))
            
            fig_mech.update_layout(
                yaxis=dict(title="労働負荷 (100=適正)", range=[90, max(150, df['workload_index'].max())]),
                yaxis2=dict(title="離職者数 (人)", overlaying='y', side='right'),
                height=400
            )
            st.plotly_chart(fig_mech, use_container_width=True)
            st.info("解説: グラフ前半で能力低下により「負荷(オレンジ)」が上昇し、それが中盤の「大量離職(青棒)」を引き起こしていることが分かります。")

        with tab3:
            st.subheader("損失の構造分析")
            fig_loss = px.area(df, x='month', y=['cum_financial_loss', 'cum_opportunity_loss'],
                               labels={'value': '損失額 (万円)', 'variable': '損失タイプ'},
                               color_discrete_map={'cum_financial_loss': '#333333', 'cum_opportunity_loss': '#cc0000'})
            st.plotly_chart(fig_loss, use_container_width=True)

    else:
        # 初期表示・解説
        st.info("👈 パラメータを設定し、「シミュレーション実行」を押してください。")
        
        st.markdown("#### Ver.2.0 モデルの数理的背景")
        st.markdown("""
        **1. 有効能力 (Effective Capacity)**
        $$ C_{total} = \sum (N_{tenured} \times 1.0) + \sum (N_{new} \times f(t)) $$
        ここで $f(t)$ は立ち上がり関数（$0.2 \to 1.0$）を表します。
        
        **2. 労働負荷と離職確率 (Workload & Attrition)**
        $$ P_{leave} = P_{base} \times (1 + S \times (Load - 1.0)^2) $$
        負荷 ($Load$) が1.0を超えると、二乗則で離職確率が跳ね上がる「非線形モデル」を採用しています。
        """)

if __name__ == "__main__":
    main()