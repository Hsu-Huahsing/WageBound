# WageBound/verify/hpm_verify_api.py

from pathlib import Path
import pandas as pd

from config.verify_config import (
    HPM_TEST_XLSX,
    HPM_API_URL,
    HPM_COMPARE_COLS,
)

from .base import load_hpm_test_cases, call_hpm_api, compare_case


def run_hpm_api_verify(
    cases_path: Path = HPM_TEST_XLSX,
    *,
    max_cases: int | None = None,
) -> pd.DataFrame:
    """主函式：跑一輪 API 驗證，回傳比對結果 DataFrame。"""
    df_cases = load_hpm_test_cases(cases_path)

    if max_cases is not None:
        df_cases = df_cases.head(max_cases)

    results = []
    for _, row in df_cases.iterrows():
        api_result = call_hpm_api(row, url=HPM_API_URL)
        comp = compare_case(row, api_result, HPM_COMPARE_COLS)
        results.append(comp)

    result_df = pd.DataFrame(results)
    return result_df


def main():
    df_result = run_hpm_api_verify()
    # 這裡你可以決定要不要寫出 Excel / CSV
    out_path = HPM_TEST_XLSX.with_name(HPM_TEST_XLSX.stem + "_api_verify_result.xlsx")
    df_result.to_excel(out_path, index=False)
    print(f"HPM API 驗證完成，輸出：{out_path}")


if __name__ == "__main__":
    main()

"""
from verify.hpm_verify_api import run_hpm_api_verify
df_chk = run_hpm_api_verify(max_cases=100)
"""