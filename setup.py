from setuptools import setup, find_packages

setup(
    name="sqlproxy",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.68.0",
        "uvicorn>=0.15.0",
        "sqlalchemy>=1.4.0",
        "psycopg2-binary>=2.9.0",
        "redis>=4.0.0",
        "pydantic>=1.8.0",
        "numpy>=1.21.0",
        "pandas>=1.3.0",
        "scipy>=1.7.0",
        "locust>=2.8.0",
    ],
    extras_require={
        'dev': [
            'pytest>=7.0.0',
            'pytest-asyncio>=0.18.0',
            'pytest-cov>=2.12.0',
            'pytest-mock>=3.6.0',
            'pytest-benchmark>=3.4.0',
            'memory-profiler>=0.58.0',
            'psutil>=5.8.0',
        ]
    }
)