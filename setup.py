from setuptools import setup


def read(name):
    with open(name) as f:
        return f.read()


setup(name='async-timeout',
      version='2.0.0',
      description=("Timeout context manager for asyncio programs"),
      long_description='\n\n'.join([read('README.rst'),
                                    read('CHANGES.rst')]),
      classifiers=[
          'License :: OSI Approved :: Apache Software License',
          'Intended Audience :: Developers',
          'Programming Language :: Python',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.4',
          'Programming Language :: Python :: 3.5',
          'Programming Language :: Python :: 3.6',
          'Topic :: Internet :: WWW/HTTP',
          'Framework :: AsyncIO',
      ],
      author='Andrew Svetlov',
      author_email='andrew.svetlov@gmail.com',
      url='https://github.com/aio-libs/async_timeout/',
      license='Apache 2',
      packages=['async_timeout'],
      include_package_data=False)
