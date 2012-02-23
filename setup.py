from distutils.core import setup

setup(
    name = "microsearch",
    version = "1.0.0",
    description = "A small search library.",
    author = 'Daniel Lindsley',
    author_email = 'daniel@toastdriven.com',
    long_description=open('README.rst', 'r').read(),
    py_modules = [
        'microsearch'
    ],
    classifiers = [
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Indexing/Search'
    ],
    url = 'http://github.com/toastdriven/microsearch'
)
