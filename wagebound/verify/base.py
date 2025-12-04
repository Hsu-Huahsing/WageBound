from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
import itertools


@dataclass
class VerifyConfig:
    """定義這次驗證要用到哪些欄位，以及數值比對的規則。"""
    key_cols: List[str]
    numeric_cols: List[str]
    date_cols: Optional[List[str]] = None
    date_mode: Optional[int] = None  # 先保留欄位，之後若要接 stringtodate 再用
    atol: float = 0.0                # 絕對誤差容許值
    rtol: float = 0.0                # 相對誤差容許值（乘在 expected 上）


@dataclass
class VerifyIssue:
    """記錄一次驗證過程中發現的問題。"""
    level: str              # "error" / "warn"
    code: str               # 例如 "MISSING_COLUMN_EXPECTED"
    message: str
    column: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class VerifyResult:
    """驗證結果：是否通過、有哪些 issue、哪些列有數值差異。"""
    config: VerifyConfig
    issues: List[VerifyIssue]
    diff_rows: pd.DataFrame

    @property
    def ok(self) -> bool:
        """沒有 error 且沒有數值差異列時視為通過。"""
        if any(i.level == "error" for i in self.issues):
            return False
        return self.diff_rows.empty

    def summary(self) -> str:
        """給人看的摘要字串。"""
        parts = []
        if self.ok:
            parts.append("✅ 驗證通過：未發現 error，數值完全一致。")
        else:
            parts.append("⚠️ 驗證未通過：")
        if self.issues:
            err_cnt = sum(1 for i in self.issues if i.level == "error")
            warn_cnt = sum(1 for i in self.issues if i.level == "warn")
            parts.append(f"- error: {err_cnt} 則，warn: {warn_cnt} 則")
        parts.append(f"- 數值差異列數：{len(self.diff_rows)}")
        return "\n".join(parts)


def _prepare_date_columns(df: pd.DataFrame, cfg: VerifyConfig) -> pd.DataFrame:
    """
    將指定的日期欄位轉成 datetime64[ns]；目前先用 pandas.to_datetime，
    之後若要接你自己寫的 stringtodate，可以在這裡改。
    """
    if not cfg.date_cols:
        return df

    df = df.copy()
    for col in cfg.date_cols:
        if col not in df.columns:
            continue
        df[col] = pd.to_datetime(df[col], errors="coerce")
    return df


def _select_working_columns(df: pd.DataFrame, cfg: VerifyConfig) -> pd.DataFrame:
    """
    只保留這次要用到的欄位（key + numeric + date），避免 300 欄一起拖下水。
    不存在的欄位會被忽略，但會在 verify_dataframes 裡面記一條 issue。
    """
    cols = list(dict.fromkeys(
        (cfg.key_cols or [])
        + (cfg.numeric_cols or [])
        + (cfg.date_cols or [])
    ))
    existing = [c for c in cols if c in df.columns]
    return df[existing].copy()


def _record_missing_columns(df: pd.DataFrame, cfg: VerifyConfig, which: str) -> List[VerifyIssue]:
    """
    檢查 df 裡缺哪些欄位；which = "expected" / "actual"。
    """
    issues: List[VerifyIssue] = []
    need_cols = list(dict.fromkeys(
        (cfg.key_cols or [])
        + (cfg.numeric_cols or [])
        + (cfg.date_cols or [])
    ))
    for col in need_cols:
        if col not in df.columns:
            issues.append(
                VerifyIssue(
                    level="error",
                    code=f"MISSING_COLUMN_{which.upper()}",
                    column=col,
                    message=f"{which} 資料缺少必要欄位：{col}",
                )
            )
    return issues


