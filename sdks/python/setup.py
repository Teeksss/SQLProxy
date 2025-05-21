"""
Setup script for SQL Proxy Python SDK
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="sqlproxy",
    version="1.0.0",
    author="SQL Proxy Team",
    author_email="admin@example.com",
    description="A Python SDK for interacting with SQL Proxy API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/example/sqlproxy-sdk-python",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    install_requires=[
        "requests>=2.25.0",
        "urllib3>=1.26.0"
    ],
)