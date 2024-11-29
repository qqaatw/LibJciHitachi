import setuptools

from JciHitachi import __author__, __version__

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

with open("requirements.txt", "r", encoding="utf-8") as f:
    install_requires = f.read().split("\n")

with open("requirements_test.txt", "r", encoding="utf-8") as f:
    tests_require = f.read().split("\n")


if __name__ == "__main__":
    setuptools.setup(
        name="LibJciHitachi",
        version=__version__,
        author=__author__,
        author_email="qqaatw@gmail.com",
        description="A library for controlling Jci Hitachi devices.",
        long_description=long_description,
        long_description_content_type="text/markdown",
        url="https://github.com/qqaatw/LibJciHitachi",
        project_urls={
            "Issue Tracker": "https://github.com/qqaatw/LibJciHitachi/issues",
            "Documentation": "https://libjcihitachi.readthedocs.io/en/latest/",
        },
        classifiers=[
            "Programming Language :: Python :: 3.10",
            "Programming Language :: Python :: 3.11",
            "Programming Language :: Python :: 3.12",
            "Programming Language :: Python :: 3.13",
            "License :: OSI Approved :: Apache Software License",
            "Operating System :: OS Independent",
        ],
        packages=setuptools.find_packages(include=["JciHitachi"]),
        package_data={"JciHitachi": ["cert/*.pem"]},
        python_requires=">=3.10",
        install_requires=install_requires,
    )
