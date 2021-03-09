from setuptools import setup

setup(name='omapper',
      version='0.0.1-alpha.1',
      description='Object Mapper',
      long_description='Object Mapper',
      classifiers=[
            'Development Status :: 1 - Planning',
            'License :: OSI Approved :: MIT License',
            'Programming Language :: Python :: 3.8',
            'Topic :: Software Development :: Libraries :: Python Modules',
      ],
      url='http://github.com/eugenma/omapper',
      author='Eugen Massini',
      author_email='eugen@massini.de',
      license='MIT',
      tests_require=['pytest', ],
      packages=['omapper'],
      zip_safe=False)
