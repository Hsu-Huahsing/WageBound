# WageBound
WageBound/
├── README.md
├── ARCHITECTURE.md      ← 建議放在這裡
├── __init__.py
├── user_lab.py          ← 測試／實驗用腳本 (sandbox)
│
├── config/
│   ├── __init__.py
│   ├── config.py        ← 路徑與欄位命名設定（核心）
│   └── verify_config.py ← 驗證規則宣告（草稿）
│
├── verify/
│   ├── __init__.py
│   ├── base.py          ← 驗證引擎骨架（TODO: 實作）
│   └── runner.py        ← 驗證流程 orchestrator（TODO: 實作）
│
├── similarity/
│   ├── __init__.py
│   └── similarity_engine.py  ← 相似度分析骨架（TODO: 實作）
│
├── landsplit/
│   ├── __init__.py
│   └── landsplit_engine.py   ← 土建拆分腳本（舊邏輯移植，未模組化）
│
└── utils/
    ├── __init__.py
    ├── addr_to_community.py  ← 地址 → 里/社區 對應工具（舊專案程式）
    └── base_utils.py         ← 一些共用的 utility 函式（目前內容有限）
