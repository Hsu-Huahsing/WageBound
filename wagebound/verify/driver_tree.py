from verify.runner import load_and_filter_data  # 假設你 verify 這樣設計
from similarity import run_similarity

df_ref, df_new = load_and_filter_data(config_path="config/xxx.yaml")

summary = run_similarity(
    df_ref=df_ref,
    df_new=df_new,
    feature_cols=[
        "Region_Level", "Customer_Level",
        "Loan_Term", "Grace_Period",
        "DBR", "ATD",
    ],
)

summary.to_excel("similarity_result.xlsx", index=False)
