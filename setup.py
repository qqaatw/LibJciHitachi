import setuptools

from JciHitachi import __author__, __version__

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

install_requires = [
    "AWSIoTPythonSDK",
    "httpx==0.21.0",
    "paho-mqtt",
]
tests_require = [
    "pytest>=6.2",
]


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
            "Programming Language :: Python :: 3.7",
            "Programming Language :: Python :: 3.8",
            "Programming Language :: Python :: 3.9",
            "Programming Language :: Python :: 3.10",
            "License :: OSI Approved :: Apache Software License",
            "Operating System :: OS Independent",
        ],
        packages=setuptools.find_packages(include=['JciHitachi']),
        package_data={'JciHitachi': ['cert/*.pem']},
        python_requires=">=3.7",
        install_requires=install_requires,
        tests_require=tests_require,
    )
