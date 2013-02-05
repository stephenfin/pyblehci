from distutils.core import setup

setup(
    name='PyBLEHCI',
    version='0.1.0',
    author='Stephen Finucane',
    author_email='stephenfinucane@hotmail.com',
    packages=['pyblehci', 'pyblehci.test'],
	scripts=[],
	url='http://code.google.com/p/pyblehci/',
    license='LICENSE.txt',
    description='A combined parser and builder library for Bluetooth Low Energy HCI packets.',
    long_description=open('README.txt').read(),
    install_requires=["serial"],
	provides=['pyblehci', 'pyblehci.test'],
)