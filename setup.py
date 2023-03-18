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
    version='1.0',  # Required
    description='A vision-based control system for PX4 drones',  # Optional
    long_description=long_description,  # Optional
    long_description_content_type='text/markdown',  # Optional (see note above)
    author='Laura Gonzalez Fernandez',  # Optional
    author_email='l.gonzalezfernan@gmail.com',  # Optional
    license='MIT',

    # For a list of valid classifiers, see https://pypi.org/classifiers/
    classifiers=[  # Optional
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        "Programming Language :: Python :: 3.10",
        'Programming Language :: Python :: 3 :: Only',
    ],

    keywords='drone computer-vision px4',  # Optional
    packages=find_packages(exclude=['test', 'Firmware']),  # Required
    python_requires='>=3.8, <4',
    entry_points={  # Optional
        'console_scripts': [
            'dronecontrol=dronecontrol.cli:main',
        ],
    },

    project_urls={  # Optional
        'Source': 'https://github.com/l-gonz/tfg-giaa-dronecontrol/',
        'Bug Reports': 'https://github.com/l-gonz/tfg-giaa-dronecontrol/issues',
        'Project Page': 'https://l-gonz.github.com/tfg-giaa-dronecontrol',
    },
)