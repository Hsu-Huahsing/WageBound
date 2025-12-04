import pandas as pd
from similarity.service import run_similarity_search

df = pd.read_pickle("your_big_table.pkl")

result = run_similarity_search(
    df=df,
    target_idx="A12345",               # 或者 123, 視你的 index 而定
    feature_cols=["縣市", "屋齡", "樓高", "總價", "建物型態"],
    date_cols=["核准日"],             # 有就填，沒有就留空
    date_mode=4,                       # 用你習慣的 stringtodate 模式
    top_k=30,
)

print(result.head())
