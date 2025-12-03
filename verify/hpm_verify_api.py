# -*- coding: utf-8 -*-
"""
verify/hpm_verify_api.py

從 Excel 載入 HPM 測試資料 → 呼叫 HPM API → 比對 → 輸出結果。
"""

from __future__ import annotations

from typing import List

from verify.base import (
    VerifyCaseConfig,
    load_hpm_cases,
    call_hpm_api_for_cases,
    compare_import_vs_api,
    save_verify_output,
)
from config.verify_config import HPM_COMPARE_COLS


def build_default_case() -> VerifyCaseConfig:
    """
    定義一個預設驗證情境：
      - sheet_name: 你的測試分頁
      - key_cols  : 對齊匯入 vs API 的 key（自己決定）
      - compare_cols: 用 verify_config.HPM_COMPARE_COLS
      - date_cols : 若匯入有日期欄，就填在這裡
      - use_cols  : 實務上只想拿來分析的欄位
    """
    key_cols: List[str] = ["客戶ID", "案件編號"]  # TODO：換成你實際的 key 欄位

    # ⚠️ use_cols 這裡示意：key + 比對欄位
    use_cols: List[str] = key_cols + list(HPM_COMPARE_COLS.keys())

    cfg = VerifyCaseConfig(
        name="hpm_api_default",
        sheet_name="HPM測試案例",   # TODO：你的 Excel 分頁名稱
        key_cols=key_cols,
        compare_cols=HPM_COMPARE_COLS,
        date_cols=["申請日"],        # 若沒有就改成 [] 或 None
        use_cols=use_cols,
    )
    return cfg


def run_hpm_api_verify() -> None:
    cfg = build_default_case()

    # 1. 載入測試資料（含日期轉換 & 欄位篩選）
    df_imp = load_hpm_cases(cfg)

    # 2. 呼叫 API 拿結果
    df_api = call_hpm_api_for_cases(df_imp)

    # 3. 比對匯入 vs API
    df_merged, df_diff = compare_import_vs_api(
        df_import=df_imp,
        df_api=df_api,
        cfg=cfg,
    )

    # 4. 輸出差異與完整紀錄
    save_verify_output(cfg, df_merged, df_diff)


if __name__ == "__main__":
    run_hpm_api_verify()
