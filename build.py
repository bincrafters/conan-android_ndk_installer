#!/usr/bin/env python
# -*- coding: utf-8 -*-


from bincrafters import build_template_default
import platform
import os

if __name__ == "__main__":

    builder = build_template_default.get_builder()
    builder.builds = []

    settings = dict()
    settings['compiler'] = 'clang'
    settings['compiler.version'] = '5.0'
    settings['compiler.libcxx'] = 'libc++'
    settings['os'] = 'Android'
    settings['os.api_level'] = '21'
    if platform.system() == 'Windows':
        settings['os_build'] = 'Windows'
        if 'ARCH_BUILD' in os.environ:
            arches_build = [os.environ['ARCH_BUILD']]
        else:
            arches_build = ['x86', 'x86_64']
    elif platform.system() == 'Linux':
        settings['os_build'] = 'Linux'
        arches_build = ['x86_64']
    elif platform.system() == 'Darwin':
        settings['os_build'] = 'Macos'
        arches_build = ['x86_64']
    settings['arch_build'] = 'x86_64'

    for arch in ['x86', 'x86_64', 'armv7', 'armv8', 'mips', 'mips64']:
        for arch_build in arches_build:
            settings['arch'] = arch
            settings['arch_build'] = arch_build
            builder.add(settings=settings.copy(), options={}, env_vars={}, build_requires={})

    builder.run()
