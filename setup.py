from setuptools import setup

setup(
    name='djdt_vmprof',
    author='Patryk Zawadzki',
    author_email='patrys@room-303.com',
    description='VMProf panel for Django Debug Toolbar',
    license='MIT',
    version='0.1.0',
    url='https://github.com/patrys/djdt-vmprof',
    packages=['djdt_vmprof'],
    install_requires=['vmprof'],
    platforms=['any'],
    zip_safe=False)
