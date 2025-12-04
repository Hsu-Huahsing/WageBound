# -*- coding: utf-8 -*-
"""
verify.runner
=============

用途（這個檔案負責的事情）：
    - 統一管理「要跑哪些驗證」、「怎麼一次跑完」。
    - 不自己寫任何業務邏輯，只是把 verify 子模組裡的檢查程式跑一輪。
    - 回傳一個整理好的 pd.DataFrame，方便後續寫入 Excel / DB / 報表。

設計重點：
    1. 完全走 import / 函式呼叫，不使用 cmd 參數。
    2. 不直接讀檔案、不連 DB，只吃呼叫端丟進來的 df。
    3. 檢查邏輯集中在各自的 script 裡（例如: missing_value.py、range_check.py...），
       每個檢查 script 自己把「檢查函式或類別」註冊到 base.VERIFIER_REGISTRY。
    4. runner 只需要知道 base.VERIFIER_REGISTRY，就能跑所有已註冊的檢查。

預期 base.py 至少要提供：
    - VERIFIER_REGISTRY: dict[str, Any]
      key   = 檢查名稱（字串）
      value = 檢查物件、檢查類別，或簡單的檢查函式

    每個檢查的介面建議（但不強制）：
        1) 類別型：
            class XXXVerifier:
                name = "xxx"  # 可選，沒有的話 runner 會用 registry key 當名稱

                def run(self, df: pd.DataFrame, context: dict | None = None) -> dict:
                    return {
                        "name": self.name,
                        "passed": True/False,
                        "level": "info/warn/error",
                        "message": "...",
                        "details": {...}  # 可選
                    }

        2) 函式型：
            def check_xxx(df: pd.DataFrame, context: dict | None = None) -> dict:
                return {... 同上 ...}

    runner 只要求「最後一定要回傳 dict 或類似物件」，會幫你轉成 DataFrame。
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

import inspect

import pandas as pd

from . import base  # 只依賴 base.VERIFIER_REGISTRY


# ---------------------------------------------------------------------------
# 工具函式：存取 registry
# ---------------------------------------------------------------------------

def _get_registry() -> Dict[str, Any]:
    """
    從 base.py 取得 VERIFIER_REGISTRY。

    預期在 base.py 裡面有類似寫法：

        VERIFIER_REGISTRY: dict[str, Any] = {}

        def register(name: str):
            def deco(obj):
                VERIFIER_REGISTRY[name] = obj
                return obj
            return deco

    如果沒有這個變數，這邊會直接 raise，強迫你先把 base.py 改好。
    """
    registry = getattr(base, "VERIFIER_REGISTRY", None)
    if registry is None:
        raise RuntimeError(
            "base.py 必須定義 VERIFIER_REGISTRY: dict[str, Any]，"
            "用來註冊各種驗證程式。"
        )
    # 複製一份，避免外面不小心修改到 base 裡的原始 dict
    return dict(registry)


def list_available_checks() -> List[str]:
    """
    回傳目前 registry 裡所有可用的檢查名稱（已排序）。
    """
    reg = _get_registry()
    return sorted(reg.keys())


# ---------------------------------------------------------------------------
# 工具函式：根據 include / exclude 篩選要跑哪些檢查
# ---------------------------------------------------------------------------

def _filter_registry(
    registry: Dict[str, Any],
    include: Optional[Sequence[str]] = None,
    exclude: Optional[Sequence[str]] = None,
) -> Dict[str, Any]:
    """
    根據 include / exclude 名單，篩選出要執行的檢查。

    include:
        - None 或空：表示「全部都要」
        - 有內容：只保留在 include 清單裡的名稱
    exclude:
        - 無論如何，最後都會把 exclude 名單裡的名稱剔除掉
    """
    selected = dict(registry)

    if include:
        include_set = set(include)
        selected = {k: v for k, v in selected.items() if k in include_set}

    if exclude:
        exclude_set = set(exclude)
        selected = {k: v for k, v in selected.items() if k not in exclude_set}

    return selected


# ---------------------------------------------------------------------------
# 工具函式：執行單一檢查 + 統一把結果轉成 dict
# ---------------------------------------------------------------------------

def _instantiate_checker(obj: Any) -> Any:
    """
    根據 registry 裡的 value 建立檢查物件：

    - 如果是 class：先實例化（沒有參數的建構子）
    - 如果是 function：直接回傳（當作函式呼叫）
    - 如果是其他物件：直接回傳（假設它本身就有 run(...) 或 __call__）
    """
    if inspect.isclass(obj):
        # 假設建構子不需要額外參數
        return obj()
    return obj


def _run_one_checker(
    name: str,
    checker: Any,
    df: pd.DataFrame,
    context: Optional[Mapping[str, Any]] = None,
    strict: bool = False,
) -> Dict[str, Any]:
    """
    執行一個檢查，並把結果統一轉成 dict。

    支援的型態：
        - 類別：有 run(df, context) 方法
        - 函式：check(df, context) → dict / 其他
        - 物件：有 run(...) 或 __call__(...)
    """
    ctx = dict(context) if context else {}

    try:
        # 判斷用哪種介面呼叫
        if hasattr(checker, "run") and callable(getattr(checker, "run")):
            raw_result = checker.run(df=df, context=ctx)
        elif callable(checker):
            # 可能是單純的函式，也可能是實作了 __call__ 的物件
            # 優先嘗試帶 context，如果檢查函式只收一個參數就讓 Python 自己丟 TypeError
            try:
                raw_result = checker(df=df, context=ctx)
            except TypeError:
                # 退而求其次：只傳 df
                raw_result = checker(df)
        else:
            raise TypeError(
                f"檢查物件 {checker!r} 不可呼叫，請確認是否實作 run(...) 或 __call__(...)"
            )

    except Exception as e:
        # 嚴格模式：直接往外拋錯，不吃掉
        if strict:
            raise

        # 非嚴格：把錯誤包裝成一筆「檢查失敗」的結果
        return {
            "name": name,
            "passed": False,
            "level": "error",
            "message": f"驗證過程發生例外：{type(e).__name__}: {e}",
            "details": None,
        }

    # 統一轉成 dict
    if isinstance(raw_result, dict):
        result = dict(raw_result)
    else:
        # 嘗試用物件屬性展開（例如 dataclass）
        # 只取不以 "_" 開頭的 public 屬性
        attrs = {
            k: getattr(raw_result, k)
            for k in dir(raw_result)
            if not k.startswith("_") and not callable(getattr(raw_result, k))
        }
        result = dict(attrs)

    # 確保有 name / passed 欄位
    result.setdefault("name", name)

    if "passed" not in result:
        # 如果沒有明確 passed，就用最保守的 false
        result["passed"] = False

    # level / message / details 若缺，就補上預設
    result.setdefault("level", "info")
    result.setdefault("message", "")
    result.setdefault("details", None)

    return result


# ---------------------------------------------------------------------------
# 對外主函式：一次跑完所有（或指定）驗證
# ---------------------------------------------------------------------------

def run_verifications(
    df: pd.DataFrame,
    *,
    include: Optional[Sequence[str]] = None,
    exclude: Optional[Sequence[str]] = None,
    context: Optional[Mapping[str, Any]] = None,
    strict: bool = False,
) -> pd.DataFrame:
    """
    執行一批驗證，並回傳結果 DataFrame。

    參數
    ----
    df :
        要被檢查的主資料表（通常是你 wagebound 的某張明細或彙總表）。
    include :
        要執行的檢查名稱清單（對應 VERIFIER_REGISTRY 的 key）。
        - None 或空：表示不特別指定 → 全部檢查都跑。
        - 有內容：只跑這裡列出的名稱。
    exclude :
        無論如何，都會把這裡列出的檢查名稱排除掉。
    context :
        額外的上下文資訊（例如：專案代號、跑的日期、門檻設定），
        會原封不動傳給每個檢查的 run(...) 或函式。
    strict :
        - True ：任何一個檢查丟出例外，直接讓例外往外拋；不吃掉。
        - False：把例外包裝成一筆「檢查失敗」的結果，流程繼續跑完其他檢查。

    回傳
    ----
    pd.DataFrame：
        每一列是一個檢查的結果，至少會有欄位：
            - name    : 檢查名稱
            - passed  : True / False
            - level   : "info" / "warn" / "error" 等級（由檢查程式自己決定）
            - message : 人類可讀的摘要
            - details : 任意結構的補充資訊（通常是 dict 或 None）
    """
    registry = _get_registry()
    selected = _filter_registry(registry, include=include, exclude=exclude)

    rows: List[Dict[str, Any]] = []

    for name, obj in selected.items():
        checker = _instantiate_checker(obj)
        res_dict = _run_one_checker(
            name=name,
            checker=checker,
            df=df,
            context=context,
            strict=strict,
        )
        rows.append(res_dict)

    if not rows:
        # 沒有任何檢查被選中，就回傳一張空表，但保留欄位結構
        return pd.DataFrame(columns=["name", "passed", "level", "message", "details"])

    # DataFrame 形式，方便日後寫入 Excel / DB
    result_df = pd.DataFrame(rows)

    # 稍微調整欄位順序，把常用的放前面
    front = ["name", "passed", "level", "message"]
    cols = [c for c in front if c in result_df.columns] + [
        c for c in result_df.columns if c not in front
    ]
    result_df = result_df[cols]

    return result_df


# ---------------------------------------------------------------------------
# 簡單範例（給你在 Notebook / .py 測試用，不會用到 cmd）
# ---------------------------------------------------------------------------

def demo() -> pd.DataFrame:
    """
    簡易示範：建立一個假資料 df，跑目前所有已註冊的驗證。

    實務上你不一定會用到這個函式，只是方便你確認架構有沒有接好。
    """
    demo_df = pd.DataFrame(
        {
            "Customer_ID": [1, 2, 3],
            "Wage": [50000, 60000, None],
            "Area": ["A1", "A2", "A2"],
        }
    )

    return run_verifications(demo_df)


if __name__ == "__main__":
    # 這段只在你直接執行 runner.py 時會跑到；
    # 你平常在別的 .py 裡 import 是不會觸發的。
    df_demo = demo()
    # 這裡只是一個輕量 smoke test，你平常可以忽略。
    print(df_demo)


"""
實務上你要怎麼用

在你的「真正業務程式」裡（例如 app/main.py 或某個 notebook）：

import pandas as pd

from wagebound.verify.runner import run_verifications
from wagebound.verify import some_check_module  # 確保檢查 script 被 import，裡面的 register 有執行

# 1. 準備好 df
df = ...  # 你要驗證的主 DataFrame

# 2. 跑全部註冊好的驗證
result_df = run_verifications(df)

# 3. 只跑其中幾個（假設 base.VERIFIER_REGISTRY 裡有這些 key）
result_df2 = run_verifications(df, include=["missing_value", "range_check"])

# 4. 帶一些 context（例如專案代碼、日期、門檻）
ctx = {"project_id": "2025Q4_WAGE", "run_date": "2025-10-06"}
result_df3 = run_verifications(df, context=ctx)


如果你願意，把現在的 verify/base.py 貼上來，我可以再幫你把 runner.py 的介面跟 base 完全對齊（例如：直接吃你現在的 register()、BaseVerifier、VerifyResult 結構），但就算不貼，以上這個 runner.py 也可以當作標準版，往回調整 base 讓它符合這個模式。

"""