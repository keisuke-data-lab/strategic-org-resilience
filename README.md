# 🛡️ Strategic Organization Resilience Simulator
**Ver.4.1: 人的資本・業務依存構造・離職連鎖をモデル化する組織レジリエンス診断シミュレーター**

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://strategic-org-resilience-9ejs4h2kqqpx5zdwuygri9.streamlit.app/)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Type](https://img.shields.io/badge/Type-DSS_Prototype-green)
![Version](https://img.shields.io/badge/Version-4.1_Actionable_Insights-orange)

---

## 📸 Dashboard Demo
**▼ 実際のシミュレーション画面 (Ver.4.1)**
> パラメータ変更 → シミュレーション実行 → **「いつ崩壊するか」「いくら損失が出るか」「今何をすべきか」**を即座に算出します。

![Dashboard Demo](./images/demo_simulation.gif)

---

## 📌 Executive Summary
**「優秀な人材が一人抜けただけで、なぜ組織は急速に機能低下するのか？」**

本プロジェクトは、**「人的依存構造 × 業務負荷偏在 × 離職連鎖」**を数理モデルとして統合し、組織の「隠れた脆弱性」と「崩壊の臨界点（Tipping Point）」を可視化する**意思決定支援システム（DSS）プロトタイプ**です。

従来の静的なHR分析とは異なり、以下の動的なメカニズムをシミュレーションします。

1.  **Workload Propagation:** 離職に伴う業務負荷の連鎖的な再配分
2.  **Stress Accumulation:** 負荷集中によるキーマンの疲弊と二次離職
3.  **Survival Analysis:** 組織の「記憶（暗黙知）」を持つ初期メンバーの残存率推移
4.  **Financial Impact:** 採用遅延と生産性低下による「財務損失」と「機会損失」の試算

### 🚀 Update: Ver.4.1 Features
* **Actionable Insights:** シミュレーション結果に基づき、「いつまでに何人の採用が必要か」等の具体的アクションを自動提案する機能を実装。
* **Risk Heatmap:** 「負荷・離職・損失」が重なる危険時期（ホットスポット）の可視化。

---

## 💼 Business Applications
本モデルは、以下の経営・人事判断の支援を目的としています。

1.  **組織再編リスク評価 (Post-Merger Integration):**
    * 再編時の負荷再配分によって、どこにボトルネックが発生し、いつ崩壊するかを事前診断。
2.  **キーマン依存リスク評価 (Key-Person Risk):**
    * ハブ人材（高依存ノード）の離職が引き起こす連鎖的な影響範囲の定量化。
3.  **採用計画の最適化 (Hiring Strategy):**
    * 組織崩壊（機能不全）を回避するために必要な「補充人数」と「リードタイム」の逆算。
4.  **DXプロジェクト耐性診断:**
    * 特定個人に依存した属人化プロジェクトの生存確率評価。

---

## 🛠 Modeling Approach
本モデルは、完全な学術的ABM（エージェントベースモデル）ではなく、実務適用を重視した**構造シミュレーションモデル**として設計されています。

### 1. 構造モデル (Structural Model)
* 組織を「依存関係ネットワーク」として捉え、業務の集中度（中心性）と負荷の偏在係数（Gini）を評価します。

### 2. 負荷伝播と離職連鎖 (Cascade Failure)
* 離職発生時に、その人材が抱えていた業務負荷が隣接ノードへ再配分されるプロセスを実装。
* 負荷集中による「ストレス閾値超過」が、二次的な離職を引き起こす**非線形な崩壊プロセス**を計算します。

### 3. 準エージェントベース挙動 (Quasi-Agent Behavior)
* 個々のノード（社員）は、**「負荷」「ストレス」「スキル」「在籍期間」**のステータスを持ち、環境変化（同僚の離職や採用遅延）に反応して状態遷移するルールベースモデルを採用しています。

---

## 📊 Key Parameters

| Parameter | Meaning | Business Interpretation |
|-----------|----------|--------------------------|
| **Dependency** | 業務依存強度 | 組織の「属人化レベル」。高いほど一人の離職の影響が大。 |
| **Gini Coeff** | 負荷偏在係数 | 業務量の不平等さ。「パレートの法則（2:8）」の再現度。 |
| **Tolerance** | ストレス閾値 | 個人の耐久限界（メンタルヘルス/キャパシティ）。 |
| **Lead Time** | 補充遅延 | 採用にかかる期間（月単位）。市場流動性の指標。 |
| **Chain Factor** | 連鎖係数 | 離職が周囲に与える心理的・実務的インパクト。 |

---

## 📂 Outputs & KPIs
シミュレーションを実行すると、以下のリスク指標が出力されます。

* **Tipping Point Alert:** 組織機能が維持できなくなる「崩壊月」の特定。
* **Financial Loss:** 予算超過コスト（Excess Cost）と機会損失（Opportunity Loss）の総額。
* **Survival Curve:** Day 1 メンバーの生存率曲線（組織文化の希薄化指標）。
* **Risk Heatmap:** リスクがピークに達する時期のヒートマップ可視化。
## 📌 How to Interpret Results (For Decision Makers)

- **Tipping Point Detected**
  → 組織機能が連鎖的に低下する閾値。採用・再配置の即時実行が必要。

- **Financial Loss High**
  → 採用リードタイム短縮 or 負荷分散施策の優先順位を再評価。

- **Survival Curve Steep Decline**
  → 初期メンバー依存構造が強く、ナレッジ移転設計が必要。

---

## 💻 How to Run

```bash
# 1. Clone the repository
git clone [https://github.com/keisuke-data-lab/strategic-org-resilience.git](https://github.com/keisuke-data-lab/strategic-org-resilience.git)

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the application
streamlit run app.py
