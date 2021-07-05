import setuptools

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

install_requires = [
    "requests>=2.25",
]
tests_require = [
    "pytest>=6.2"
]

setuptools.setup(
    name="LibJciHitachi",
    version="0.0.4",
    author="Allan Lin",
    author_email="qqaatw@gmail.com",
    description="A library for controlling Jci Hitachi devices.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/qqaatw/LibJciHitachi",
    project_urls={
        "Issue Tracker": "https://github.com/qqaatw/LibJciHitachi/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    packages=setuptools.find_packages(),
    python_requires=">=3.7",
    install_requires=install_requires,
    tests_require=tests_require
)