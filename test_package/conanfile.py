#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

from conans import ConanFile, CMake, tools, RunEnvironment
import os


class TestPackageConan(ConanFile):
    settings = "os", "compiler", "build_type", "arch"
    generators = "cmake"

    def build(self):
        if self.settings.arch == 'mips64':
            # https://github.com/android-ndk/ndk/issues/399
            if 'CFLAGS' in os.environ:
                os.environ['CFLAGS'] += ' -fintegrated-as'
            else:
                os.environ['CFLAGS'] = '-fintegrated-as'
            if 'CXXFLAGS' in os.environ:
                os.environ['CXXFLAGS'] += ' -fintegrated-as'
            else:
                os.environ['CXXFLAGS'] = '-fintegrated-as'
        generator = 'MinGW Makefiles' if os.name == 'nt' else 'Unix Makefiles'
        cmake = CMake(self, generator=generator)
        cmake.configure()
        cmake.build()

    def test(self):
        with tools.environment_append(RunEnvironment(self).vars):
            bin_path = os.path.join("bin", "test_package")
            if self.settings.os == "Windows":
                self.run(bin_path)
            elif self.settings.os == "Macos":
                self.run("DYLD_LIBRARY_PATH=%s %s" % (os.environ.get('DYLD_LIBRARY_PATH', ''), bin_path))
            else:
                self.run("LD_LIBRARY_PATH=%s %s" % (os.environ.get('LD_LIBRARY_PATH', ''), bin_path))
