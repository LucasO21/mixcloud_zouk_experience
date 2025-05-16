from setuptools import setup, find_packages, setup
from typing import List


HYPE_E_DOT = '-e .'

def get_requirements(file_path:str)->List[str]:

    requirements = []
    with open(file_path) as f:
        requirements = f.readlines()
        requirements = [req.replace('\n', '') for req in requirements]

        if HYPE_E_DOT in requirements:
            requirements.remove(HYPE_E_DOT)

    return requirements


setup(
    name             = "mixcloud_zouk_experience",
    author           = "Lucas Okwudishu",
    author_email     = "clfo2014@gmail.com",
    version          = "0.0.1",
    packages         = find_packages(),
    install_requires = get_requirements('requirements.txt')
)