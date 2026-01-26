# Strategic Organizational Resilience Simulation
**戦略的組織レジリエンス構築：人材トリアージとROI分析**

## 📌 Project Overview
2030年の労働供給不足を見据え、既存人材の離職が引き起こす「組織の機能不全（負の連鎖）」をPythonによるモンテカルロ・シミュレーションで定量化。
単純な「採用難」のリスクだけでなく、既存社員（特にハイパフォーマー）への負荷集中による連鎖的な離職リスクをモデル化しました。

「直接的な現金流出」だけでなく「機会損失」を含めたリスク総額を算出し、ROI 217% の投資対効果を持つ「人材トリアージ戦略」を立案しています。

---

## 📄 Full Report (Detailed Analysis)
**詳細な分析ロジック、数理モデルの解説、およびトリアージ戦略の提言書**
> **[👉 Download PDF: 戦略的組織レジリエンス構築レポート (Ver.4)](report/Strategic_Org_Resilience_Report.pdf)**

---

## 📊 Key Simulation Results

### 1. 負の連鎖シミュレーション (Negative Chain "Death Spiral")
**【New Analysis】**
離職の連鎖が「ハイパフォーマーへの負荷集中（残業増）」を引き起こし、組織が機能不全に陥るプロセスを可視化。
24ヶ月で約11億円の直接財務損失（採用費＋人件費増）が発生するリスクを算出しました。
![Negative Chain Simulation](negative_chain_simulation.png)

### 2. リスクヒートマップ (Risk Heatmap)
部署・職種ごとの離職リスクを可視化し、優先対策エリアを特定。
![Risk Heatmap](report/risk_heatmap.png)

### 3. 感度分析 (Sensitivity Analysis)
採用リードタイム短縮による財務インパクトの改善効果を試算。
![Sensitivity Analysis](report/sensitivity_analysis.png)

---

## 🛠 Tech Stack & Source Code

- **Language**: Python 3.12
- **Libraries**: Pandas, NumPy, Matplotlib, Seaborn
- **Methodology**: Agent-Based Monte Carlo Simulation

### 📂 Source Code
- **[simulation_negative_chain.py](python/simulation_negative_chain.py)**
  負の連鎖（デススパイラル）と財務損失を計算するシミュレーションのソースコード。

  ---

## 🚀 Web Application (Simulator Ver.2.0)

本レポートの数理モデルをブラウザ上で体験できるインタラクティブ・シミュレーターを実装しました。
Ver.1.0（単なる人数計算）とは異なり、**「有効組織能力 (Effective Capacity)」**と**「不可逆性 (Irreversibility)」**を組み込んだ研究用モデルです。

### Key Logic (Ver.2.0):
1. **不可逆性 (Irreversibility)**:
   - 「退職者を即座に補充しても、組織能力は回復しない」という現実を再現。
   - 新規採用者の戦力化期間 (Ramp-up Period) を変数化し、生産性の遅れ（Learning Curve）を考慮。
2. **非線形な燃え尽き (Non-linear Burnout)**:
   - 業務負荷が閾値を超えると、離職確率が「指数関数的」に上昇する数理モデルを実装。
   - 組織が一気に崩壊する「ティッピング・ポイント」を予見可能。

### 🛠 Usage
```bash
# Run locally
pip install -r requirements.txt
streamlit run app.py