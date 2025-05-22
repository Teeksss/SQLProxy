from setuptools import setup, find_packages

setup(
    name="sqlproxy",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "numpy>=1.21.0",
        "pandas>=1.3.0",
        "scipy>=1.7.0",
        "sqlalchemy>=1.4.0",
        "redis>=4.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=3.0.0",
            "pytest-asyncio>=0.18.0",
            "pytest-mock>=3.7.0",
            "black>=22.3.0",
            "flake8>=4.0.1",
            "mypy>=0.910",
        ]
    },
    python_requires=">=3.7",
)