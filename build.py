import os
import subprocess

from pybuilder.utils import assert_can_execute
from pybuilder.core import use_plugin, init, Author, task

use_plugin('python.core')
use_plugin('python.install_dependencies')
use_plugin('python.distutils')
use_plugin('copy_resources')
use_plugin('filter_resources')

use_plugin('python.pycharm')

use_plugin('python.unittest')
use_plugin('python.coverage')
use_plugin('python.flake8')
use_plugin('python.frosted')

use_plugin('pypi:pybuilder_header_plugin')


authors = [Author('Maximilien Riehl', 'max@riehl.io')]

description = """isphere - interactive shell for vsphere"""

name = 'isphere'
license = 'WTFPL'
summary = 'interactive shell for vsphere'
url = 'https://github.com/mriehl/isphere'
version = '0.0.1'

default_task = ['clean', 'analyze', 'publish']


@init
def set_properties(project):
    project.depends_on('pyvmomi')
    project.depends_on('docopt')
    project.depends_on('cmd2')
    project.build_depends_on('mock')

    project.set_property('verbose', True)

    project.set_property('flake8_verbose_output', True)
    project.set_property('flake8_include_test_sources', True)
    project.set_property('flake8_ignore', 'E501,E731')
    project.set_property('flake8_break_build', True)

    FROSTED_BARE_EXCEPT_WARNING = 'W101'
    project.set_property('frosted_ignore', [FROSTED_BARE_EXCEPT_WARNING])
    project.set_property('frosted_include_test_sources', True)

    project.set_property('coverage_threshold_warn', 50)
    project.set_property('coverage_break_build', False)
    project.set_property('coverage_exceptions', ['thirdparty.tasks'])

    project.set_property('copy_resources_target', '$dir_dist')
    project.get_property('copy_resources_glob').extend(['setup.cfg'])
    project.set_property('filter_resources_glob', ['**/cli.py'])

    project.set_property('dir_dist_scripts', 'scripts')

    project.set_property('distutils_classifiers', [
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Programming Language :: Python',
        'Topic :: System :: Systems Administration'
    ])

    project.set_property('pybuilder_header_plugin_break_build', False)  # embedded 3rd-party sources
    project.set_property('pybuilder_header_plugin_expected_header',
                         ('#  Copyright (c) 2014-2015 Maximilien Riehl <max@riehl.io>\n'
                          '#  This work is free. You can redistribute it and/or modify it under the\n'
                          '#  terms of the Do What The Fuck You Want To Public License, Version 2,\n'
                          '#  as published by Sam Hocevar. See the COPYING.wtfpl file for more details.\n'
                          '#\n'))

    project.set_property('distutils_console_scripts', ['isphere.exe = isphere.cli:main'])


@init(environments='teamcity')
def set_properties_for_teamcity_builds(project):
    import os
    project.set_property('teamcity_output', True)
    project.version = '%s-%s' % (project.version, os.environ.get('BUILD_NUMBER', 0))
    project.default_task = ['clean', 'install_build_dependencies', 'publish']
    project.set_property('install_dependencies_index_url', os.environ.get('PYPIPROXY_URL'))
    project.set_property('install_dependencies_use_mirrors', False)
    project.rpm_release = os.environ.get('RPM_RELEASE', 0)


@task("pdoc_generate_documentation", "Generates HTML documentation tree with pdoc")
def pdoc_generate(project, logger):
    assert_can_execute(command_and_arguments=["pdoc", "--version"],
                       prerequisite="pdoc",
                       caller=pdoc_generate.__name__)

    logger.info("Generating pdoc documentation")
    command_and_arguments = ["pdoc", "--html", "isphere", "--all-submodules", "--overwrite", "--html-dir", "api-doc"]
    source_directory = project.get_property("dir_source_main_python")
    environment = {"PYTHONPATH": source_directory,
                   "PATH": os.environ["PATH"]}

    subprocess.check_call(command_and_arguments, shell=False, env=environment)
