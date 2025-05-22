from setuptools import setup, find_packages

setup(
    name="sqlproxy",
    version="0.1.0",
    packages=find_packages(include=['sqlproxy', 'sqlproxy.*']),
    install_requires=[
        "fastapi>=0.100.0",
        "uvicorn>=0.22.0",
        "sqlalchemy>=2.0.18",
        "psycopg2-binary>=2.9.6",
        "redis>=4.6.0",
        "pydantic>=2.0.2",
        "numpy>=1.24.3",
        "pandas>=2.0.3",
        "scipy>=1.10.1"
    ],
    extras_require={
        'dev': [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.1",
            "pytest-cov>=4.1.0",
            "pytest-mock>=3.11.1",
            "pytest-xdist>=3.3.1",
            "black>=23.3.0",
            "flake8>=6.0.0",
            "mypy>=1.4.1",
            "pre-commit>=3.3.3"
        ]
    }
)