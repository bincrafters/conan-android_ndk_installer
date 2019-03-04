#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

from conans import ConanFile, CMake, tools, RunEnvironment
import os
import subprocess


class TestPackageConan(ConanFile):
    settings = "os", "compiler", "build_type", "arch"
    generators = "cmake"

    def build(self):
        generator = 'MinGW Makefiles' if os.name == 'nt' else 'Unix Makefiles'
        cmake = CMake(self, generator=generator)
        cmake.configure()
        cmake.build()

    def test(self):
        for var in ["CC", "CXX", "LD", "AR", "AS", "RANDLIB", "STRIP", "ADDR2LINE", "NM",
                    "OBJCOPY", "OBJDUMP", "READELF", "ELFEDIT"]:
            self.run("%s --version" % os.environ[var], run_environment=True)

        output = subprocess.check_output([os.environ['READELF'], '-h', 'test_package']).decode()
        output = output.split('\n')[1:]
        readelf = dict()
        for line in output:
            if line:
                tokens = line.split(':')
                name, value = tokens[0], tokens[1]
                readelf[name.strip()] = value.strip()
        machine = {'armv7': 'ARM',
                   'armv8': 'AArch64',
                   'x86': 'Intel 80386',
                   'x86_64': 'Advanced Micro Devices X86-64',
                   'mips': 'MIPS R3000',
                   'mips64': 'MIPS R3000'}.get(str(self.settings.arch))
        elf_class = {'armv7': 'ELF32',
                     'armv8': 'ELF64',
                     'x86': 'ELF32',
                     'x86_64': 'ELF64',
                     'mips': 'ELF32',
                     'mips64': 'ELF64'}.get(str(self.settings.arch))
        if readelf['Machine'] != machine:
            raise Exception('incorrect machine, expected %s, but found %s' % (machine, readelf['Machine']))
        if readelf['Class'] != elf_class:
            raise Exception('incorrect class, expected %s, but found %s' % (elf_class, readelf['Class']))
