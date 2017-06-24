from setuptools import setup

setup(
    name='github-explorer',
    version='0.1',
    packages=['github_explorer'],
    url='https://github.com/michal-raska/github_explorer',
    license='MIT',
    author='Michal Raska',
    author_email='michal.raska@gmail.com',
    description='',
    install_requires=['pygithub', 'termcolor', 'python-dateutil']
)
