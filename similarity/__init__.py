# similarity/__init__.py

from .engine import run_similarity

__all__ = ["run_similarity"]



# from similarity import run_similarity
#
# result = run_similarity(
#     df_ref=dev_df,        # 參考樣本（例如舊制、全體母體）
#     df_new=oos_df,        # 新樣本（例如新制、子樣本）
#     feature_cols=["age", "income", "dti"],   # 想看的欄位
# )
# print(result)

"""
from similarity import run_similarity

summary = run_similarity(
    df_ref=dev_df,
    df_new=oos_df,
    feature_cols=["Age", "Income", "LTV", "DBR"],
)

print(summary.head(10))

"""

"""
summary = run_similarity(
    df_ref=population_df,
    df_new=sample_df,
    # feature_cols=None → 會自動抓共同欄位，排除一些明顯 ID 欄
)


"""