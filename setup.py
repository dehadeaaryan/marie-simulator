import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="marieSimulator",
    version="1.1.8",
    author="Aaryan Dehade",
    author_email="dehadeaaryan@gmail.com",
    description="A Python Package to simulate a MARIE architecture on any computer",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/dehadeaaryan/MarieSimulator",
    project_urls={
        "Bug Tracker": "https://github.com/dehadeaaryan/MarieSimulator/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    python_requires=">=3.10",
    extras_require={"desktop": ["PySide6==6.11.0"]},
)