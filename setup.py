from setuptools import setup, find_packages


setup(
    name='cryptography.vectors',
    author='PyCA',
    version='0.1',
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    namespace_packages=['cryptography'],
)
