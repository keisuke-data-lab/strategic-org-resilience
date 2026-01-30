# 🛡️ Strategic Organization Resilience Simulator
**人的資本・業務依存構造・離職連鎖をモデル化する組織レジリエンス診断シミュレーター**

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://strategic-org-resilience-9ejs4h2kqqpx5zdwuygri9.streamlit.app/)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Type](https://img.shields.io/badge/Type-DSS_Prototype-green)

---

## 📌 Executive Summary
**優秀な人材が一人抜けただけで、なぜ組織は急速に機能低下するのか？**

本プロジェクトは、**「人的依存構造 × 業務負荷偏在 × 離職連鎖」**を数理モデルとして統合し、組織の「隠れた脆弱性」と「崩壊の臨界点」を可視化する**意思決定支援システム（DSS）プロトタイプ**です。

静的なHR指標ではなく、動的な構造変化をシミュレーションします。

* **業務依存ネットワーク** (Network Dependency)
* **負荷再配分** (Workload Redistribution)
* **ストレス蓄積** (Stress Accumulation)
* **離職連鎖** (Attrition Chain)

---

## 💼 Business Applications
本モデルは、以下の経営・人事判断の支援を目的としています。

1.  **組織再編リスク評価:**
    * 再編時の負荷再配分によって、どこにボトルネックが発生するかを事前診断。
2.  **キーマン依存リスク評価:**
    * ハブ人材（高依存ノード）の離職が引き起こす連鎖的な影響範囲の分析。
3.  **採用計画支援:**
    * 組織崩壊を回避するために必要な「補充人数」と「タイミング」の推定。
4.  **DXプロジェクト耐性診断:**
    * 特定個人に依存した属人化プロジェクトの崩壊確率評価。

---

## 🛠 Modeling Approach
本モデルは、完全な学術的ABM（エージェントベースモデル）ではなく、実務適用を重視した**構造シミュレーションモデル**として設計されています。

### 1. 構造モデル (Structural Model)
* 組織を「依存関係ネットワーク」として表現（ノード＝人材、エッジ＝業務依存）。
* Graph理論に基づき、業務の集中度（中心性）を評価。

### 2. 負荷伝播モデル (Workload Propagation)
* 離職発生時に、その人材が抱えていた業務負荷が隣接ノードへ再配分されるプロセスを実装。
* 負荷集中による「ストレス閾値超過」が、二次的な離職を引き起こす連鎖を計算。

### 3. 準エージェントベース挙動 (Quasi-Agent Behavior)
* 個々のノード（社員）は自律思考しませんが、**「負荷」「ストレス」「スキル」のステータスを持ち、環境変化（同僚の離職）に反応して状態遷移する**ルールベースの動態モデルを採用しています。

---

## 📊 Key Parameters

| Parameter | Meaning | Business Interpretation |
|-----------|----------|--------------------------|
| **Dependency** | 業務依存強度 | 組織の「属人化レベル」 |
| **Gini Coeff** | 負荷偏在係数 | 業務量の不平等さ（特定の人への集中度） |
| **Tolerance** | ストレス閾値 | 個人の耐久限界（メンタルヘルス/キャパシティ） |
| **Lead Time** | 補充遅延 | 採用にかかる期間（月単位） |
| **Chain Factor** | 連鎖係数 | 離職が周囲に与える心理的・実務的インパクト |

---

## 📂 Outputs
シミュレーションを実行すると、以下のリスク指標が出力されます。

* **崩壊リスク指数:** 組織が機能不全に陥る確率
* **組織機能維持スコア:** 業務遂行能力の時系列推移
* **負荷ヒートマップ:** 誰に負荷が集中しているかの可視化
* **生存曲線:** シナリオ別の組織生存率（カプランマイヤー推定的アプローチ）
* **ティッピングポイント:** 連鎖崩壊が始まる「臨界点」の推定

---

## ⚠️ Limitations & Positioning
本モデルは実務上の意思決定を支援するプロトタイプであり、以下の前提と制約があります。

* **Limitations:**
    * 心理的要因（モチベーション等）は、代理指標で近似しています。
    * 実データ（人事DB）とのAPI接続は未実装です。
    * 企業ごとのパラメータチューニング（キャリブレーション）を前提としています。

* **Positioning:**
    * 本プロジェクトは、経営・人的資本課題を構造モデルとして設計し、**Pythonを用いてDSSプロトタイプとして実装できる能力の実証**を目的としています。単なるデータ分析ではなく、「動く意思決定モデル」の提示を目指しました。

---

## 💻 How to Run

```bash
git clone [https://github.com/keisuke-data-lab/strategic-org-resilience.git](https://github.com/keisuke-data-lab/strategic-org-resilience.git)
pip install -r requirements.txt
streamlit run app.py
