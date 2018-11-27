from setuptools import setup

packages = ['pysenate']
install_requires = ['beautifulsoup4>=4.6.0']

if __name__ == "__main__":
    setup(
        name="pysenate",
        author="Mauricio Tec",
        version="0.0.1",
        author_email="mauriciogtec@utexas.edu",
        packages=packages,
        install_requires=install_requires
    )