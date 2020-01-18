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
    settings['compiler.version'] = '9'
    settings['compiler.libcxx'] = 'libc++'
    settings['os'] = 'Android'
    if platform.system() == 'Windows':
        settings['os_build'] = 'Windows'
        if 'ARCH_BUILD' in os.environ:
            arches_build = [os.environ['ARCH_BUILD']]
        else:
            arches_build = ['x86_64']
    elif platform.system() == 'Linux':
        settings['os_build'] = 'Linux'
        arches_build = ['x86_64']
    elif platform.system() == 'Darwin':
        settings['os_build'] = 'Macos'
        arches_build = ['x86_64']
    if 'ARCH' in os.environ:
        arches = [os.environ['ARCH']]
    else:
        arches = ['x86', 'x86_64', 'armv7', 'armv8']
    for arch in arches:
        for arch_build in arches_build:
            settings['arch'] = arch
            settings['arch_build'] = arch_build
            if arch in ['x86', 'armv7']:
                settings['os.api_level'] = '16'
            else:
                settings['os.api_level'] = '21'
            builder.add(settings=settings.copy(), options={}, env_vars={}, build_requires={})

    builder.run()
