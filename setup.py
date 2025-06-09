from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="lapis-llmt-spyder",
    version="0.1.0",
    author="Lapis Team",
    author_email="team@lapis-spider.com",
    description="Web crawler system with AI-powered content processing",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/lapis/llmt-spyder",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Internet :: WWW/HTTP :: Indexing/Search",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.12",
    install_requires=[
        "fastapi>=0.109.0",
        "uvicorn[standard]>=0.27.0",
        "sqlalchemy>=2.0.25",
        "celery[redis]>=5.3.4",
        "pymongo>=4.6.1",
        "google-generativeai>=0.3.2",
    ],
    entry_points={
        "console_scripts": [
            "lapis-spider=src.main:cli",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)