from setuptools import setup, find_packages

setup(
    name='lts_scan',
    version='0.1.2',
    packages=find_packages(),
    install_requires=[
        'aiohttp',
    ],
    entry_points={
        'console_scripts': [
            'lts-scan = lts_scan.scanner:main',
        ],
    },
    author='Alexandre Meline',
    author_email='alexandre.meline.dev@gmail.com',
    description='Lightweight TLS Scanner using SSL Labs API',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/alexandre-meline/LTS_scan',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.7',
)
