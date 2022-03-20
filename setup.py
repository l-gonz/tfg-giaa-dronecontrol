"""A setuptools based setup module.

See:
https://packaging.python.org/guides/distributing-packages-using-setuptools/
https://github.com/pypa/sampleproject
"""

# Always prefer setuptools over distutils
from setuptools import setup, find_packages
import pathlib

here = pathlib.Path(__file__).parent.resolve()

# Get the long description from the README file
long_description = (here / 'README.md').read_text(encoding='utf-8')

setup(
    name='dronecontrol',  # Required
    version='0.2',  # Required
    description='A sample Python project',  # Optional
    long_description=long_description,  # Optional
    long_description_content_type='text/markdown',  # Optional (see note above)
    url='https://github.com/pypa/sampleproject',  # Optional
    author='Laura Gonzalez Fernandez',  # Optional
    author_email='author@example.com',  # Optional
    license='MIT',

    # For a list of valid classifiers, see https://pypi.org/classifiers/
    classifiers=[  # Optional
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        "Programming Language :: Python :: 3.10",
        'Programming Language :: Python :: 3 :: Only',
    ],

    keywords='drone computer-vision px4',  # Optional
    packages=find_packages(exclude=['test', 'Firmware']),  # Required
    python_requires='>=3.6, <4',
    #install_requires=['peppercorn'],  # Optional
    entry_points={  # Optional
        'console_scripts': [
            'dronecontrol=dronecontrol.cli:main',
        ],
    },

    project_urls={  # Optional
        'Bug Reports': 'https://github.com/pypa/sampleproject/issues',
        'Funding': 'https://donate.pypi.org',
        'Say Thanks!': 'http://saythanks.io/to/example',
        'Source': 'https://github.com/pypa/sampleproject/',
    },
)