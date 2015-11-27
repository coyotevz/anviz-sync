
from setuptools import setup
from anviz_sync import __version__

with open("README.rst") as readme:
    long_description = str(readme.read())

setup(
    name='anviz-sync',
    version=__version__,
    author='Augusto Roccasalva',
    author_email='augusto@rioplomo.com.ar',
    url='https://github.com/coyotevz/anviz-sync',
    description='Sync Anviz Time & Attendance data with specified database',
    long_description=long_description,
    download_url='https://github.com/coyotevz/anviz-sync',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intented Audience :: End Users/Desktop',
        'Intented Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Operating System :: POSIX ',
        'Operating System :: POSIX :: BSD',
        'Operating System :: POSIX :: Linux',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Topic :: Office/Business',
    ],
    keywords="anviz a300 time attendance",
    platforms='any',
    license='BSD',
    packages=['anviz_sync'],
    install_requires=[
        'SQLAlchemy>=0.9.8',
        'configparser>=3.3.0',
    ],
    entry_points={
        'console_scripts': [
            'anviz-sync = anviz_sync.sync:main'
        ],
    },
)
