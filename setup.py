from setuptools import find_packages, setup

setup(
    name="artificial-u",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "alembic>=1.12.0",
        "anthropic>=0.18.1",
        "click>=8.1.7",
        "elevenlabs>=0.2.24",
        "pydantic>=2.4.0",
        "python-dotenv>=1.0.0",
        "rich>=13.6.0",
        "sqlalchemy>=2.0.23",
    ],
    extras_require={
        "dev": [
            "ollama>=0.4.0",
            "pytest>=7.0.0",
        ],
        "test": [
            "ollama>=0.4.0",
            "pytest>=7.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "artificial-u=cli:cli",
        ],
    },
)
