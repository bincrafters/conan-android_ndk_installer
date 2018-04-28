#!/usr/bin/env python
# -*- coding: utf-8 -*-

from conans import ConanFile, tools
from conans.errors import ConanException
import os


class AndroidNDKInstallerConan(ConanFile):
    name = "android_ndk_installer"
    version = "r16b"
    description = "The Android NDK is a toolset that lets you implement parts of your app in native code, " \
                  "using languages such as C and C++"
    url = "https://github.com/bincrafters/conan-android_ndk_installer"
    homepage = "https://developer.android.com/ndk/"
    license = "GNU GPL"
    exports = ["LICENSE.md"]
    short_paths = True
    no_copy_source = True

    settings = {"os_build": ["Windows", "Linux", "Macos"],
                "arch_build": ["x86", "x86_64"],
                "arch": ["x86", "x86_64", "mips", "mips64", "armv7", "armv8"]}
    options = {"stl": ["gnustl", "libc++", "stlport"],
               "api": list(range(14, 28))}
    default_options = "stl=libc++", "api=21"

    def configure(self):
        if self.settings.os_build == "Linux" and self.settings.arch_build == "x86":
            raise ConanException("x86 %s host is not supported" % str(self.settings.os_build))
        if str(self.settings.arch) in ["x86_64", "armv8", "mips64"] and int(str(self.options.api)) < 21:
            raise ConanException("minumum API version for architecture %s is 21" % str(self.settings.arch))

    def source(self):
        os_name = {"Windows": "windows",
                   "Macos": "darwin",
                   "Linux": "linux"}.get(str(self.settings.os_build))
        arch_name = str(self.settings.arch_build)

        source_url = "https://dl.google.com/android/repository/android-ndk-{0}-{1}-{2}.zip".format(self.version,
                                                                                                   os_name,
                                                                                                   arch_name)
        tools.get(source_url)

    @property
    def android_arch(self):
        return {"armv7": "arm",
                "armv8": "arm64",
                "mips": "mips",
                "mips64": "mips64",
                "x86": "x86",
                "x86_64": "x86_64"}.get(str(self.settings.arch))

    @property
    def abi(self):
        return 'androideabi' if self.android_arch == 'arm' else 'android'

    @property
    def triplet(self):
        return '%s-linux-%s' % (self.android_arch, self.abi)

    def build(self):
        ndk = "android-ndk-%s" % self.version
        make_standalone_toolchain = os.path.join(self.source_folder,
                                                 ndk, 'build', 'tools', 'make_standalone_toolchain.py')
        python = tools.which('python')
        command = '%s %s --arch %s --api %s --stl %s --install-dir %s' % (python,
                                                                          make_standalone_toolchain,
                                                                          self.android_arch,
                                                                          str(self.options.api),
                                                                          str(self.options.stl),
                                                                          self.package_folder)
        self.run(command)

    def package(self):
        self.copy(pattern="LICENSE", dst="license", src='.')

    def tool_name(self, tool):
        suffix = '.exe' if self.settings.os_build == 'Windows' else ''
        return '%s%s%s' % (self.triplet, tool, suffix)

    def define_tool_var(self, name, value):
        ndk_bin = os.path.join(self.package_folder, 'bin')
        path = os.path.join(ndk_bin, self.tool_name(value))
        self.output.info('Creating %s environment variable: %s' % (name, path))
        return path

    def package_info(self):
        ndk_root = self.package_folder
        ndk_bin = os.path.join(ndk_root, 'bin')

        self.output.info('Creating CHOST environment variable: %s' % self.triplet)
        self.env_info.CHOST = self.triplet

        self.output.info('Appending PATH environment variable: %s' % ndk_bin)
        self.env_info.PATH.append(ndk_bin)

        ndk_sysroot = os.path.join(ndk_root, 'sysroot')
        self.output.info('Creating CONAN_CMAKE_FIND_ROOT_PATH environment variable: %s' % ndk_sysroot)
        self.env_info.CONAN_CMAKE_FIND_ROOT_PATH = ndk_sysroot

        self.env_info.CC = self.define_tool_var('CC', 'clang')
        self.env_info.CXX = self.define_tool_var('CXX', 'clang++')
        self.env_info.LD = self.define_tool_var('LD', 'ld')
        self.env_info.AR = self.define_tool_var('AR', 'ar')
        self.env_info.RANLIB = self.define_tool_var('RANLIB', 'ranlib')
        self.env_info.AS = self.define_tool_var('AS', 'as')
        self.env_info.STRIP = self.define_tool_var('STRIP', 'strip')
        self.env_info.NM = self.define_tool_var('NM', 'nm')
        self.env_info.ADDR2LINE = self.define_tool_var('ADDR2LINE', 'addr2line')
        self.env_info.OBJCOPY = self.define_tool_var('OBJCOPY', 'objcopy')
        self.env_info.OBJDUMP = self.define_tool_var('OBJDUMP', 'objdump')
        self.env_info.READELF = self.define_tool_var('READELF', 'readelf')
        self.env_info.ELFEDIT = self.define_tool_var('ELFEDIT', 'elfedit')