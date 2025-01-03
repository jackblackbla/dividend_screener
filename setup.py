from setuptools import setup, find_packages

setup(
    name="dividend_screener",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "uvicorn",
        "sqlalchemy",
        "mysqlclient",
        "pydantic",
        "python-dotenv",
    ],
)