def verify_dataframes(
    expected: pd.DataFrame,
    actual: pd.DataFrame,
    config: VerifyConfig,
) -> VerifyResult:
    """
    核心驗證函式：比較 expected vs actual。

    步驟：
        1. 檢查必要欄位是否存在（key / numeric / date）
        2. 僅保留這次要用到的欄位
        3. 日期欄位轉成 datetime
        4. 用 key_cols 做 outer join，找出：
            - 只在 expected 出現的 key（missing in actual）
            - 只在 actual 出現的 key（unexpected new rows）
        5. 對 numeric_cols 做逐列差異比對，產生 diff_rows
    """
    cfg = config
    issues: List[VerifyIssue] = []

    # 1) 欄位檢查
    issues.extend(_record_missing_columns(expected, cfg, "expected"))
    issues.extend(_record_missing_columns(actual, cfg, "actual"))

    # 真正可用的 key / numeric / date（兩邊都存在才算）
    key_cols = [c for c in cfg.key_cols if c in expected.columns and c in actual.columns]
    num_cols = [c for c in cfg.numeric_cols if c in expected.columns and c in actual.columns]
    date_cols = [c for c in (cfg.date_cols or []) if c in expected.columns and c in actual.columns]

    if not key_cols:
        issues.append(
            VerifyIssue(
                level="error",
                code="NO_COMMON_KEY_COLUMNS",
                message="expected 與 actual 沒有任何共同的 key_cols，無法比對。",
                context={"key_cols": cfg.key_cols},
            )
        )
        # 既然連 key 都沒有，直接回傳空 diff
        empty = pd.DataFrame()
        return VerifyResult(config=cfg, issues=issues, diff_rows=empty)

    # 2) 只保留需要的欄位
    exp = _select_working_columns(expected, cfg)
    act = _select_working_columns(actual, cfg)

    # 3) 日期欄位轉成 datetime
    exp = _prepare_date_columns(exp, cfg)
    act = _prepare_date_columns(act, cfg)

    # 4) 設定索引為 key_cols，方便做集合運算
    exp_idxed = exp.set_index(key_cols)
    act_idxed = act.set_index(key_cols)

    exp_keys = set(exp_idxed.index)
    act_keys = set(act_idxed.index)

    missing_in_actual = exp_keys - act_keys
    extra_in_actual = act_keys - exp_keys

    if missing_in_actual:
        sample = list(itertools.islice(missing_in_actual, 5))
        issues.append(
            VerifyIssue(
                level="error",
                code="MISSING_ROWS_IN_ACTUAL",
                message=f"actual 缺少 {len(missing_in_actual)} 組 key（只出現在 expected）。",
                context={"sample_keys": sample},
            )
        )

    if extra_in_actual:
        sample = list(itertools.islice(extra_in_actual, 5))
        issues.append(
            VerifyIssue(
                level="warn",
                code="UNEXPECTED_ROWS_IN_ACTUAL",
                message=f"actual 多出 {len(extra_in_actual)} 組 key（未出現在 expected）。",
                context={"sample_keys": sample},
            )
        )

    # 只對「兩邊都有」的 key 做數值比對
    common_keys = exp_keys & act_keys
    if not common_keys or not num_cols:
        # 沒有共同 key 或沒有數值欄位，就直接回傳（只靠 issues）
        empty = pd.DataFrame()
        return VerifyResult(config=cfg, issues=issues, diff_rows=empty)

    exp_common = exp_idxed.loc[sorted(common_keys)]
    act_common = act_idxed.loc[sorted(common_keys)]

    # 5) 比對 numeric_cols
    diff_frames = []
    for col in num_cols:
        exp_series = pd.to_numeric(exp_common[col], errors="coerce")
        act_series = pd.to_numeric(act_common[col], errors="coerce")

        diff = act_series - exp_series

        # 判斷「超出容許誤差」的列
        tol = cfg.atol + cfg.rtol * exp_series.abs()
        mask = diff.abs() > tol.fillna(cfg.atol)

        if not mask.any():
            continue

        changed = diff[mask]
        idx_df = changed.index.to_frame(index=False).reset_index(drop=True)
        col_df = pd.DataFrame({
            "column": col,
            "expected": exp_series[mask].reset_index(drop=True),
            "actual": act_series[mask].reset_index(drop=True),
            "diff": changed.reset_index(drop=True),
        })
        diff_frames.append(pd.concat([idx_df, col_df], axis=1))

    if diff_frames:
        diff_rows = pd.concat(diff_frames, ignore_index=True)
    else:
        diff_rows = pd.DataFrame(columns=key_cols + ["column", "expected", "actual", "diff"])

    return VerifyResult(config=cfg, issues=issues, diff_rows=diff_rows)


__all__ = [
    "VerifyConfig",
    "VerifyIssue",
    "VerifyResult",
    "verify_dataframes",
]
