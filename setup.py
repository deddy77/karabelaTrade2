from setuptools import setup, find_packages
from version_check import VERSION

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="karabelatrade",
    version=VERSION,
    author="KarabelaTrade Team",
    author_email="support@karabelatrade.com",
    description="A professional Forex trading bot with advanced analysis capabilities",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/karabelatrade/kbt2",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Financial and Insurance Industry",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Office/Business :: Financial :: Investment",
    ],
    python_requires=">=3.8",
    install_requires=[
        "MetaTrader5>=5.0.45",
        "pandas>=2.0.0",
        "numpy>=1.24.3",
        "matplotlib>=3.7.1",
        "mplfinance>=0.12.9b7",
        "pytz>=2023.3",
        "requests>=2.31.0",
        "python-dotenv>=1.0.0",
    ],
    entry_points={
        "console_scripts": [
            "karabelatrade=run_gui:main",
            "kbt-test=test_environment:main",
            "kbt-version=version_check:print_version_info",
        ],
    },
    package_data={
        "karabelatrade": ["py.typed"],
    },
    include_package_data=True,
    zip_safe=False
)
