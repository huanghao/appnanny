from setuptools import setup, find_packages

setup(
    name="appnanny",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "flask",
        "requests",
        "apscheduler",
        "streamlit",
    ],
    python_requires=">=3.10",
)
