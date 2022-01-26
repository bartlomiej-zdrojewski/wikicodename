import os
from setuptools import setup


def read(file_name):
    return open(os.path.join(os.path.dirname(__file__), file_name)).read()


setup(
    name='wikicodename',
    version='1.0.0',
    author='Bartłomiej Zdrojewski',
    author_email='bartlomiej.zdrojewski@gmail.com',
    url='https://github.com/bartlomiej-zdrojewski/wikicodename',
    description='Generate code names using lists and tables from Wikipedia '
        'articles.',
    long_description_content_type="text/markdown",
    long_description=read('README.md'),
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Utilities'
    ],
    keywords='code name codename generate generator wiki Wikipedia',
    license='MIT',
    packages=['wikicodename'],
    include_package_data=True,
    package_data={
        'wikicodename': ['defaults/config/*']
    },
    install_requires=[
        'appdirs>=1.4,<1.5',
        'colorama>=0.4,<0.5',
        'lxml>=4.7,<4.8',
        'PyYAML>=6.0,<6.1',
        'Unidecode>=1.3,<1.4'
    ],
    entry_points={
        'console_scripts': [
            'wikicodename = wikicodename.__main__:main'
        ]
    }
)
