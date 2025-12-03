# -*- coding: utf-8 -*-

from wagebound.verify.hpm_verify_api import run_hpm_api_verify
# 如果你的 package 名稱是 WageBound 或 verify 在同一層，
# 就改成：
# from verify.hpm_verify_api import run_hpm_api_verify

def main():
    # 這裡之後要多 case，你可以包成：
    # run_hpm_api_verify_case1()
    # run_hpm_api_verify_case2()
    run_hpm_api_verify()

if __name__ == "__main__":
    main()
