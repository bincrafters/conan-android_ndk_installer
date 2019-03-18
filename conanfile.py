#!/usr/bin/env python
# -*- coding: utf-8 -*-

from conans import ConanFile, tools
from conans.errors import ConanInvalidConfiguration
import os
import fnmatch
import shutil


class AndroidNDKInstallerConan(ConanFile):
    name = "android_ndk_installer"
    version = "r19b"
    description = "The Android NDK is a toolset that lets you implement parts of your app in " \
                  "native code, using languages such as C and C++"
    url = "https://github.com/bincrafters/conan-android_ndk_installer"
    homepage = "https://developer.android.com/ndk/"
    topics = ("NDK", "android", "toolchain", "compiler")
    license = "Apache-2.0"
    exports = ["LICENSE.md"]
    short_paths = True
    no_copy_source = True
    exports_sources = ["cmake-wrapper.cmd", "cmake-wrapper"]

    settings = {"os_build": ["Windows", "Linux", "Macos"],
                "arch_build": ["x86", "x86_64"],
                "compiler": ["clang"],
                "os": ["Android"],
                "arch": ["x86", "x86_64", "armv7", "armv8"]}

    def configure(self):
        api_level = int(str(self.settings.os.api_level))
        if self.settings.os_build in ["Linux", "Macos"] and self.settings.arch_build == "x86":
            raise ConanInvalidConfiguration("x86 host is not supported "
                                            "for %s" % self.settings.os_build)
        if api_level < 16:
            raise ConanInvalidConfiguration("minumum API version for architecture %s is 16, "
                                            "but used %s" % (self.settings.arch, api_level))
        if self.settings.arch in ["x86_64", "armv8"] and api_level < 21:
            raise ConanInvalidConfiguration("minumum API version for architecture %s is 21, "
                                            "but used %s" % (self.settings.arch, api_level))
        if self.settings.compiler.version != "8":
            raise ConanInvalidConfiguration("only Clang 8 is supported")
        if self.settings.compiler.libcxx != "libc++":
            raise ConanInvalidConfiguration("only libc++ standard library is supported")

    def source(self):
        variant = "{0}-{1}".format(self._platform, self.settings.arch_build)
        archive_name = "android-ndk-{0}-{1}.zip".format(self.version, variant)
        source_url = "https://dl.google.com/android/repository/" + archive_name

        sha1 = {"windows-x86": "805e95ba96e5cc46060f5585594c6e2aef8c0304",
                "windows-x86_64": "1aaedfa02ae3b2cb09ef1ca262ceaf2aca436f96",
                "darwin-x86_64": "02a74f9b211f22bea223e91acc6f40853db818e4",
                "linux-x86_64": "16f62346ab47f7125a0e977dcc08f54881f8a3d7"}.get(variant)
        tools.get(source_url, sha1=sha1)

    @property
    def _platform(self):
        return {"Windows": "windows",
                "Macos": "darwin",
                "Linux": "linux"}.get(str(self.settings.os_build))

    @property
    def _android_abi(self):
        return {"x86": "x86",
                "x86_64": "x86_64",
                "armv7": "armeabi-v7a",
                "armv8": "arm64-v8a"}.get(str(self.settings.arch))

    @property
    def _llvm_triplet(self):
        arch = {'armv7': 'arm',
                'armv8': 'aarch64',
                'x86': 'i686',
                'x86_64': 'x86_64'}.get(str(self.settings.arch))
        abi = 'androideabi' if self.settings.arch == 'armv7' else 'android'
        return '%s-linux-%s' % (arch, abi)

    @property
    def _clang_triplet(self):
        arch = {'armv7': 'armv7a',
                'armv8': 'aarch64',
                'x86': 'i686',
                'x86_64': 'x86_64'}.get(str(self.settings.arch))
        abi = 'androideabi' if self.settings.arch == 'armv7' else 'android'
        return '%s-linux-%s' % (arch, abi)

    def _fix_permissions(self):
        if os.name != 'posix':
            return
        for root, _, files in os.walk(self.package_folder):
            for filename in files:
                filename = os.path.join(root, filename)
                with open(filename, 'rb') as f:
                    sig = f.read(4)
                    if type(sig) is str:
                        sig = [ord(s) for s in sig]
                    else:
                        sig = [s for s in sig]
                    if len(sig) > 2 and sig[0] == 0x23 and sig[1] == 0x21:
                        self.output.info('chmod on script file: "%s"' % filename)
                        self._chmod_plus_x(filename)
                    elif sig == [0x7F, 0x45, 0x4C, 0x46]:
                        self.output.info('chmod on ELF file: "%s"' % filename)
                        self._chmod_plus_x(filename)
                    elif sig == [0xCA, 0xFE, 0xBA, 0xBE] or \
                         sig == [0xBE, 0xBA, 0xFE, 0xCA] or \
                         sig == [0xFE, 0xED, 0xFA, 0xCF] or \
                         sig == [0xCF, 0xFA, 0xED, 0xFE] or \
                         sig == [0xFE, 0xEF, 0xFA, 0xCE] or \
                         sig == [0xCE, 0xFA, 0xED, 0xFE]:
                        self.output.info('chmod on Mach-O file: "%s"' % filename)
                        self._chmod_plus_x(filename)

    def _fix_command_files(self):
        # https://github.com/android-ndk/ndk/issues/920
        if self.settings.os_build != "Windows":
            return

        with tools.chdir(os.path.join(self._ndk_root, 'bin')):
            for filename in os.listdir("."):
                if fnmatch.fnmatch(filename, "*-linux-android*-clang.cmd"):
                    newfilename = filename[:-4] + "++.cmd"
                    if not os.path.isfile(newfilename):
                        self.output.info("processing %s" % filename)
                        shutil.copy(filename, newfilename)
                        tools.replace_in_file(filename, "clang++.exe", "clang.exe", strict=False)
                        tools.replace_in_file(filename, "-stdlib=libc++", "", strict=False)

    def package(self):
        ndk = "android-ndk-%s" % self.version
        self.copy(pattern="*", dst=".", src=ndk, keep_path=True, symlinks=True)
        self.copy(pattern="*NOTICE", dst="licenses", src=ndk)
        self.copy(pattern="*NOTICE.toolchain", dst="licenses", src=ndk)
        self.copy("cmake-wrapper.cmd")
        self.copy("cmake-wrapper")

        if self.settings.arch_build == "x86":
            tools.replace_in_file(os.path.join(self.package_folder, "build", "cmake", "android.toolchain.cmake"),
                                  "set(ANDROID_HOST_TAG windows-x86_64)",
                                  "set(ANDROID_HOST_TAG windows)", strict=False)
        self._fix_permissions()
        self._fix_command_files()

    @property
    def _host(self):
        return self._platform if self.settings.arch_build == "x86" else self._platform + "-x86_64"

    @property
    def _ndk_root(self):
        return os.path.join(self.package_folder, "toolchains", "llvm", "prebuilt", self._host)

    def _tool_name(self, tool):
        if 'clang' in tool:
            suffix = '.cmd' if self.settings.os_build == 'Windows' else ''
            return '%s%s-%s%s' % (self._clang_triplet, self.settings.os.api_level, tool, suffix)
        else:
            suffix = '.exe' if self.settings.os_build == 'Windows' else ''
            return '%s-%s%s' % (self._llvm_triplet, tool, suffix)

    def _define_tool_var(self, name, value):
        ndk_bin = os.path.join(self._ndk_root, 'bin')
        path = os.path.join(ndk_bin, self._tool_name(value))
        self.output.info('Creating %s environment variable: %s' % (name, path))
        return path

    def package_id(self):
        self.info.include_build_settings()
        del self.info.settings.arch
        del self.info.settings.os.api_level

    @staticmethod
    def _chmod_plus_x(filename):
        if os.name == 'posix':
            os.chmod(filename, os.stat(filename).st_mode | 0o111)

    def package_info(self):
        ndk_bin = os.path.join(self._ndk_root, 'bin')

        self.output.info('Creating NDK_ROOT environment variable: %s' % self._ndk_root)
        self.env_info.NDK_ROOT = self._ndk_root

        self.output.info('Creating ANDROID_NDK_HOME environment variable: %s' % self.package_folder)
        self.env_info.ANDROID_NDK_HOME = self.package_folder

        self.output.info('Creating CHOST environment variable: %s' % self._llvm_triplet)
        self.env_info.CHOST = self._llvm_triplet

        self.output.info('Appending PATH environment variable: %s' % ndk_bin)
        self.env_info.PATH.append(ndk_bin)

        ndk_sysroot = os.path.join(self._ndk_root, 'sysroot')
        self.output.info('Creating CONAN_CMAKE_FIND_ROOT_PATH environment variable: %s' % ndk_sysroot)
        self.env_info.CONAN_CMAKE_FIND_ROOT_PATH = ndk_sysroot

        self.output.info('Creating SYSROOT environment variable: %s' % ndk_sysroot)
        self.env_info.SYSROOT = ndk_sysroot

        self.output.info('Creating self.cpp_info.sysroot: %s' % ndk_sysroot)
        self.cpp_info.sysroot = ndk_sysroot

        self.output.info('Creating ANDROID_NATIVE_API_LEVEL environment variable: %s' % self.settings.os.api_level)
        self.env_info.ANDROID_NATIVE_API_LEVEL = str(self.settings.os.api_level)

        self._chmod_plus_x(os.path.join(self.package_folder, "cmake-wrapper"))
        cmake_wrapper = "cmake-wrapper.cmd" if self.settings.os_build == "Windows" else "cmake-wrapper"
        cmake_wrapper = os.path.join(self.package_folder, cmake_wrapper)
        self.output.info('Creating CONAN_CMAKE_PROGRAM environment variable: %s' % cmake_wrapper)
        self.env_info.CONAN_CMAKE_PROGRAM = cmake_wrapper

        toolchain = os.path.join(self.package_folder, "build", "cmake", "android.toolchain.cmake")
        self.output.info('Creating CONAN_CMAKE_TOOLCHAIN_FILE environment variable: %s' % toolchain)
        self.env_info.CONAN_CMAKE_TOOLCHAIN_FILE = toolchain

        self.env_info.CC = self._define_tool_var('CC', 'clang')
        self.env_info.CXX = self._define_tool_var('CXX', 'clang++')
        self.env_info.LD = self._define_tool_var('LD', 'ld')
        self.env_info.AR = self._define_tool_var('AR', 'ar')
        self.env_info.AS = self._define_tool_var('AS', 'as')
        self.env_info.RANLIB = self._define_tool_var('RANLIB', 'ranlib')
        self.env_info.STRIP = self._define_tool_var('STRIP', 'strip')
        self.env_info.ADDR2LINE = self._define_tool_var('ADDR2LINE', 'addr2line')
        self.env_info.NM = self._define_tool_var('NM', 'nm')
        self.env_info.OBJCOPY = self._define_tool_var('OBJCOPY', 'objcopy')
        self.env_info.OBJDUMP = self._define_tool_var('OBJDUMP', 'objdump')
        self.env_info.READELF = self._define_tool_var('READELF', 'readelf')
        self.env_info.ELFEDIT = self._define_tool_var('ELFEDIT', 'elfedit')

        self.env_info.ANDROID_PLATFORM = "android-%s" % self.settings.os.api_level
        self.env_info.ANDROID_TOOLCHAIN = "clang"
        self.env_info.ANDROID_ABI = self._android_abi
        self.env_info.ANDROID_STL = "c++_shared"

        self.env_info.CMAKE_FIND_ROOT_PATH_MODE_PROGRAM = "BOTH"
        self.env_info.CMAKE_FIND_ROOT_PATH_MODE_LIBRARY = "BOTH"
        self.env_info.CMAKE_FIND_ROOT_PATH_MODE_INCLUDE = "BOTH"
        self.env_info.CMAKE_FIND_ROOT_PATH_MODE_PACKAGE = "BOTH"
