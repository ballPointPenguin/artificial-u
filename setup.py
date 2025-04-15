from setuptools import find_packages, setup

setup(
    name="artificial-u",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "alembic>=1.12.0",
        "anthropic>=0.18.1",
        "boto3>=1.37.34",
        "click>=8.1.7",
        "elevenlabs>=0.2.24",
        "fastapi>=0.115.0",
        "google-genai>=1.10.0",
        "httpx>=0.28.0",
        "ollama>=0.4.7",
        "openai>=1.74.0",
        "psycopg2-binary>=2.9.0",
        "pydantic-settings>=2.8.0",
        "pydantic>=2.11.3",
        "python-dotenv>=1.0.0",
        "python-multipart>=0.0.6",
        "rich>=13.6.0",
        "sqlalchemy>=2.0.23",
        "uvicorn[standard]>=0.34.1",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
        ],
        "test": [
            "pytest>=7.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "artificial-u=cli:cli",
        ],
    },
)
