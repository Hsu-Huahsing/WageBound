from wagebound.verify import VerifyConfig, verify_dataframes

cfg = VerifyConfig(
    key_cols=["Cust_ID", "Month"],
    numeric_cols=["Wage_Bound"],
    date_cols=["Month"],
    atol=0.0,
    rtol=0.0,
)

res = verify_dataframes(previous_df, current_df, cfg)
print(res.summary())
