# WageBound/verify/__init__.py

"""
WageBound.verify

統一對外暴露的「驗證工具」API。

主要功能：
- HPM API 驗證（import vs API 結果比對）
- 驗證結果 log 彙整
"""

from .base import (
    VerifyCaseConfig,
    load_hpm_cases,
    call_hpm_api_for_cases,
    compare_import_vs_api,
    save_verify_output,
)

from .hpm_verify_api import (
    run_hpm_api_verify,   # 高階封裝，一次做到「讀檔 → 打 API → 比對 → 輸出」
)

from .multilog import (
    dict_to_df,    # 依你原本命名，如果有
    merge_logs,    # 假設你有類似功能，或之後改名
)

__all__ = [
    "VerifyCaseConfig",
    "load_hpm_cases",
    "call_hpm_api_for_cases",
    "compare_import_vs_api",
    "save_verify_output",
    "run_hpm_api_verify",
    "dict_to_df",
    "merge_logs",
]
# WageBound/verify/__init__.py

from .runner import verify_dataframe  # 新增這一行
