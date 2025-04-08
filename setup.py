from setuptools import setup, find_packages

setup(
    name="artificial-u",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "elevenlabs>=0.2.24",
        "pydantic>=2.4.0",
        "python-dotenv>=1.0.0",
        "click>=8.1.7",
        "rich>=13.6.0",
        "sqlalchemy>=2.0.23",
        "anthropic>=0.18.1",
    ],
    entry_points={
        "console_scripts": [
            "artificial-u=artificial_u.cli.app:cli",
        ],
    },
)
