#!/usr/bin/env python

from setuptools import setup

setup(name='Setup Grafana',
      version='1.0',
      description='Tool for installing all datasources and importing all dashboards neccessary for JMeter and InspectIT',
      author='Thomas Zwickl',
      author_email='thomas.zwickl@novatec-gmbh.de',
      install_requires=[
          'GitPython'
      ]
     )