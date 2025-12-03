from setuptools import find_packages, setup
# 因為windows的environ參數有可能和mac不一樣，所以用environ就會造成windows出錯，因此盡量不用
# from os import environ

setup(
    name='WageBound',  # 应用名
    author='Steven',
    license='BSD',
    version='0.0.3',  # 版本号
    packages=find_packages(),  # 包括在安装包内的Python包
    # include_package_data=True,  # 启用清单文件MANIFEST.in,包含数据文件
    exclude_package_data={'': ['.gitignore']},  # 上面的代码会将所有”.gitignore”文件排除在包外。如果上述exclude_package_date对象属性不为空，比如{'myapp':['.gitignore']}，就表明只排除”myapp”包下的所有”.gitignore”文件。
    # {'docs': ['']},
    # install_requires=[  # 自动安装依赖
    #     # 'Flask>=0.10',
    # ],
)
