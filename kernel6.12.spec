%define buildid 95.123

# We have to override the new %%install behavior because, well... the kernel is special.
%global __spec_install_pre %%{___build_pre}

# We do our own build flags management.  In particular, see
# rpm_inherit_flags below.
%undefine _auto_set_build_flags

# Package notes are also causing trouble with our current spec file
%undefine _package_note_file

# This isn't available generically
%define dracutlibdir %{_prefix}/lib/dracut

Summary: The Linux kernel

# Amazon: Enable module signing and disable efi
%global signmodules 1
%if 0%{?amzn} >= 2022
%global signkernel 1
%else
%global signkernel 0
%endif

# Amazon Linux secure boot key name and version
%global amzn_sb_keyname sign-kernel
%global amzn_sb_keyver 1

# Save original buildid for later if it's defined
%if 0%{?buildid:1}
%global orig_buildid %{buildid}
%undefine buildid
%endif

###################################################################
# Polite request for people who spin their own kernel rpms:
# please modify the "buildid" define in a way that identifies
# that the kernel isn't the stock distribution kernel, for example,
# by setting the define to ".local" or ".bz123456". This will be
# appended to the full kernel version.
#
# (Uncomment the '#' and both spaces below to set the buildid.)
#
# %% define buildid .local
###################################################################

# The buildid can also be specified on the rpmbuild command line
# by adding --define="buildid .whatever". If both the specfile and
# the environment define a buildid they will be concatenated together.
%if 0%{?orig_buildid:1}
%if 0%{?buildid:1}
%global srpm_buildid %{buildid}
%define buildid %{srpm_buildid}%{orig_buildid}
%else
%define buildid %{orig_buildid}
%endif
%endif

# what kernel is it we are building
%global kversion 6.12.73
%define rpmversion %{kversion}
%global kbasever 6.12

# What parts do we want to build?  We must build at least one kernel.
# These are the kernels that are built IF the architecture allows it.
# All should default to 1 (enabled) and be flipped to 0 (disabled)
# by later arch-specific checks.

# The following build options are enabled by default.
# Use either --without <opt> in your rpmbuild command or force values
# to 0 in here to disable them.
#
# standard kernel
%define with_up        %{?_without_up:        0} %{?!_without_up:        1}
# kernel-debug
%define with_debug     %{?_without_debug:     0} %{?!_without_debug:     0}
# kernel-doc
%define with_doc       %{?_without_doc:       0} %{?!_without_doc:       0}
# kernel-headers
%define with_headers   %{?_without_headers:   0} %{?!_without_headers:   1}
# perf
%define with_perf      %{?_without_perf:      0} %{?!_without_perf:      1}
# tools
%define with_tools     %{?_without_tools:     0} %{?!_without_tools:     1}
# bpf tool
%define with_bpftool   %{?_without_bpftool:   0} %{?!_without_bpftool:   1}
# kernel-debuginfo
%define with_debuginfo %{?_without_debuginfo: 0} %{?!_without_debuginfo: 1}
# Want to build a the vsdo directories installed
%define with_vdso_install %{?_without_vdso_install: 0} %{?!_without_vdso_install: 1}
# Control whether we build the hmac for fips mode
%define with_fips      %{?_without_fips:       0} %{?!_without_fips:   1}
# libbpf 
%define with_libbpf    %{?_without_libbpf:     0} %{?!_without_libbpf:   0}

# Build the kernel-doc package, but don't fail the build if it botches.
# Here "true" means "continue" and "false" means "fail the build".
%define doc_build_fail true

# should we do C=1 builds with sparse
%define with_sparse	%{?_with_sparse:      1} %{?!_with_sparse:      0}
# build kernel configs only
%define with_configs_only %{?_with_configs_only:   1} %{?!_with_configs_only:   0}

# Set debugbuildsenabled to 1 for production (build separate debug kernels)
#  and 0 for rawhide (all kernels are debug kernels).
# See also 'make debug' and 'make release'.
%if 0%{amzn}
%define debugbuildsenabled 1
%else
%define debugbuildsenabled 0
%endif

# do we want the oldconfig run over the config files (when regenerating
# configs this should be avoided in order to save duplicate work...)
%define with_oldconfig     %{?_without_oldconfig:      0} %{?!_without_oldconfig:      1}

# pkg_release is what we'll fill in for the rpm Release: field
%define pkg_release %{?buildid}%{?dist}

%define make_target bzImage

%define KVERREL %{rpmversion}-%{pkg_release}.%{_target_cpu}
%define hdrarch %_target_cpu
%define asmarch %_target_cpu

%if !%{debugbuildsenabled}
%define with_debug 0
%endif

%if !%{with_debuginfo}
%define _enable_debug_packages 0
%endif
%define debuginfodir /usr/lib/debug
%global _build_id_links alldebug

%define all_x86 i386 i686

%if %{with_vdso_install}
# These arches install vdso/ directories.
%define vdso_arches x86_64 aarch64
%endif

# Overrides for generic default options

# don't do debug builds on anything but x86_64 and aarch64
%ifnarch x86_64 aarch64
%define with_debug 0
%endif

# only package docs noarch
%ifnarch noarch
%define with_doc 0
%endif

# don't build noarch kernels or headers (duh)
%ifarch noarch
%define with_up 0
%define with_headers 0
%define with_tools 0
%define with_perf 0
%define signmodules 0
%define all_arch_configs kernel-%{version}-*.config
%endif

# Per-arch tweaks

%ifarch %{all_x86}
%define asmarch x86
%define hdrarch i386
%define all_arch_configs kernel-%{version}-i?86*.config
%define image_install_path boot
%define kernel_image arch/%{asmarch}/boot/bzImage
%endif

%ifarch x86_64
%define asmarch x86
%define all_arch_configs kernel-%{version}-x86_64*.config
%define image_install_path boot
%define kernel_image arch/%{asmarch}/boot/bzImage
%endif

%ifarch aarch64
%define all_arch_configs kernel-%{version}-aarch64*.config
%define asmarch arm64
%define hdrarch arm64
%define image_install_path boot
%define make_target vmlinuz.efi
%define kernel_image arch/%{asmarch}/boot/vmlinuz.efi
%define with_perf 1
%endif

# amazon: don't use nonint config target - we want to know when our config files are
# not complete
%define oldconfig_target olddefconfig
# To temporarily exclude an architecture from being built, add it to
# %%nobuildarches. Do _NOT_ use the ExclusiveArch: line, because if we
# don't build kernel-headers then the new build system will no longer let
# us use the previous build of that package -- it'll just be completely AWOL.
# Which is a BadThing(tm).

%global GCC_VER gcc10-

# We don't build a kernel on i386; we only do kernel-headers there
%define nobuildarches i386 i486 i586 i686 noarch

%if 0%{?amzn} >= 2022
%define with_libbpf 1
%global libbpf_version 1.5.0
%endif 

%if 0%{?amzn} >= 2022
%define with_mods_extra 1
%else
%define with_mods_extra 0
%endif

%ifarch %nobuildarches
%define with_up 0
%define with_debug 0
%define with_debuginfo 0
%define with_perf 0
%define with_bpftool 0
%define with_tools 0
%define _enable_debug_packages 0
%define signmodules 0
%define with_libbpf 0
%define with_mods_extra 0
%define with_configs_only 0
%endif

%if %{with_configs_only}
%define with_bpftool 0
%define with_debug 0
%define with_debuginfo 0
%define with_doc 0
%define with_fips 0
%define with_headers 0
%define with_libbpf 0
%define with_mods_extra 0
%define with_perf 0
%define with_sparse 0
%define with_tools 0
%define with_up 0
%define with_vdso_install 0
%define signmodules 0
%endif

# Architectures we build tools/cpupower on
%define cpupowerarchs %{ix86} x86_64 aarch64
#define cpupowerarchs none

#
# Three sets of minimum package version requirements in the form of Conflicts:
# to versions below the minimum
#

#
# Packages that need to be installed before the kernel is, because the %%post
# scripts use them.
#
%if 0%{?amzn} >= 2022
%define kernel_prereq  coreutils, systemd >= 203-2, /usr/bin/kernel-install
%define initrd_prereq  dracut >= 027
%define microcode_ctl_version 2:2.1-43
# This is the version of linux-firmware where amd-ucode-firmware was split off as a subpackage
%define linux_firmware_version 20210208-117.amzn2023.0.6
%else
%define kernel_prereq  fileutils, module-init-tools, initscripts >= 8.11.1-1, grubby >= 7.0.15-2.5
%define initrd_prereq  dracut >= 004-336.27
%define microcode_ctl_version 2:2.1-47.amzn2.2.15
# This is the version of linux-firmware where amd-ucode-firmware was split off as a subpackage
%define linux_firmware_version 20200421-83.git78c0348.amzn2
%endif

%define __python %{__python3}
%define py_pkg_prefix python3

#
# This macro takes a package name, such as kernel-tools, as argument, and
# obsoletes all released 6.12 packages. This is useful when switching from
# unnamespaced packages to namespacing.
#
%define obsolete_released_6_12_packages() \
Obsoletes: %{1} = 6.12.20-23.97.amzn2023\
Obsoletes: %{1} = 6.12.22-27.96.amzn2023\
Obsoletes: %{1} = 6.12.23-29.97.amzn2023\
Obsoletes: %{1} = 6.12.25-32.101.amzn2023\
Obsoletes: %{1} = 6.12.29-33.102.amzn2023\
Obsoletes: %{1} = 6.12.30-34.92.amzn2023\
Obsoletes: %{1} = 6.12.31-35.92.amzn2023\
Obsoletes: %{1} = 6.12.35-55.103.amzn2023\
%{nil}

#
# This macro does requires, provides, conflicts for a namespaced package.
#	%%namespaced_pkg_conflicts <unnamespaced subpackage name>
# This macro makes sure that the namespaced package conflicts with the unnamespaced version.
#
%define namespaced_pkg_conflicts() \
Provides: %{1} = %{?epoch:%{epoch}:}%{rpmversion}-%{pkg_release}\
Provides: %{1}%{_isa} = %{?epoch:%{epoch}:}%{rpmversion}-%{pkg_release}\
Conflicts: %{1}\
# We need to conflict with the older kernel series which implies that these\
# packages can only be installed if older kernels are removed. This is a\
# work-around to avoid picking the latest namespaced package as an indirect\
# dependency. For example, `dnf install kernel-headers` installs the\
# non-namespaced version while `dnf install glibc-devel` might install the\
# package that provides the highest version of `kernel-headers` which might be\
# kernel6.12-headers.\
Conflicts: kernel-uname-r < %{kbasever}\
%obsolete_released_6_12_packages %{1}\
%{nil}

#
# This macro does requires, provides, conflicts, obsoletes for a kernel package.
#	%%kernel_reqprovconf <subpackage>
# It uses any kernel_<subpackage>_conflicts and kernel_<subpackage>_obsoletes
# macros defined above.
#
# Require on kernel-devel if kernel-devel is installed makes sure that all
# matching kernel-devel packages are installed if the user installs
# kernel-devel. Same for kernel-modules-extra.
%define kernel_reqprovconf \
Provides: kernel = %{?epoch:%{epoch}:}%{rpmversion}-%{pkg_release}\
Provides: kernel-%{_target_cpu} = %{?epoch:%{epoch}:}%{rpmversion}-%{pkg_release}%{?1:.%{1}}\
Provides: kernel-drm-nouveau = 16\
Provides: kernel-modeset = 1\
Provides: kernel-uname-r = %{KVERREL}%{?variant}%{?1:.%{1}}\
Requires: (kernel-devel = %{?epoch:%{epoch}:}%{version}-%{release}%{?1:.%{1}} if kernel-devel)\
Requires: (kernel-modules-extra = %{?epoch:%{epoch}:}%{version}-%{release}%{?1:.%{1}} if kernel-modules-extra)\
Requires(pre): %{kernel_prereq}\
Requires(pre): %{initrd_prereq}\
%if %{with_perf}\
Suggests: perf%{kbasever}\
Suggests: %{py_pkg_prefix}-perf%{kbasever}\
%endif\
%if 0%{?amzn} < 2022\
Requires(post): %{_sbindir}/new-kernel-pkg\
Requires(preun): %{_sbindir}/new-kernel-pkg\
%else\
%if %{signkernel} \
%{?amzn_sb_requires}\
%endif\
%endif\
%{expand:%%{?kernel%{?1:_%{1}}_conflicts:Conflicts: %%{kernel%{?1:_%{1}}_conflicts}}}\
%{expand:%%{?kernel%{?1:_%{1}}_obsoletes:Obsoletes: %%{kernel%{?1:_%{1}}_obsoletes}}}\
%{expand:%%{?kernel%{?1:_%{1}}_provides:Provides: %%{kernel%{?1:_%{1}}_provides}}}\
# We can't let RPM do the dependencies automatic because it'll then pick up\
# a correct but undesirable perl dependency from the module headers which\
# isn't required for the kernel proper to function\
AutoReq: no\
AutoProv: yes\
%{nil}

Name: kernel%{kbasever}%{?variant}
Group: System Environment/Kernel
License: GPLv2 and Redistributable, no modification permitted
URL: http://www.kernel.org/
# Keep this the same for all kernel builds in a distro
Epoch: 1
Version: %{rpmversion}
Release: %{pkg_release}
# DO NOT CHANGE THE 'ExclusiveArch' LINE TO TEMPORARILY EXCLUDE AN ARCHITECTURE BUILD.
# SET %%nobuildarches (ABOVE) INSTEAD
ExclusiveArch: noarch %{all_x86} x86_64 aarch64
ExclusiveOS: Linux

%kernel_reqprovconf
%ifarch x86_64
Requires(pre): microcode_ctl >= %{microcode_ctl_version}
Requires(pre): amd-ucode-firmware >= %{linux_firmware_version}
%endif

%ifarch x86_64
Obsoletes: kernel-smp
%endif

Provides: kmod-lustre-client = 2.15.6

#
# List the packages used during the kernel build
#
BuildRequires: kmod, patch, bash, tar, bison
BuildRequires: bzip2, xz, findutils, gzip, m4, perl, make, diffutils, gawk
BuildRequires: hostname, openssl rsync, python3, python3-devel, dwarves >= 1.16
BuildRequires: glibc-static
%if 0%{?amzn} >= 2022
BuildRequires: gcc
BuildRequires: systemd-rpm-macros
%else
BuildRequires: gcc10, gcc10-binutils >= 2.35
%endif
# Required for kernel documentation build
%if %{with_doc}
BuildRequires: %{py_pkg_prefix}-virtualenv, %{py_pkg_prefix}-sphinx
%endif
#defines based on the compiler version we need to use
%if 0%{?amzn} >= 2022
%global _gcc gcc
%global _gxx g++
%else
%global _gcc %{GCC_VER}gcc
%global _gxx %{GCC_VER}g++
%endif

%global _gccver %(eval %{_gcc} -dumpfullversion 2>/dev/null || :)
%if "%{_gccver}" > "7"
Provides: buildrequires(gcc) = %{_gccver}
%endif
BuildRequires: binutils >= 2.12
BuildRequires: system-rpm-config, gdb, bc
BuildRequires: net-tools
BuildRequires: xmlto, asciidoc
BuildRequires: openssl-devel
%if %{with_sparse}
BuildRequires: sparse >= 0.4.1
%endif
%if %{with_perf}
BuildRequires: elfutils-devel zlib-devel binutils-devel newt-devel %{py_pkg_prefix}-devel libtraceevent-devel
BuildRequires: audit-libs-devel
%if 0%{?amzn} >= 2022
BuildRequires: javapackages-local
%else
BuildRequires: java-devel
%endif
BuildRequires: libzstd-devel
BuildRequires: numactl-devel
%endif
%if %{with_tools}
BuildRequires: pciutils-devel gettext
BuildRequires: libcap-devel
%endif
%if %{with_bpftool}
%if 0%{?amzn} >= 2022
BuildRequires: %{py_pkg_prefix}-docutils
%else
BuildRequires: python-docutils
%endif
BuildRequires: zlib-devel binutils-devel
%endif
%if %{with_libbpf}
BuildRequires: gcc elfutils-libelf-devel elfutils-devel python3
BuildRequires: make
%endif
BuildConflicts: rhbuildsys(DiskFree) < 3000Mb
%if %{with_debuginfo}
BuildRequires: rpm-build >= 4.11.3-40.amzn2.0.4, elfutils
# Most of these should be enabled after more investigation
%undefine _include_minidebuginfo
%undefine _find_debuginfo_dwz_opts
%if 0%{?amzn} >= 2022
%undefine _unique_build_ids
%undefine _unique_debug_names
%undefine _unique_debug_srcs
%undefine _debugsource_packages
%global _find_debuginfo_opts_btf --keep-section '.BTF'
%endif
%undefine _debuginfo_subpackages
%global _find_debuginfo_opts -r
%global _missing_build_ids_terminate_build 1
%global _no_recompute_build_ids 1
%endif

%if %{signmodules} || %{signkernel}
BuildRequires: pesign >= 0.10-4
%endif
%if %{signkernel}
BuildRequires: amazon-linux-sb-keys
%endif

%if %{with_fips}
BuildRequires: hmaccalc
%endif

Source0: linux-6.12.73.tar.xz
Source1: linux-6.12.73-patches.tar

# this is for %%{signmodules}
Source11: x509.genkey

Source15: kconfig.py
Source16: mod-extra.list
Source17: mod-extra.sh
Source18: mod-extra-sign.sh
%define modsign_cmd %{SOURCE18}

Source19: Makefile.config
Source20: config-x86_64
Source21: config-x86_64-debug
Source30: config-aarch64
Source31: config-aarch64-debug
Source50: split-man.pl
Source60: Makefile.module 
%define split_man_cmd %{SOURCE50}

# udev and dracut rules for module-extras
Source100: drm-simplefb.rules
Source101: dracut-drm-simplefb.module

# Sources for kernel-tools
Source2000: cpupower.init
Source2001: cpupower.config

# __PATCHFILE_TEMPLATE__
Patch0001: 0001-Sysfs-memory-probe-interface.patch
Patch0002: 0002-arm64-mm-Enable-sysfs-based-memory-hot-remove-probe.patch
Patch0003: 0003-memory-fix-offline_and_remove_memory-use.patch
Patch0004: 0004-drivers-base-memory-use-MHP_MEMMAP_ON_MEMORY-from-th.patch
Patch0005: 0005-mm-add-offline-page-reporting-interface.patch
Patch0006: 0006-virtio-add-hack-to-allow-pre-mapped-scatterlists.patch
Patch0007: 0007-virtio-balloon-optionally-report-offlined-memory-ran.patch
Patch0008: 0008-Introduce-page-touching-DMA-ops-binding.patch
Patch0009: 0009-Correct-read-overflow-in-page-touching-DMA-ops-bindi.patch
Patch0010: 0010-Enable-ptIOMMU-for-all-supported-platforms.patch
Patch0011: 0011-drivers-introduce-AMAZON_DRIVER_UPDATES.patch
Patch0012: 0012-drivers-Add-amazon-drivers-for-EFA-ENA-and-igb_uio.patch
Patch0013: 0013-drivers-amazon-net-ena-config-Add-ENA_HAVE_ETHTOOL_R.patch
Patch0014: 0014-AL2023-6.1-Update-ena-driver-to-2.12.3g.patch
Patch0015: 0015-drivers-amazon-net-ena-ena_xdp-Use-napi_alloc_skb.patch
Patch0016: 0016-drivers-amazon-net-ena-ena_xdp-Fix-build-failure-due.patch
Patch0017: 0017-dma-Automatically-enable-page-touching-on-Caspian.patch
Patch0018: 0018-ena-efa-fixes-for-kernel-6.11.patch
Patch0019: 0019-TEMPORARILY-Revert-arm64-Kconfig-Enable-hotplug-CPU-.patch
Patch0020: 0020-perf-x86-amd-core-Don-t-unfreeze-LBR.patch
Patch0021: 0021-efa-fix-to-account-for-upstream-change.patch
Patch0022: 0022-page_touching-select-ARCH_HAS_DMA_OPS.patch
Patch0023: 0023-AL2023-6.12-Update-EFA-driver-to-2.13.1.patch
Patch0024: 0024-Config-glue-for-Lustre-client.patch
Patch0025: 0025-Lustre-client-support-for-6.12-kernel.patch
Patch0026: 0026-xen-manage-keep-track-of-the-on-going-suspend-mode.patch
Patch0027: 0027-xen-manage-introduce-helper-function-to-know-the-on-.patch
Patch0028: 0028-xenbus-add-freeze-thaw-restore-callbacks-support.patch
Patch0029: 0029-x86-xen-Introduce-new-function-to-map-HYPERVISOR_sha.patch
Patch0030: 0030-x86-xen-add-system-core-suspend-and-resume-callbacks.patch
Patch0031: 0031-xen-blkfront-add-callbacks-for-PM-suspend-and-hibern.patch
Patch0032: 0032-xen-netfront-add-callbacks-for-PM-suspend-and-hibern.patch
Patch0033: 0033-xen-time-introduce-xen_-save-restore-_steal_clock.patch
Patch0034: 0034-x86-xen-save-and-restore-steal-clock.patch
Patch0035: 0035-xen-events-add-xen_shutdown_pirqs-helper-function.patch
Patch0036: 0036-x86-xen-close-event-channels-for-PIRQs-in-system-cor.patch
Patch0037: 0037-PM-hibernate-update-the-resume-offset-on-SNAPSHOT_SE.patch
Patch0038: 0038-Revert-xen-dont-fiddle-with-event-channel-masking-in.patch
Patch0039: 0039-xen-blkfront-Fixed-blkfront_restore-to-remove-a-call.patch
Patch0040: 0040-x86-tsc-avoid-system-instability-in-hibernation.patch
Patch0041: 0041-block-xen-blkfront-consider-new-dom0-features-on-res.patch
Patch0042: 0042-xen-restore-pirqs-on-resume-from-hibernation.patch
Patch0043: 0043-xen-Only-restore-the-ACPI-SCI-interrupt-in-xen_resto.patch
Patch0044: 0044-xen-netfront-call-netif_device_attach-on-resume.patch
Patch0045: 0045-xen-Restore-xen-pirqs-on-resume-from-hibernation.patch
Patch0046: 0046-block-xen-blkfront-bump-the-maximum-number-of-indire.patch
Patch0047: 0047-Revert-xen-x2apic-enable-x2apic-mode-when-supported-.patch
Patch0048: 0048-x86-Disable-KASLR-when-Xen-is-detected.patch
Patch0049: 0049-media-Import-v4l2loopback-v0.13.2.patch
Patch0050: 0050-AL2023-6.12-Update-ena-driver-to-2.13.2g.patch
Patch0051: 0051-arm64-Export-acpi_psci_use_hvc-symbol.patch
Patch0052: 0052-hwrng-Add-Gravition-RNG-driver.patch
Patch0053: 0053-arm64-pt_regs-assert-pt_regs-is-a-multiple-of-16-byt.patch
Patch0054: 0054-arm64-pt_regs-remove-stale-big-endian-layout.patch
Patch0055: 0055-arm64-pt_regs-rename-pmr_save-pmr.patch
Patch0056: 0056-arm64-pt_regs-swap-unused-and-pmr-fields.patch
Patch0057: 0057-arm64-use-a-common-struct-frame_record.patch
Patch0058: 0058-arm64-stacktrace-move-dump_backtrace-to-kunwind_stac.patch
Patch0059: 0059-arm64-stacktrace-report-source-of-unwind-data.patch
Patch0060: 0060-arm64-stacktrace-report-recovered-PCs.patch
Patch0061: 0061-arm64-stacktrace-split-unwind_consume_stack.patch
Patch0062: 0062-arm64-stacktrace-unwind-exception-boundaries.patch
Patch0063: 0063-arm64-stacktrace-Skip-reporting-LR-at-exception-boun.patch
Patch0064: 0064-arm64-stacktrace-Don-t-WARN-when-unwinding-other-tas.patch
Patch0065: 0065-acpi-Support-CONFIG_ACPI-without-CONFIG_PCI.patch
Patch0066: 0066-ip-Bump-default-ttl-to-127.patch
Patch0067: 0067-ptp-Add-support-for-the-AMZNC10C-vmclock-device.patch
Patch0068: 0068-ptp-vmclock-Add-.owner-to-vmclock_miscdev_fops.patch
Patch0069: 0069-ptp-vmclock-Set-driver-data-before-its-usage.patch
Patch0070: 0070-ptp-vmclock-Don-t-unregister-misc-device-if-it-was-n.patch
Patch0071: 0071-ptp-vmclock-Clean-up-miscdev-and-ptp-clock-through-d.patch
Patch0072: 0072-ptp-vmclock-Remove-goto-based-cleanup-logic.patch
Patch0073: 0073-Revert-memcg-use-ratelimited-stats-flush-in-the-recl.patch
Patch0074: 0074-KEYS-Make-use-of-platform-keyring-for-module-signatu.patch
Patch0075: 0075-scripts-sign_file-Add-option-to-keep-signing-certifi.patch
Patch0076: 0076-AL2023-6.12-Update-lustre-and-lnet-to-2.15.6-fsx16-c.patch
Patch0077: 0077-AL2023-6.12-Update-lustrefsx-to-2.15.6-fsx18-commit.patch
Patch0078: 0078-asm-generic-introduce-text-patching.h.patch
Patch0079: 0079-arm64-patching-Rename-aarch64_insn_copy-to-text_poke.patch
Patch0080: 0080-arm64-module-Use-text-poke-API-for-late-relocations.patch
Patch0081: 0081-AL2023-6.12-Update-ena-driver-to-2.14.1g.patch
Patch0082: 0082-Enable-Algorithims-for-Amazon-Linux-6.1.y.patch
Patch0083: 0083-crypto-ecdh-zeroize-crpytographic-keys-after-use.patch
Patch0084: 0084-random-Add-hook-to-override-device-reads-and-getrand.patch
Patch0085: 0085-crypto-rng-Override-drivers-char-random-in-FIPS-mode.patch
Patch0086: 0086-crypto-Only-allow-GCM-in-FIPS-when-instantiated-via-.patch
Patch0087: 0087-random-allow-reseeding-DRBG-with-getrandom.patch
Patch0088: 0088-crypto-rng-Use-a-different-crypto_rng-for-reseeding.patch
Patch0089: 0089-crypto-dh-Add-SP800-56A-rev-3-Pair-wise-Consistency-.patch
Patch0090: 0090-crypto-ecc-Add-SP800-56A-rev-3-Pair-wise-Consistency.patch
Patch0091: 0091-crypto-ecc-Remove-flipping-of-private-key-in-selftes.patch
Patch0092: 0092-Override-drivers-char-random-only-after-FIPS-mode-RN.patch
Patch0093: 0093-virtio-break-and-reset-virtio-devices-on-device_shut.patch
Patch0094: 0094-virtgpu-don-t-reset-on-shutdown.patch
Patch0095: 0095-ublk-fix-race-between-io_uring_cmd_complete_in_task-.patch
Patch0096: 0096-AL2023-6.12-Update-lustrefsx-to-2.15.6-fsx19-commit.patch
Patch0097: 0097-net-Change-IPv4-6-IP-fragmentation-waiting-time-to-1.patch
Patch0098: 0098-jfs-fix-array-index-out-of-bounds-read-in-add_missin.patch
Patch0099: 0099-exfat-fix-double-free-in-delayed_free.patch
Patch0100: 0100-crypto-rng-fix-incorrect-mutex-unlock-in-crypto_del_.patch
Patch0101: 0101-Revert-mm-hugetlb-fix-huge_pmd_unshare-vs-GUP-fast-r.patch
Patch0102: 0102-AL2023-6.12-Update-EFA-driver-to-2.17.2.patch
Patch0103: 0103-Updating-lustrefsx-to-2.15.6.patch
Patch0104: 0104-mm-damon-core-prevent-unnecessary-overflow-in-damos_.patch
Patch0105: 0105-net-mlx5-Introduce-data-placement-ordering-bits.patch
Patch0106: 0106-RDMA-mlx5-Support-OOO-RX-WQE-consumption.patch
Patch0107: 0107-RDMA-mlx5-Support-querying-per-plane-IB-PortCounters.patch
Patch0108: 0108-net-sched-Fix-backlog-accounting-in-qdisc_dequeue_in.patch
Patch0109: 0109-arm64-stacktrace-Implement-arch_stack_walk_reliable.patch
Patch0110: 0110-arm64-Implement-HAVE_LIVEPATCH.patch
Patch0111: 0111-net-mlx5-HWS-Fix-memory-leak-in-hws_pool_buddy_init-.patch
Patch0112: 0112-AL2023-6.12-Update-ena-driver-to-2.15.0g.patch
Patch0113: 0113-drivers-media-v4l2loopback-ingest-version-0.15.1.patch
Patch0114: 0114-vfio-pci-enable-mmap-ing-ena-device.patch
Patch0115: 0115-crypto-rng-Remove-reseeding-call.patch
Patch0116: 0116-AL2023-6.12-Update-lustrefsx-to-2.15.6-fsx23-commit.patch
Patch0117: 0117-drivers-amazon-net-Update-igb_uio.patch
Patch0118: 0118-AL2023-6.12-Update-lustrefsx-to-2.15.6-fsx25-commit.patch
Patch0119: 0119-Revert-sched-fair-Proportional-newidle-balance.patch
Patch0120: 0120-AL2023-6.12-Update-ena-driver-to-2.16.1g.patch
Patch0121: 0121-iommu-Skip-PASID-validation-for-devices-without-PASI.patch
Patch0122: 0122-AL2023-6.12-Update-lustrefsx-to-2.15.6-fsx27-commit.patch

BuildRoot: %{_tmppath}/kernel-%{KVERREL}-root

%description
The kernel package contains the Linux kernel (vmlinuz), the core of any
Linux operating system.  The kernel handles the basic functions
of the operating system: memory allocation, process allocation, device
input and output, etc.


%package doc
Summary: Various documentation bits found in the kernel source
Group: Documentation
%description doc
This package contains documentation files from the kernel
source. Various bits of information about the Linux kernel and the
device drivers shipped with it are documented in these files.

You'll want to install this package if you need a reference to the
options that can be passed to Linux kernel modules at load time.


%package headers
Summary: Header files for the Linux kernel for use by glibc
Group: Development/System
Obsoletes: glibc-kernheaders < 3.0-46
Provides: glibc-kernheaders = 3.0-46
%namespaced_pkg_conflicts kernel-headers
%description headers
Kernel-headers includes the C header files that specify the interface
between the Linux kernel and userspace libraries and programs.  The
header files define structures and constants that are needed for
building most standard programs and are also needed for rebuilding the
glibc package.

%package debuginfo-common-%{_target_cpu}
Summary: Kernel source files used by %{name}-debuginfo packages
Group: Development/Debug
%description debuginfo-common-%{_target_cpu}
This package is required by %{name}-debuginfo subpackages.
It provides the kernel source files common to all builds.

%if %{with_perf}
%package -n perf%{kbasever}
Summary: Performance monitoring for the Linux kernel
Group: Development/System
Requires: libzstd
License: GPLv2
%namespaced_pkg_conflicts perf
%description -n perf%{kbasever}
This package contains the perf tool, which enables performance monitoring
of the Linux kernel.

%package -n perf%{kbasever}-debuginfo
Summary: Debug information for package perf
Group: Development/Debug
Requires: %{name}-debuginfo-common-%{_target_cpu} = %{?epoch:%{epoch}:}%{version}-%{release}
AutoReqProv: no
%namespaced_pkg_conflicts perf-debuginfo
%description -n perf%{kbasever}-debuginfo
This package provides debug information for the perf package.

# Note that this pattern only works right to match the .build-id
# symlinks because of the trailing nonmatching alternation and
# the leading .*, because of find-debuginfo.sh's buggy handling
# of matching the pattern against the symlinks file.
%{expand:%%global _find_debuginfo_opts %{?_find_debuginfo_opts} -p '.*%%{_bindir}/(perf|trace)(\.debug)?|.*%%{_libexecdir}/perf-core/.*|.*%%{_libdir}/libperf-jvmti.so(\.debug)?|XXX' -o perf-debuginfo.list}

%package -n %{py_pkg_prefix}-perf%{kbasever}
Summary: Python bindings for apps which will manipulate perf events
Group: Development/Libraries
%namespaced_pkg_conflicts %{py_pkg_prefix}-perf
%description -n %{py_pkg_prefix}-perf%{kbasever}
The python-perf package contains a module that permits applications
written in the Python programming language to use the interface
to manipulate perf events.

%package -n %{py_pkg_prefix}-perf%{kbasever}-debuginfo
Summary: Debug information for package perf python bindings
Group: Development/Debug
Requires: %{name}-debuginfo-common-%{_target_cpu} = %{?epoch:%{epoch}:}%{version}-%{release}
AutoReqProv: no
%namespaced_pkg_conflicts %{py_pkg_prefix}-perf-debuginfo
%description -n %{py_pkg_prefix}-perf%{kbasever}-debuginfo
This package provides debug information for the perf python bindings.

%{expand:%%global _find_debuginfo_opts %{?_find_debuginfo_opts} -p '.*%%{python_sitearch}/perf.*so(\.debug)?|XXX' -o %{py_pkg_prefix}-perf-debuginfo.list}

%endif

%if %{with_tools}
%package tools
Summary: Assortment of tools for the Linux kernel
Group: Development/System
License: GPLv2
Provides:  cpupowerutils = 1:009-0.6.p1
Obsoletes: cpupowerutils < 1:009-0.6.p1
Provides:  cpufreq-utils = 1:009-0.6.p1
Provides:  cpufrequtils = 1:009-0.6.p1
Obsoletes: cpufreq-utils < 1:009-0.6.p1
Obsoletes: cpufrequtils < 1:009-0.6.p1
Obsoletes: cpuspeed < 1:1.5-16
%if 0%{?amzn} >= 2022
Obsoletes: kernel-tools-libs < 5.15
Provides: kernel-tools-libs = %{?epoch:%{epoch}:}%{version}-%{release}
%endif
%namespaced_pkg_conflicts kernel-tools

%description tools
This package contains the tools/ directory from the kernel source
and the supporting documentation.

%package tools-devel
Summary: Assortment of tools for the Linux kernel
Group: Development/System
License: GPLv2
Requires: kernel-tools = %{?epoch:%{epoch}:}%{version}-%{release}
%ifarch %{cpupowerarchs}
Provides:  cpupowerutils-devel = 1:009-0.6.p1
Obsoletes: cpupowerutils-devel < 1:009-0.6.p1
%endif
%if 0%{?amzn} >= 2022
Obsoletes: kernel-tools-libs-devel < 5.15
Provides: kernel-tools-libs-devel = %{?epoch:%{epoch}:}%{version}-%{release}
%endif
%namespaced_pkg_conflicts kernel-tools-devel

%description tools-devel
This package contains the development files for the tools/ directory from
the kernel source.

%package tools-debuginfo
Summary: Debug information for package kernel-tools
Group: Development/Debug
Requires: %{name}-debuginfo-common-%{_target_cpu} = %{?epoch:%{epoch}:}%{version}-%{release}
AutoReqProv: no
%namespaced_pkg_conflicts kernel-tools-debuginfo
%description tools-debuginfo
This package provides debug information for package kernel-tools.

# Note that this pattern only works right to match the .build-id
# symlinks because of the trailing nonmatching alternation and
# the leading .*, because of find-debuginfo.sh's buggy handling
# of matching the pattern against the symlinks file.
%{expand:%%global _find_debuginfo_opts %{?_find_debuginfo_opts} -p '.*%%{_bindir}/(centrino-decode|turbostat|x86_energy_perf_policy|powernow-k8-decode|cpupower)(\.debug)?|.*%%{_libdir}/libcpupower.*|XXX' -o kernel-tools-debuginfo.list}
%endif

%if %{with_bpftool}

%package -n bpftool%{kbasever}
Summary: Inspection and simple manipulation of eBPF programs and maps
License: GPLv2
%namespaced_pkg_conflicts bpftool
%description -n bpftool%{kbasever}
This package contains the bpftool, which allows inspection and simple
manipulation of eBPF programs and maps.

%package -n bpftool%{kbasever}-debuginfo
Summary: Debug information for package bpftool
Group: Development/Debug
Requires: %{name}-debuginfo-common-%{_target_cpu} = %{?epoch:%{epoch}:}%{version}-%{release}
AutoReqProv: no
%namespaced_pkg_conflicts bpftool-debuginfo
%description -n bpftool%{kbasever}-debuginfo
This package provides debug information for the bpftool package.

%{expand:%%global _find_debuginfo_opts %{?_find_debuginfo_opts} -p '.*%%{_sbindir}/bpftool(\.debug)?|XXX' -o bpftool-debuginfo.list}

# with_bpftool
%endif

%if %{with_libbpf}

%package libbpf
Summary: Libbpf library
License: LGPLv2 or BSD
Provides: libbpf = %{libbpf_version}
%namespaced_pkg_conflicts kernel-libbpf
%description libbpf
This package contains the libbpf library built from kernel sources. 

%package libbpf-devel
Summary: Development files for libbpf
Requires: kernel-headers >= %{?epoch:%{epoch}:}%{kversion}
Requires: zlib
Provides: libbpf-devel = %{libbpf_version}
%namespaced_pkg_conflicts kernel-libbpf-devel
%description libbpf-devel
The libbpf-devel package contains libraries header files for
developing applications that use libbpf

%package libbpf-static
Summary: Static library for libbpf development
Provides: libbpf-static = %{libbpf_version}
%namespaced_pkg_conflicts kernel-libbpf-static
%description libbpf-static
The libbpf-static package contains static library for
developing applications that use libbpf

%if %{with_debuginfo}
%package libbpf-debuginfo
Summary: Debug information for package kernel-libbpf
Group: Development/Debug
Requires: %{name}-debuginfo-common-%{_target_cpu} = %{?epoch:%{epoch}:}%{version}-%{release}
AutoReqProv: no
%namespaced_pkg_conflicts kernel-libbpf-debuginfo
%description libbpf-debuginfo
This package provides debug information for the bpftool package.

%{expand:%%global _find_debuginfo_opts %{?_find_debuginfo_opts} -p '.*%%{_libdir}/libbpf.so(.1|.%{libbpf_version})?(\.debug)?|XXX' -o kernel-libbpf-debuginfo.list}
%endif

# with_libbpf
%endif

%if %{with_mods_extra}
%package modules-extra-common
Summary: Common files for the kernel modules extra package
Group: System Environment/Kernel
%namespaced_pkg_conflicts kernel-modules-extra-common
%description modules-extra-common
This package provides some global configuration files used to ensure
that some of the modules in the kernel-modules-extra package are
properly loaded at boot time.
%endif

%if %{with_configs_only}
%package configs
Summary: Amazon Linux Kernel configs
License: GPLv2
%description configs
Tiny package to generate kernel configs in a clean environment by koji. Not for production use.
%endif

#
# This macro creates a kernel-<subpackage>-debuginfo package.
#	%%kernel_debuginfo_package <subpackage>
#
%define kernel_debuginfo_package() \
%package %{?1:%{1}-}debuginfo\
Summary: Debug information for package %{name}%{?1:-%{1}}\
Group: Development/Debug\
Requires: %{name}-debuginfo-common-%{_target_cpu} = %{?epoch:%{epoch}:}%{version}-%{release}\
Provides: %{name}%{?1:-%{1}}-debuginfo-%{_target_cpu} = %{?epoch:%{epoch}:}%{version}-%{release}\
AutoReqProv: no\
%description -n %{name}%{?1:-%{1}}-debuginfo\
This package provides debug information for package %{name}%{?1:-%{1}}.\
This is required to use SystemTap with %{name}%{?1:-%{1}}-%{KVERREL}.\
%{expand:%%global _find_debuginfo_opts %{?_find_debuginfo_opts} %{?_find_debuginfo_opts_btf} -p '/.*/%%{KVERREL}%{?1:\.%{1}}/.*|/.*%%{KVERREL}%{?1:\.%{1}}(\.debug)?' -o debuginfo%{?1}.list}\
%{nil}

#
# This macro creates a kernel-<subpackage>-devel package.
#	%%kernel_devel_package <subpackage> <pretty-name>
#
%define kernel_devel_package() \
%package %{?1:%{1}-}devel\
Summary: Development package for building kernel modules to match the %{?2:%{2} }kernel\
Group: System Environment/Kernel\
Provides: kernel%{?1:-%{1}}-devel-%{_target_cpu} = %{?epoch:%{epoch}:}%{version}-%{release}\
Provides: kernel-devel-%{_target_cpu} = %{?epoch:%{epoch}:}%{version}-%{release}%{?1:.%{1}}\
Provides: kernel-devel = %{?epoch:%{epoch}:}%{version}-%{release}%{?1:.%{1}}\
Provides: kernel-devel-uname-r = %{KVERREL}%{?1:.%{1}}\
Provides: installonlypkg(kernel)\
%obsolete_released_6_12_packages kernel-devel\
AutoReqProv: no\
%if 0%{?amzn} < 2022\
Requires(pre): %{_bindir}/find\
Requires(post): %{_sbindir}/hardlink\
Requires: gcc10\
%else\
Requires: gcc >= 10\
%endif\
Requires: perl\
Requires: elfutils-libelf-devel\
%if  "%{_gccver}" > "7"\
Provides: buildrequires(gcc) = %{_gccver}\
%endif\
%description %{?variant:%{variant}-}%{?1:%{1}-}devel\
This package provides kernel headers and makefiles sufficient to build modules\
against the %{?2:%{2} }kernel package.\
%{nil}

#
# This macro creates a kernel-<subpackage>-modules-extra package.
#	%%kernel_modules_extra_package [-m] <subpackage> <pretty-name>
#
%define kernel_modules_extra_package() \
%package %{?1:%{1}-}modules-extra\
Summary: Extra kernel modules to match the %{?2:%{2} }kernel\
Provides: kernel%{?1:-%{1}}-modules-extra-%{_target_cpu} = %{?epoch:%{epoch}:}%{version}-%{release}\
Provides: kernel%{?1:-%{1}}-modules-extra-%{_target_cpu} = %{?epoch:%{epoch}:}%{version}-%{release}%{?1:.%{1}}\
Provides: kernel%{?1:-%{1}}-modules-extra = %{?epoch:%{epoch}:}%{version}-%{release}%{?1:.%{1}}\
Provides: installonlypkg(kernel-module)\
Provides: kernel%{?1:-%{1}}-modules-extra-uname-r = %{KVERREL}%{?1:+%{1}}\
Provides: bundled(v4l2loopback) = v0.13.2\
Requires: kernel-uname-r = %{KVERREL}%{?1:+%{1}}\
Requires: kernel-modules-extra-common >= 6.12.31-35.92.amzn2023\
AutoReq: no\
AutoProv: yes\
%description %{?1:%{1}-}modules-extra\
This package provides less commonly used kernel modules for the %{?2:%{2} }kernel package.\
%{nil}


#
# This macro creates a kernel-<subpackage> and its -devel and -debuginfo too.
#	%%define variant_summary The Linux kernel compiled for <configuration>
#	%%kernel_variant_package [-n <pretty-name>] <subpackage>
#
%define kernel_variant_package(n:) \
%package %1\
Summary: %{variant_summary}\
Group: System Environment/Kernel\
%kernel_reqprovconf\
%{expand:%%kernel_devel_package %1 %{!?-n:%1}%{?-n:%{-n*}}}\
%if %{with_mods_extra}\
%{expand:%%kernel_modules_extra_package %{!?-n:%1}%{?-n:%{-n*}}}\
%endif\
%{expand:%%kernel_debuginfo_package %1}\
%{nil}


# First the auxiliary packages of the main kernel package.
%kernel_devel_package
%if %{with_mods_extra}
%kernel_modules_extra_package
%endif
%kernel_debuginfo_package


# Now, each variant package.

%define variant_summary The Linux kernel compiled with extra debugging enabled
%kernel_variant_package debug
%description debug
The kernel package contains the Linux kernel (vmlinuz), the core of any
Linux operating system.  The kernel handles the basic functions
of the operating system:  memory allocation, process allocation, device
input and output, etc.

This variant of the kernel has numerous debugging options enabled.
It should only be installed when trying to gather additional information
on kernel bugs, as some of these options impact performance noticably.


%prep
# more sanity checking; do it quietly
if [ "%{patches}" != "%%{patches}" ] ; then
  for patch in %{patches} ; do
    if [ ! -f $patch ] ; then
      echo "ERROR: Patch  ${patch##/*/}  listed in specfile but is missing"
      exit 1
    fi
  done
fi 2>/dev/null

patch_command='patch -p1 -F1 -s'

ApplyNoCheckPatch()
{
  local patch=$1
  shift
  case "$patch" in
    *.bz2) bunzip2 < "$RPM_SOURCE_DIR/$patch" | $patch_command ${1+"$@"} ;;
    *.gz) gunzip < "$RPM_SOURCE_DIR/$patch" | $patch_command ${1+"$@"} ;;
    *) $patch_command ${1+"$@"} < $patch ;;
  esac
}

ApplyPatch()
{
  local patch=$1
  shift
  if [ ! -f $RPM_SOURCE_DIR/$patch ]; then
    exit 1
  fi
  if ! grep -E "^Patch[0-9]+: $patch\$" %{_specdir}/${RPM_PACKAGE_NAME%%%%%{?variant}}.spec ; then
    if [ "${patch:0:8}" != "patch-3." ] ; then
      echo "ERROR: Patch  $patch  not listed as a source patch in specfile"
      exit 1
    fi
  fi 2>/dev/null
  case "$patch" in
  *.bz2) bunzip2 < "$RPM_SOURCE_DIR/$patch" | $patch_command ${1+"$@"} ;;
  *.gz) gunzip < "$RPM_SOURCE_DIR/$patch" | $patch_command ${1+"$@"} ;;
  *) $patch_command ${1+"$@"} < "$RPM_SOURCE_DIR/$patch" ;;
  esac
}

# don't apply patch if it's empty
ApplyOptionalPatch()
{
  local patch=$1
  shift
  if [ ! -f $RPM_SOURCE_DIR/$patch ]; then
    exit 1
  fi
  local C=$(wc -l $RPM_SOURCE_DIR/$patch | awk '{print $1}')
  if [ "$C" -gt 9 ]; then
    ApplyPatch $patch ${1+"$@"}
  fi
}

# First we unpack the kernel tarball.
# If this isn't the first make prep, we use links to the existing clean tarball
# which speeds things up quite a bit.

# Update to latest upstream.
%define vanillaversion %{kversion}

# %%{vanillaversion} : the full version name, e.g. 2.6.35-rc6-git3
# %%{kversion}       : the base version, e.g. 2.6.34

# Use kernel-%%{kversion}%%{?dist} as the top-level directory name
# so we can prep different trees within a single git directory.

%setup -q -n kernel-%{kversion}%{?dist} -c
mv linux-%{vanillaversion} vanilla-%{vanillaversion}

%if "%{kversion}" != "%{vanillaversion}"
# Need to apply patches to the base vanilla version.
pushd vanilla-%{vanillaversion} && popd

%endif

# Now build the fedora kernel tree.
if [ -d linux-%{KVERREL} ]; then
  # Just in case we ctrl-c'd a prep already
  rm -rf deleteme.%{_target_cpu}
  # Move away the stale away, and delete in background.
  mv linux-%{KVERREL} deleteme.%{_target_cpu}
  rm -rf deleteme.%{_target_cpu} &
fi

cp -rl vanilla-%{vanillaversion} linux-%{KVERREL}

cd linux-%{KVERREL}
tar xf %{SOURCE1}

# Drop some necessary files from the source dir into the buildroot
cp $RPM_SOURCE_DIR/config-* .
cp %{SOURCE15} .

%ifnarch %nobuildarches
# Dynamically generate kernel .config files from config-* files
make KARCH=%{_target_cpu} -f %{SOURCE19} VERSION=%{version} config
%endif

# apply the patches we had included in the -patches tarball. We use the
# linux-KVER-patches.list hardcoded apply log filename
patch_list=linux-%{kversion}-patches.list
if [ ! -f ${patch_list} ] ; then
    echo "ERROR: patch file apply log is missing: ${patch_list} not found"
    exit -1
fi
for p in `cat $patch_list` ; do
  ApplyNoCheckPatch ${p}
done

# __APPLYFILE_TEMPLATE__
ApplyPatch 0001-Sysfs-memory-probe-interface.patch
ApplyPatch 0002-arm64-mm-Enable-sysfs-based-memory-hot-remove-probe.patch
ApplyPatch 0003-memory-fix-offline_and_remove_memory-use.patch
ApplyPatch 0004-drivers-base-memory-use-MHP_MEMMAP_ON_MEMORY-from-th.patch
ApplyPatch 0005-mm-add-offline-page-reporting-interface.patch
ApplyPatch 0006-virtio-add-hack-to-allow-pre-mapped-scatterlists.patch
ApplyPatch 0007-virtio-balloon-optionally-report-offlined-memory-ran.patch
ApplyPatch 0008-Introduce-page-touching-DMA-ops-binding.patch
ApplyPatch 0009-Correct-read-overflow-in-page-touching-DMA-ops-bindi.patch
ApplyPatch 0010-Enable-ptIOMMU-for-all-supported-platforms.patch
ApplyPatch 0011-drivers-introduce-AMAZON_DRIVER_UPDATES.patch
ApplyPatch 0012-drivers-Add-amazon-drivers-for-EFA-ENA-and-igb_uio.patch
ApplyPatch 0013-drivers-amazon-net-ena-config-Add-ENA_HAVE_ETHTOOL_R.patch
ApplyPatch 0014-AL2023-6.1-Update-ena-driver-to-2.12.3g.patch
ApplyPatch 0015-drivers-amazon-net-ena-ena_xdp-Use-napi_alloc_skb.patch
ApplyPatch 0016-drivers-amazon-net-ena-ena_xdp-Fix-build-failure-due.patch
ApplyPatch 0017-dma-Automatically-enable-page-touching-on-Caspian.patch
ApplyPatch 0018-ena-efa-fixes-for-kernel-6.11.patch
ApplyPatch 0019-TEMPORARILY-Revert-arm64-Kconfig-Enable-hotplug-CPU-.patch
ApplyPatch 0020-perf-x86-amd-core-Don-t-unfreeze-LBR.patch
ApplyPatch 0021-efa-fix-to-account-for-upstream-change.patch
ApplyPatch 0022-page_touching-select-ARCH_HAS_DMA_OPS.patch
ApplyPatch 0023-AL2023-6.12-Update-EFA-driver-to-2.13.1.patch
ApplyPatch 0024-Config-glue-for-Lustre-client.patch
ApplyPatch 0025-Lustre-client-support-for-6.12-kernel.patch
ApplyPatch 0026-xen-manage-keep-track-of-the-on-going-suspend-mode.patch
ApplyPatch 0027-xen-manage-introduce-helper-function-to-know-the-on-.patch
ApplyPatch 0028-xenbus-add-freeze-thaw-restore-callbacks-support.patch
ApplyPatch 0029-x86-xen-Introduce-new-function-to-map-HYPERVISOR_sha.patch
ApplyPatch 0030-x86-xen-add-system-core-suspend-and-resume-callbacks.patch
ApplyPatch 0031-xen-blkfront-add-callbacks-for-PM-suspend-and-hibern.patch
ApplyPatch 0032-xen-netfront-add-callbacks-for-PM-suspend-and-hibern.patch
ApplyPatch 0033-xen-time-introduce-xen_-save-restore-_steal_clock.patch
ApplyPatch 0034-x86-xen-save-and-restore-steal-clock.patch
ApplyPatch 0035-xen-events-add-xen_shutdown_pirqs-helper-function.patch
ApplyPatch 0036-x86-xen-close-event-channels-for-PIRQs-in-system-cor.patch
ApplyPatch 0037-PM-hibernate-update-the-resume-offset-on-SNAPSHOT_SE.patch
ApplyPatch 0038-Revert-xen-dont-fiddle-with-event-channel-masking-in.patch
ApplyPatch 0039-xen-blkfront-Fixed-blkfront_restore-to-remove-a-call.patch
ApplyPatch 0040-x86-tsc-avoid-system-instability-in-hibernation.patch
ApplyPatch 0041-block-xen-blkfront-consider-new-dom0-features-on-res.patch
ApplyPatch 0042-xen-restore-pirqs-on-resume-from-hibernation.patch
ApplyPatch 0043-xen-Only-restore-the-ACPI-SCI-interrupt-in-xen_resto.patch
ApplyPatch 0044-xen-netfront-call-netif_device_attach-on-resume.patch
ApplyPatch 0045-xen-Restore-xen-pirqs-on-resume-from-hibernation.patch
ApplyPatch 0046-block-xen-blkfront-bump-the-maximum-number-of-indire.patch
ApplyPatch 0047-Revert-xen-x2apic-enable-x2apic-mode-when-supported-.patch
ApplyPatch 0048-x86-Disable-KASLR-when-Xen-is-detected.patch
ApplyPatch 0049-media-Import-v4l2loopback-v0.13.2.patch
ApplyPatch 0050-AL2023-6.12-Update-ena-driver-to-2.13.2g.patch
ApplyPatch 0051-arm64-Export-acpi_psci_use_hvc-symbol.patch
ApplyPatch 0052-hwrng-Add-Gravition-RNG-driver.patch
ApplyPatch 0053-arm64-pt_regs-assert-pt_regs-is-a-multiple-of-16-byt.patch
ApplyPatch 0054-arm64-pt_regs-remove-stale-big-endian-layout.patch
ApplyPatch 0055-arm64-pt_regs-rename-pmr_save-pmr.patch
ApplyPatch 0056-arm64-pt_regs-swap-unused-and-pmr-fields.patch
ApplyPatch 0057-arm64-use-a-common-struct-frame_record.patch
ApplyPatch 0058-arm64-stacktrace-move-dump_backtrace-to-kunwind_stac.patch
ApplyPatch 0059-arm64-stacktrace-report-source-of-unwind-data.patch
ApplyPatch 0060-arm64-stacktrace-report-recovered-PCs.patch
ApplyPatch 0061-arm64-stacktrace-split-unwind_consume_stack.patch
ApplyPatch 0062-arm64-stacktrace-unwind-exception-boundaries.patch
ApplyPatch 0063-arm64-stacktrace-Skip-reporting-LR-at-exception-boun.patch
ApplyPatch 0064-arm64-stacktrace-Don-t-WARN-when-unwinding-other-tas.patch
ApplyPatch 0065-acpi-Support-CONFIG_ACPI-without-CONFIG_PCI.patch
ApplyPatch 0066-ip-Bump-default-ttl-to-127.patch
ApplyPatch 0067-ptp-Add-support-for-the-AMZNC10C-vmclock-device.patch
ApplyPatch 0068-ptp-vmclock-Add-.owner-to-vmclock_miscdev_fops.patch
ApplyPatch 0069-ptp-vmclock-Set-driver-data-before-its-usage.patch
ApplyPatch 0070-ptp-vmclock-Don-t-unregister-misc-device-if-it-was-n.patch
ApplyPatch 0071-ptp-vmclock-Clean-up-miscdev-and-ptp-clock-through-d.patch
ApplyPatch 0072-ptp-vmclock-Remove-goto-based-cleanup-logic.patch
ApplyPatch 0073-Revert-memcg-use-ratelimited-stats-flush-in-the-recl.patch
ApplyPatch 0074-KEYS-Make-use-of-platform-keyring-for-module-signatu.patch
ApplyPatch 0075-scripts-sign_file-Add-option-to-keep-signing-certifi.patch
ApplyPatch 0076-AL2023-6.12-Update-lustre-and-lnet-to-2.15.6-fsx16-c.patch
ApplyPatch 0077-AL2023-6.12-Update-lustrefsx-to-2.15.6-fsx18-commit.patch
ApplyPatch 0078-asm-generic-introduce-text-patching.h.patch
ApplyPatch 0079-arm64-patching-Rename-aarch64_insn_copy-to-text_poke.patch
ApplyPatch 0080-arm64-module-Use-text-poke-API-for-late-relocations.patch
ApplyPatch 0081-AL2023-6.12-Update-ena-driver-to-2.14.1g.patch
ApplyPatch 0082-Enable-Algorithims-for-Amazon-Linux-6.1.y.patch
ApplyPatch 0083-crypto-ecdh-zeroize-crpytographic-keys-after-use.patch
ApplyPatch 0084-random-Add-hook-to-override-device-reads-and-getrand.patch
ApplyPatch 0085-crypto-rng-Override-drivers-char-random-in-FIPS-mode.patch
ApplyPatch 0086-crypto-Only-allow-GCM-in-FIPS-when-instantiated-via-.patch
ApplyPatch 0087-random-allow-reseeding-DRBG-with-getrandom.patch
ApplyPatch 0088-crypto-rng-Use-a-different-crypto_rng-for-reseeding.patch
ApplyPatch 0089-crypto-dh-Add-SP800-56A-rev-3-Pair-wise-Consistency-.patch
ApplyPatch 0090-crypto-ecc-Add-SP800-56A-rev-3-Pair-wise-Consistency.patch
ApplyPatch 0091-crypto-ecc-Remove-flipping-of-private-key-in-selftes.patch
ApplyPatch 0092-Override-drivers-char-random-only-after-FIPS-mode-RN.patch
ApplyPatch 0093-virtio-break-and-reset-virtio-devices-on-device_shut.patch
ApplyPatch 0094-virtgpu-don-t-reset-on-shutdown.patch
ApplyPatch 0095-ublk-fix-race-between-io_uring_cmd_complete_in_task-.patch
ApplyPatch 0096-AL2023-6.12-Update-lustrefsx-to-2.15.6-fsx19-commit.patch
ApplyPatch 0097-net-Change-IPv4-6-IP-fragmentation-waiting-time-to-1.patch
ApplyPatch 0098-jfs-fix-array-index-out-of-bounds-read-in-add_missin.patch
ApplyPatch 0099-exfat-fix-double-free-in-delayed_free.patch
ApplyPatch 0100-crypto-rng-fix-incorrect-mutex-unlock-in-crypto_del_.patch
ApplyPatch 0101-Revert-mm-hugetlb-fix-huge_pmd_unshare-vs-GUP-fast-r.patch
ApplyPatch 0102-AL2023-6.12-Update-EFA-driver-to-2.17.2.patch
ApplyPatch 0103-Updating-lustrefsx-to-2.15.6.patch
ApplyPatch 0104-mm-damon-core-prevent-unnecessary-overflow-in-damos_.patch
ApplyPatch 0105-net-mlx5-Introduce-data-placement-ordering-bits.patch
ApplyPatch 0106-RDMA-mlx5-Support-OOO-RX-WQE-consumption.patch
ApplyPatch 0107-RDMA-mlx5-Support-querying-per-plane-IB-PortCounters.patch
ApplyPatch 0108-net-sched-Fix-backlog-accounting-in-qdisc_dequeue_in.patch
ApplyPatch 0109-arm64-stacktrace-Implement-arch_stack_walk_reliable.patch
ApplyPatch 0110-arm64-Implement-HAVE_LIVEPATCH.patch
ApplyPatch 0111-net-mlx5-HWS-Fix-memory-leak-in-hws_pool_buddy_init-.patch
ApplyPatch 0112-AL2023-6.12-Update-ena-driver-to-2.15.0g.patch
ApplyPatch 0113-drivers-media-v4l2loopback-ingest-version-0.15.1.patch
ApplyPatch 0114-vfio-pci-enable-mmap-ing-ena-device.patch
ApplyPatch 0115-crypto-rng-Remove-reseeding-call.patch
ApplyPatch 0116-AL2023-6.12-Update-lustrefsx-to-2.15.6-fsx23-commit.patch
ApplyPatch 0117-drivers-amazon-net-Update-igb_uio.patch
ApplyPatch 0118-AL2023-6.12-Update-lustrefsx-to-2.15.6-fsx25-commit.patch
ApplyPatch 0119-Revert-sched-fair-Proportional-newidle-balance.patch
ApplyPatch 0120-AL2023-6.12-Update-ena-driver-to-2.16.1g.patch
ApplyPatch 0121-iommu-Skip-PASID-validation-for-devices-without-PASI.patch
ApplyPatch 0122-AL2023-6.12-Update-lustrefsx-to-2.15.6-fsx27-commit.patch

# Any further pre-build tree manipulations happen here.

chmod +x scripts/checkpatch.pl

touch .scmversion

# Mangle /usr/bin/python shebangs to /usr/bin/python3
# Mangle all Python shebangs to be Python 3 explicitly
# -p preserves timestamps
# -n prevents creating ~backup files
# -i specifies the interpreter for the shebang
# This fixes errors such as
# *** ERROR: ambiguous python shebang in /usr/bin/kvm_stat: #!/usr/bin/python. Change it to python3 (or python2) explicitly.
# We patch all sources below for which we got a report/error.
pathfix.py -i "%{__python3} %{py3_shbang_opts}" -p -n \
      tools/kvm/kvm_stat/kvm_stat \
      scripts/show_delta \
      scripts/diffconfig \
      scripts/bloat-o-meter \
      scripts/jobserver-exec \
      scripts/tracing/draw_functrace.py \
      scripts/spdxcheck.py \
      tools \
      Documentation \
      scripts/clang-tools

# only deal with configs if we are going to build for the arch
%ifnarch %nobuildarches

mkdir configs

# Remove configs not for the buildarch
for cfg in kernel-%{version}-*.config; do
  if [ `echo %{all_arch_configs} | grep -c $cfg` -eq 0 ]; then
    rm -f $cfg
  fi
done

%if !%{debugbuildsenabled}
rm -f kernel-%{version}-*debug.config
%endif

%if 0%{?amzn} >= 2022
%global make_defines CC=gcc HOSTCC=gcc HOSTCXX=g++
%else
%global make_defines CROSS_COMPILE=%{GCC_VER} CC=%{GCC_VER}gcc HOSTCC=%{GCC_VER}gcc HOSTCXX=%{GCC_VER}g++ LD=%{GCC_VER}ld.bfd
%endif

# now run oldconfig over all the config files
for i in *.config
do
  mv $i .config

  Arch=`head -1 .config | cut -b 3-`
%if %{with_oldconfig}
  make ARCH=$Arch %{oldconfig_target} %{?make_defines}
%endif
  echo "# $Arch" > configs/$i
  cat .config >> configs/$i
done
# end of kernel config
%endif

# get rid of unwanted files resulting from patch fuzz
find . \( -name "*.orig" -o -name "*~" \) -exec rm -f {} \; >/dev/null

cd ..

###
### build
###
%build

%if %{with_sparse}
%define sparse_mflags	C=1
%endif

cp_vmlinux()
{
  eu-strip --remove-comment -o "$2" "$1"
}

export CC=%{?_gcc}%{?!_gcc:gcc}
export HOSTCC=%{?_gcc}%{?!_gcc:gcc}
export HOSTCXX=%{?_gxx}%{?!_gxx:g++}

export KBUILD_BUILD_HOST=$(hostname --short)

BuildKernel() {
    MakeTarget=$1
    KernelImage=$2
    Flavour=$3
    Flav=${Flavour:+.${Flavour}}
    InstallName=${4:-vmlinuz}

    # Pick the right config file for the kernel we're building
    Config=kernel-%{version}-%{_target_cpu}${Flavour:+-${Flavour}}.config
    DevelDir=/usr/src/kernels/%{KVERREL}${Flav}

    # When the bootable image is just the ELF kernel, strip it.
    # We already copy the unstripped file into the debuginfo package.
    if [ "$KernelImage" = vmlinux ]; then
      CopyKernel=cp_vmlinux
    else
      CopyKernel=cp
    fi

    KernelVer=%{version}-%{release}.%{_target_cpu}${Flav}
    echo BUILDING A KERNEL FOR ${Flavour} %{_target_cpu}...

    # make sure EXTRAVERSION says what we want it to say
    perl -p -i -e "s/^EXTRAVERSION.*/EXTRAVERSION = -%{release}.%{_target_cpu}${Flav}/" Makefile

    # and now to start the build process

    make -s mrproper %{?make_defines} 
    cp configs/$Config .config

%if %{signmodules}%{signkernel}
    cp %{SOURCE11} certs/.
%endif

    Arch=`head -1 .config | cut -b 3-`
    echo USING ARCH=$Arch

    make -s ARCH=$Arch %{oldconfig_target} %{?make_defines} > /dev/null

     # This ensures build-ids are unique to allow parallel debuginfo
     perl -p -i -e "s/^CONFIG_BUILD_SALT.*/CONFIG_BUILD_SALT=\"%{KVERREL}\"/" .config

    make -s ARCH=$Arch V=1 %{?_smp_mflags} $MakeTarget %{?sparse_mflags} %{?make_defines}
    make -s ARCH=$Arch V=1 %{?_smp_mflags} modules %{?sparse_mflags} %{?make_defines} || exit 1

    # Start installing the results
%if %{with_debuginfo}
    mkdir -p $RPM_BUILD_ROOT%{debuginfodir}/boot
    mkdir -p $RPM_BUILD_ROOT%{debuginfodir}/%{image_install_path}
%endif
    mkdir -p $RPM_BUILD_ROOT/%{image_install_path}
    install -m 644 .config $RPM_BUILD_ROOT/boot/config-$KernelVer
    install -m 644 System.map $RPM_BUILD_ROOT/boot/System.map-$KernelVer

%if 0%{?amzn} >= 2022
    mkdir -p $RPM_BUILD_ROOT/lib/modules/$KernelVer
    install -m 644 .config $RPM_BUILD_ROOT/lib/modules/$KernelVer/config
    install -m 644 System.map $RPM_BUILD_ROOT/lib/modules/$KernelVer/System.map
%endif

    # We estimate the size of the initramfs because rpm needs to take this size
    # into consideration when performing disk space calculations. (See bz #530778)
    dd if=/dev/zero of=$RPM_BUILD_ROOT/boot/initramfs-$KernelVer.img bs=1M count=20

    if [ -f arch/$Arch/boot/zImage.stub ]; then
      cp arch/$Arch/boot/zImage.stub $RPM_BUILD_ROOT/%{image_install_path}/zImage.stub-$KernelVer || :
%if 0%{?amzn} >= 2022
      cp arch/$Arch/boot/zImage.stub $RPM_BUILD_ROOT/lib/modules/$KernelVer/zImage.stub-$KernelVer || :
%endif
    fi
%if %{signkernel}
    if [ "$KernelImage" = vmlinux ]; then
        # We can't strip and sign $KernelImage in place, because
        # we need to preserve original vmlinux for debuginfo.
        # Use a copy for signing.
        $CopyKernel $KernelImage $KernelImage.tosign
        KernelImage=$KernelImage.tosign
        CopyKernel=cp
    fi

    # Sign the image if we're using EFI
    # aarch64 kernels are gziped EFI images
    KernelExtension=${KernelImage##*.}
    if [ "$KernelExtension" == "gz" ]; then
        SignImage=${KernelImage%.*}
    else
        SignImage=$KernelImage
    fi

%ifarch x86_64 aarch64
    %pesign -s -i $SignImage -o vmlinuz.signed
%endif

    if [ ! -s vmlinuz.signed ]; then
        echo "pesigning failed"
        exit 1
    fi
    mv vmlinuz.signed $SignImage
    if [ "$KernelExtension" == "gz" ]; then
        gzip -f9 $SignImage
    fi
# signkernel
%endif

    $CopyKernel $KernelImage \
    		$RPM_BUILD_ROOT/%{image_install_path}/$InstallName-$KernelVer
    chmod 755 $RPM_BUILD_ROOT/%{image_install_path}/$InstallName-$KernelVer
%if 0%{?amzn} >= 2022
    cp $RPM_BUILD_ROOT/%{image_install_path}/$InstallName-$KernelVer $RPM_BUILD_ROOT/lib/modules/$KernelVer/$InstallName
%endif

%if %{with_fips}
    #hmac sign the kernel for FIPS
    echo "Creating hmac file: $RPM_BUILD_ROOT/%{image_install_path}/.vmlinuz-$KernelVer.hmac"
    ls -l $RPM_BUILD_ROOT/%{image_install_path}/$InstallName-$KernelVer
    sha512hmac $RPM_BUILD_ROOT/%{image_install_path}/$InstallName-$KernelVer | sed -e "s,$RPM_BUILD_ROOT,," >  $RPM_BUILD_ROOT/%{image_install_path}/.vmlinuz-$KernelVer.hmac
%if 0%{?amzn} >= 2022
    cp $RPM_BUILD_ROOT/%{image_install_path}/.vmlinuz-$KernelVer.hmac $RPM_BUILD_ROOT/lib/modules/$KernelVer/.vmlinuz.hmac
%endif
%endif

    # Override $(mod-fw) because we don't want it to install any firmware
    # we'll get it from the linux-firmware package and we don't want conflicts
    make -s ARCH=$Arch INSTALL_MOD_PATH=$RPM_BUILD_ROOT modules_install KERNELRELEASE=$KernelVer mod-fw= %{?make_defines}

%ifarch %{vdso_arches}
    make -s ARCH=$Arch INSTALL_MOD_PATH=$RPM_BUILD_ROOT vdso_install KERNELRELEASE=$KernelVer %{?make_defines}
%endif

    # And save the headers/makefiles etc for building modules against
    #
    # This all looks scary, but the end result is supposed to be:
    # * all arch relevant include/ files
    # * all Makefile/Kconfig files
    # * all script/ files

    rm -f $RPM_BUILD_ROOT/lib/modules/$KernelVer/build
    rm -f $RPM_BUILD_ROOT/lib/modules/$KernelVer/source
    mkdir -p $RPM_BUILD_ROOT/lib/modules/$KernelVer/build
    (cd $RPM_BUILD_ROOT/lib/modules/$KernelVer ; ln -s build source)
    # dirs for additional modules per module-init-tools, kbuild/modules.txt
    mkdir -p $RPM_BUILD_ROOT/lib/modules/$KernelVer/extra
    mkdir -p $RPM_BUILD_ROOT/lib/modules/$KernelVer/updates
    mkdir -p $RPM_BUILD_ROOT/lib/modules/$KernelVer/weak-updates
    # first copy everything
    cp --parents `find  -type f -name "Makefile*" -o -name "Kconfig*"` $RPM_BUILD_ROOT/lib/modules/$KernelVer/build
    cp Module.symvers $RPM_BUILD_ROOT/lib/modules/$KernelVer/build
    gzip -c9 Module.symvers >  $RPM_BUILD_ROOT/boot/symvers-$KernelVer.gz
%if 0%{?amzn} >= 2022
    cp $RPM_BUILD_ROOT/boot/symvers-$KernelVer.gz $RPM_BUILD_ROOT/lib/modules/$KernelVer/symvers.gz
%endif
    cp System.map $RPM_BUILD_ROOT/lib/modules/$KernelVer/build
    if [ -s Module.markers ]; then
      cp Module.markers $RPM_BUILD_ROOT/lib/modules/$KernelVer/build
    fi
    # then drop all but the needed Makefiles/Kconfig files
    rm -rf $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/Documentation
    rm -rf $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/scripts
    rm -rf $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/include
    cp .config $RPM_BUILD_ROOT/lib/modules/$KernelVer/build
    if [ -f tools/objtool/objtool ]; then
      cp -a tools/objtool/objtool $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/tools/objtool/ || :
    fi
    cp -a scripts $RPM_BUILD_ROOT/lib/modules/$KernelVer/build
    if [ -d arch/$Arch/scripts ]; then
      cp -a arch/$Arch/scripts $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/arch/%{_arch} || :
    fi
    if [ -f arch/$Arch/*lds ]; then
      cp -a arch/$Arch/*lds $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/arch/%{_arch}/ || :
    fi
    if [ -f arch/%{asmarch}/kernel/module.lds ]; then
      cp -a --parents arch/%{asmarch}/kernel/module.lds $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/
    fi
    rm -f $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/scripts/*.o
    rm -f $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/scripts/*/*.o
    if [ -d arch/%{asmarch}/include ]; then
      cp -a --parents arch/%{asmarch}/include $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/
    fi
    cp -a include $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/include
%if 0%{?amzn} < 2022
    #Use a wrapper Makefile so modules compile with gcc10
    mv $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/Makefile $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/Makefile.kernel
    cp $RPM_SOURCE_DIR/Makefile.module $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/Makefile
%endif


    # newer kernels relocate these from under include/linux to
    # include/generated.... Maintain compatibility with old(er) code looking
    # for former files in the formerly valid location
    pushd  $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/include/linux
    test -s utsrelease.h        || ln -sf ../generated/utsrelease.h .
    test -s autoconf.h          || ln -sf ../generated/autoconf.h .
    test -s version.h           || ln -sf ../generated/uapi/linux/version.h .
    popd

    # Make sure the Makefile, version.h, and auto.conf have a matching
    # timestamp so that external modules can be built
    touch -r $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/Makefile \
        $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/include/generated/uapi/linux/version.h \
        $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/include/config/auto.conf
%if 0%{?amzn} < 2022
    touch -r $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/Makefile $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/Makefile.kernel
%endif
    touch -r $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/.config $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/include/linux/autoconf.h
    
%if %{with_debuginfo}
    eu-readelf -n vmlinux | grep "Build ID" | awk '{print $NF}' > vmlinux.id
    cp vmlinux.id $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/vmlinux.id
    #
    # save the vmlinux file for kernel debugging into the kernel-debuginfo rpm
    #
    mkdir -p $RPM_BUILD_ROOT%{debuginfodir}/lib/modules/$KernelVer
    cp vmlinux $RPM_BUILD_ROOT%{debuginfodir}/lib/modules/$KernelVer
%endif

    find $RPM_BUILD_ROOT/lib/modules/$KernelVer -name "*.ko" -type f >modnames

    # mark modules executable so that strip-to-file can strip them
    xargs --no-run-if-empty chmod u+x < modnames

    # Generate a list of modules for block and networking.

    grep -F /drivers/ modnames | xargs --no-run-if-empty %{GCC_VER}nm -upA |
    sed -n 's,^.*/\([^/]*\.ko\):  *U \(.*\)$,\1 \2,p' > drivers.undef

    collect_modules_list()
    {
      sed -r -n -e "s/^([^ ]+) \\.?($2)\$/\\1/p" drivers.undef |
      LC_ALL=C sort -u > $RPM_BUILD_ROOT/lib/modules/$KernelVer/modules.$1
    }

    collect_modules_list networking \
                        'register_netdev|ieee80211_register_hw|usbnet_probe|phy_driver_register|rt(l_|2x00)(pci|usb)_probe|register_netdevice'
    collect_modules_list block \
                        'ata_scsi_ioctl|scsi_add_host|scsi_add_host_with_dma|blk_init_queue|register_mtd_blktrans|scsi_esp_register|scsi_register_device_handler|blk_queue_physical_block_size'
    collect_modules_list drm \
                        'drm_open|drm_init'
    collect_modules_list modesetting \
                        'drm_crtc_init'

    # detect missing or incorrect license tags
    rm -f modinfo
    while read i
    do
      echo -n "${i#$RPM_BUILD_ROOT/lib/modules/$KernelVer/} " >> modinfo
      %{_sbindir}/modinfo -l $i >> modinfo
    done < modnames

    grep -E -v \
    	  'GPL( v2)?$|Dual BSD/GPL$|Dual MPL/GPL$|GPL and additional rights$' \
	  modinfo && exit 1

    rm -f modinfo modnames

%if %{with_mods_extra}
    # Call the modules-extra script to move things around
    %{SOURCE17} $RPM_BUILD_ROOT lib/modules/$KernelVer %{SOURCE16}
%endif

%if %{signmodules}
    # Save off the modules.order file.  We'll use it in the
    # __debug_install_post macro below to sign the right things
    # Also save the signing keys so we actually sign the modules with the
    # right key.
    cp -v modules.order modules.order.sign${Flavour:+.${Flavour}}
    cp certs/signing_key.pem signing_key.pem.sign${Flavour:+.${Flavour}}
    cp certs/signing_key.x509 signing_key.x509.sign${Flavour:+.${Flavour}}
%endif

    # remove files that will be auto generated by depmod at rpm -i time
    for i in alias alias.bin builtin.bin ccwmap dep dep.bin ieee1394map inputmap isapnpmap ofmap pcimap seriomap symbols symbols.bin usbmap devname softdep
    do
      rm -f $RPM_BUILD_ROOT/lib/modules/$KernelVer/modules.$i
    done

    # Move the devel headers out of the root file system
    mkdir -p $RPM_BUILD_ROOT/usr/src/kernels
    mv $RPM_BUILD_ROOT/lib/modules/$KernelVer/build $RPM_BUILD_ROOT/$DevelDir
    ln -sf $DevelDir $RPM_BUILD_ROOT/lib/modules/$KernelVer/build

    # prune junk from kernel-devel
    find $RPM_BUILD_ROOT/usr/src/kernels -name ".*.cmd" -exec rm -f {} \;
}

###
# DO it...
###

# prepare directories
rm -rf $RPM_BUILD_ROOT
mkdir -p $RPM_BUILD_ROOT/boot
mkdir -p $RPM_BUILD_ROOT%{_libexecdir}
%if %{with_configs_only}
mkdir -p $RPM_BUILD_ROOT/configs
%endif

cd linux-%{KVERREL}

%if %{with_debug}
BuildKernel %make_target %kernel_image debug
%endif

%if %{with_up}
BuildKernel %make_target %kernel_image
%endif

# perf
%global perf_make \
  make %{?_smp_mflags} -C tools/perf -s V=1 EXTRA_CFLAGS="-Wno-error=array-bounds -Wno-error=format-overflow" HAVE_CPLUS_DEMANGLE=1 NO_LIBUNWIND=1 NO_GTK2=1 NO_LIBNUMA=1 NO_STRLCPY=1 prefix=%{_prefix} lib=%{_lib} PYTHON=%{__python} VF=1 %{?make_defines}
%if %{with_perf}
%{perf_make} all
%{perf_make} man || %{doc_build_fail}
%endif

%if %{with_tools}
%ifarch %{cpupowerarchs}
# cpupower
# make sure version-gen.sh is executable.
chmod +x tools/power/cpupower/utils/version-gen.sh
make %{?_smp_mflags} -C tools/power/cpupower CPUFREQ_BENCH=false %{?make_defines}
%ifarch %{ix86}
    pushd tools/power/cpupower/debug/i386
    make %{?_smp_mflags} centrino-decode powernow-k8-decode
    popd
%endif
%ifarch x86_64
    pushd tools/power/cpupower/debug/x86_64
    make %{?_smp_mflags} centrino-decode powernow-k8-decode
    popd
%endif
%ifarch %{ix86} x86_64
   pushd tools/power/x86/x86_energy_perf_policy/
   make %{?make_defines}
   popd
   pushd tools/power/x86/turbostat
   make %{?make_defines}
   popd
%endif
%endif
%endif

%global bpftool_make \
  %{__make} EXTRA_CFLAGS="${RPM_OPT_FLAGS}" EXTRA_LDFLAGS="%{__global_ldflags}" DESTDIR=$RPM_BUILD_ROOT V=1 %{?make_defines}
%if %{with_bpftool}
pushd tools/bpf/bpftool
%{bpftool_make}
popd
%endif

%define _lto_cflags %{nil}

%global libbpf_make \
  %{__make} DESTDIR=$RPM_BUILD_ROOT OBJDIR=%{_builddir} CFLAGS="%{build_cflags} -fPIC" LDFLAGS="%{build_ldflags} -Wl,--no-as-needed" LIBDIR=/%{_libdir} NO_PKG_CONFIG=1
%if %{with_libbpf}
pushd tools/lib/bpf
%{libbpf_make} prefix=%{_prefix}
popd
%endif



%if %{with_doc}
#
# Make the HTML documents.
# Newer kernel versions use ReST markups for documentation which
# needs to be built using Sphinx. Sphinx toolchain is fragile and any
# upgrade to its toolchain or dependent python package can cause
# documentation build to fail. To avoid this problem, documentation
# build uses one particular version of Sphinx. To build document,
# we create a virtual environment and install the required version
# of Sphinx inside it.
# Refer to $SRC/Documentation/sphinx/requirements.txt for more
# information related to package and version dependency.
#
virtualenv doc_build_env
source ./doc_build_env/bin/activate
pip install -r Documentation/sphinx/requirements.txt
make htmldocs || %{doc_build_fail}
deactivate
rm -rf doc_build_env

# Build man pages for the kernel API (section 9)
scripts/kernel-doc -man $(find . -name '*.[ch]') | %{split_man_cmd} Documentation/output/man
pushd Documentation/output/man
gzip *.9
popd

# sometimes non-world-readable files sneak into the kernel source tree
chmod -R a=rX Documentation
find Documentation -type d | xargs chmod u+w

# switch absolute symlinks to relative ones
find . -lname "$(pwd)*" -exec sh -c 'ln -snvf $(%{__%{py_pkg_prefix}} -c "from os.path import *; print relpath(\"$(readlink {})\",dirname(\"{}\"))") {}' \;
%endif

# In the modsign case, we do 3 things.  1) We check the "flavour" and hard
# code the value in the following invocations.  This is somewhat sub-optimal
# but we're doing this inside of an RPM macro and it isn't as easy as it
# could be because of that.  2) We restore the .tmp_versions/ directory from
# the one we saved off in BuildKernel above.  This is to make sure we're
# signing the modules we actually built/installed in that flavour.  3) We
# grab the arch and invoke mod-sign.sh command to actually sign the modules.
#
# We have to do all of those things _after_ find-debuginfo runs, otherwise
# that will strip the signature off of the modules.
%define __modsign_install_post \
  if [ "%{signmodules}" == "1" ]; then \
    if [ "%{with_debug}" -ne "0" ]; \
    then \
      mv modules.order.sign.debug modules.order \
      Arch=`head -1 configs/kernel-%{rpmversion}-%{_target_cpu}-debug.config | cut -b 3-` \
      mv signing_key.pem.sign.debug signing_key.pem \
      mv signing_key.x509.sign.debug signing_key.x509 \
      make -s ARCH=$Arch V=1 INSTALL_MOD_PATH=$RPM_BUILD_ROOT modules_sign KERNELRELEASE=%{KVERREL}.debug %{?make_defines} \
      %{modsign_cmd} $RPM_BUILD_ROOT/lib/modules/%{KVERREL}.debug/extra/ \
    fi \
    if [ "%{with_up}" -ne "0" ]; \
    then \
      Arch=`head -1 configs/kernel-%{rpmversion}-%{_target_cpu}.config | cut -b 3-` \
      mv signing_key.pem.sign signing_key.pem \
      mv signing_key.x509.sign signing_key.x509 \
      %{modsign_cmd} $RPM_BUILD_ROOT/lib/modules/%{KVERREL}/ \
      %{modsign_cmd} $RPM_BUILD_ROOT/lib/modules/%{KVERREL}/extra/ \
    fi \
  fi \
%{nil}

###
### Special hacks for debuginfo subpackages.
###

# This macro is used by %%install, so we must redefine it before that.
%define debug_package %{nil}

%if %{with_debuginfo}

%ifnarch noarch
%global __debug_package 1
%files -f debugfiles.list debuginfo-common-%{_target_cpu}
%defattr(-,root,root)
%endif

%endif

#
# Disgusting hack alert! We need to ensure we sign modules *after* all
# invocations of strip occur, which is in __debug_install_post if
# find-debuginfo.sh runs, and __os_install_post if not.
%define __spec_install_post \
  %{?__debug_package:%{__debug_install_post}}\
  %{__arch_install_post}\
  %{__os_install_post}\
  %{__modsign_install_post}

###
### install
###

%install

cd linux-%{KVERREL}

%if %{with_doc}
docdir=$RPM_BUILD_ROOT%{_datadir}/doc/kernel-doc-%{rpmversion}
man9dir=$RPM_BUILD_ROOT%{_datadir}/man/man9

# copy the source over
mkdir -p $docdir
tar -f - --exclude=man --exclude='.*' -c Documentation | tar xf - -C $docdir

# Install man pages for the kernel API.
mkdir -p $man9dir
pushd Documentation/output/man
find -type f -name '*.9.gz' -print0 |
xargs -0 --no-run-if-empty %{__install} -m 444 -t $man9dir $m
popd
ls $man9dir | grep -q '' || > $man9dir/BROKEN
%endif

# We have to do the headers install before the tools install because the
# kernel headers_install will remove any header files in /usr/include that
# it doesn't install itself.

%if %{with_headers}
# Install kernel headers
make -s ARCH=%{hdrarch} INSTALL_HDR_PATH=$RPM_BUILD_ROOT/usr headers_install %{?make_defines}

# Do headers_check but don't die if it fails.
make -s ARCH=%{hdrarch} INSTALL_HDR_PATH=$RPM_BUILD_ROOT/usr headers_check \
     > hdrwarnings.txt || :
if grep -q exist hdrwarnings.txt; then
   sed s:^$RPM_BUILD_ROOT/usr/include/:: hdrwarnings.txt
   # Temporarily cause a build failure if header inconsistencies.
   # exit 1
fi

find $RPM_BUILD_ROOT/usr/include \
     \( -name .install -o -name .check -o \
     	-name ..install.cmd -o -name ..check.cmd \) | xargs rm -f

# glibc provides scsi headers for itself, for now
rm -rf $RPM_BUILD_ROOT/usr/include/scsi
rm -f $RPM_BUILD_ROOT/usr/include/asm*/atomic.h
rm -f $RPM_BUILD_ROOT/usr/include/asm*/io.h
rm -f $RPM_BUILD_ROOT/usr/include/asm*/irq.h
%endif

%if %{with_perf}
# perf tool binary and supporting scripts/binaries
%{perf_make} DESTDIR=$RPM_BUILD_ROOT install
# python-perf extension
%{perf_make} DESTDIR=$RPM_BUILD_ROOT install-python_ext
# perf man pages (note: implicit rpm magic compresses them later)
%{perf_make} DESTDIR=$RPM_BUILD_ROOT install-man || %{doc_build_fail}
# clean up files we don't use
rm -f $RPM_BUILD_ROOT/etc/bash_completion.d/perf
%endif

%if %{with_tools}
%ifarch %{cpupowerarchs}
make -C tools/power/cpupower DESTDIR=$RPM_BUILD_ROOT libdir=%{_libdir} mandir=%{_mandir} CPUFREQ_BENCH=false install
rm -f %{buildroot}%{_libdir}/*.{a,la}
%find_lang cpupower
mv cpupower.lang ../
%ifarch %{ix86}
    pushd tools/power/cpupower/debug/i386
    install -m755 centrino-decode %{buildroot}%{_bindir}/centrino-decode
    install -m755 powernow-k8-decode %{buildroot}%{_bindir}/powernow-k8-decode
    popd
%endif
%ifarch x86_64
    pushd tools/power/cpupower/debug/x86_64
    install -m755 centrino-decode %{buildroot}%{_bindir}/centrino-decode
    install -m755 powernow-k8-decode %{buildroot}%{_bindir}/powernow-k8-decode
    popd
%endif
%ifarch %{ix86} x86_64
   mkdir -p %{buildroot}%{_mandir}/man8
   pushd tools/power/x86/x86_energy_perf_policy
   make DESTDIR=%{buildroot} install
   popd
   pushd tools/power/x86/turbostat
   make DESTDIR=%{buildroot} install
   popd
%endif
chmod 0755 %{buildroot}%{_libdir}/libcpupower.so*
mkdir -p %{buildroot}%{_initddir} %{buildroot}%{_sysconfdir}/sysconfig
#install -m644 %{SOURCE2000} %{buildroot}%{_initddir}/cpupower
install -m644 %{SOURCE2001} %{buildroot}%{_sysconfdir}/sysconfig/cpupower
%endif
# just in case so the files list won't croak
touch ../cpupower.lang
%endif

%if %{with_bpftool}
pushd tools/bpf/bpftool
%{bpftool_make} prefix=%{_prefix} bash_compdir=%{_sysconfdir}/bash_completion.d/ mandir=%{_mandir} install doc-install
popd
%endif

%if %{with_libbpf}
pushd tools/lib/bpf
%{libbpf_make} prefix=%{_prefix} install_lib install_headers install_pkgconfig
popd
%endif 

# Install udev and dracut rules for modules-extra
%if %{with_mods_extra}
mkdir -p %{buildroot}%{_udevrulesdir}
install -m644 %{SOURCE100} %{buildroot}%{_udevrulesdir}/61-drm-simplefb.rules
mkdir -p %{buildroot}%{_libdir}/dracut/modules.d/51drm-simplefb
install -D -m 755 %{SOURCE101} %{buildroot}%{dracutlibdir}/modules.d/51drm-simplefb/module-setup.sh
%endif

%if %{with_configs_only}
for i in configs/*
do
    if [[ $i =~ debug ]];
    then
        install -m 644 $i $RPM_BUILD_ROOT/configs/config-%{_target_cpu}-debug
    else
        install -m 644 $i $RPM_BUILD_ROOT/configs/config-%{_target_cpu}
    fi
done
%endif

###
### clean
###

%clean
rm -rf $RPM_BUILD_ROOT

###
### scripts
###

%if %{with_tools}
%post tools
%{_sbindir}/ldconfig

%postun tools
%{_sbindir}/ldconfig
%endif

#
# This macro defines a %%post script for a kernel*-devel package.
#	%%kernel_devel_post [<subpackage>]
#
# Note we don't run hardlink if ostree is in use, as ostree is
# a far more sophisticated hardlink implementation.
# https://github.com/projectatomic/rpm-ostree/commit/58a79056a889be8814aa51f507b2c7a4dccee526
#
%define kernel_devel_post() \
%{expand:%%post %{?1:%{1}-}devel}\
if [ -f /etc/sysconfig/kernel ]\
then\
    . /etc/sysconfig/kernel || exit $?\
fi\
if [ "$HARDLINK" != "no" -a -x %{_sbindir}/hardlink -a ! -e /run/ostree-booted ]\
then\
    (cd /usr/src/kernels/%{KVERREL}%{?1:.%{1}} &&\
     %{_bindir}/find . -type f | while read f; do\
       %{_sbindir}/hardlink -c /usr/src/kernels/*.%{dist}.*/$f $f\
     done)\
fi\
    %{nil}


# These 2 macros make sure we run dracut if needed. There are 2 cases:
# 1. if only kernel-modules-extra is installed, then we must execute dracut -f
# so the modules are properly added to the initramfs.
#
# 2. if both kernel and kernel-modules-extra are installed, then dracut runs as
# part of the kernel installation in the kernel's %%posttrans and it can be
# skipped in kernel-modules-extra's %%posttrans. Because the package
# installation order between kernel and kernel-modules-extra can be arbitrary
# due to the cyclic dependency, we must check again in the posttrans whether
# we're really not installing a kernel at the same time to avoid running dracut
# before the kernel is completely installed.
%define set_need_to_run_dracut() \
if [ ! -f %{_localstatedir}/lib/rpm-state/%{name}/installing_%{KVERREL}%{?1:+%{1}} ]; then\
	mkdir -p %{_localstatedir}/lib/rpm-state/%{name}\
	touch %{_localstatedir}/lib/rpm-state/%{name}/need_to_run_dracut_%{KVERREL}%{?1:+%{1}}\
fi\
%{nil}

%define check_and_run_dracut() \
if [ -f %{_localstatedir}/lib/rpm-state/%{name}/need_to_run_dracut_%{KVERREL}%{?1:+%{1}} ]; then\
	rm -f %{_localstatedir}/lib/rpm-state/%{name}/need_to_run_dracut_%{KVERREL}%{?1:+%{1}}\
	if [ ! -f %{_localstatedir}/lib/rpm-state/%{name}/installing_%{KVERREL}%{?1:+%{1}} ]; then\
		echo "Running: dracut -f --kver %{KVERREL}%{?1:+%{1}}"\
		dracut -f --kver "%{KVERREL}%{?1:+%{1}}" || exit $?\
	fi\
fi\
%{nil}

#
# This macro defines a %%post script for a kernel*-modules-extra package.
# It also defines a %%postun script that does the same thing.
#	%%kernel_modules_extra_post [<subpackage>]
#
# Note: We don't run dracut to re-create the initramfs when removing the modules-extra package.
#       we probably should, but for some obscure reason, rpm doesn't call %posttrans on
#       uninstall transactions and I don't want to leave a stale state file.

%define kernel_modules_extra_post() \
%{expand:%%post %{?1:%{1}-}modules-extra}\
[ -d /lib/modules/%{KVERREL}%{?1:+%{1}} ] && /sbin/depmod -a %{KVERREL}%{?1:+%{1}}\
%{expand:%%set_need_to_run_dracut}\
%{nil}\
%{expand:%%postun %{?1:%{1}-}modules-extra}\
[ -d /lib/modules/%{KVERREL}%{?1:+%{1}} ] && /sbin/depmod -a %{KVERREL}%{?1:+%{1}}\
%{nil}\
%{expand:%%posttrans %{?1:%{1}-}modules-extra}\
%{expand:%%check_and_run_dracut}\
%{nil}

# This macro defines a %%posttrans script for a kernel package.
#	%%kernel_variant_posttrans [<subpackage>]
# More text can follow to go at the end of this variant's %%post.
#
%if 0%{?amzn} >= 2022

%define kernel_variant_posttrans() \
%{expand:%%posttrans %{?1}}\
if [ -x %{_sbindir}/weak-modules ]\
then\
    %{_sbindir}/weak-modules --add-kernel %{KVERREL}%{?1:+%{1}} || exit $?\
fi\
rm -f %{_localstatedir}/lib/rpm-state/%{name}/installing_%{KVERREL}%{?-v:+%{-v*}}\
/bin/kernel-install add %{KVERREL}%{?1:+%{1}} /lib/modules/%{KVERREL}%{?1:+%{1}}/vmlinuz || exit $?\
%if %{signkernel} \
    %amzn_sb_revoke\
%endif\
%{nil}

%else

%define kernel_variant_posttrans() \
%{expand:%%posttrans %{?1}}\
%{expand:\
%{_sbindir}/new-kernel-pkg --package kernel%{?1:-%{1}} --mkinitrd --make-default --dracut --depmod --install %{KVERREL}%{?1:.%{1}} || exit $?\
}\
%{_sbindir}/new-kernel-pkg --package kernel%{?1:-%{1}} --rpmposttrans %{KVERREL}%{?1:.%{1}} || exit $?\
%{nil}

%endif

#
# This macro defines a %%post script for a kernel package and its devel package.
#	%%kernel_variant_post [-v <subpackage>] [-r <replace>]
# More text can follow to go at the end of this variant's %%post.
#
%define kernel_variant_post(v:r:) \
%{expand:%%kernel_devel_post %{?-v*}}\
%if %{with_mods_extra}\
%{expand:%%kernel_modules_extra_post %{?-v*}}\
%endif\
%{expand:%%kernel_variant_posttrans %{?-v*}}\
%{expand:%%post %{?-v*}}\
%{-r:\
if [ `uname -i` == "x86_64" -o `uname -i` == "i386" ] &&\
   [ -f /etc/sysconfig/kernel ]; then\
  %{_bindir}/sed -r -i -e 's/^DEFAULTKERNEL=%{-r*}$/DEFAULTKERNEL=kernel%{?-v:-%{-v*}}/' /etc/sysconfig/kernel || exit $?\
fi}\
/sbin/depmod -a %{KVERREL}%{?1:+%{1}}\
mkdir -p %{_localstatedir}/lib/rpm-state/%{name}\
%if 0%{?amzn} >= 2022\
touch %{_localstatedir}/lib/rpm-state/%{name}/installing_%{KVERREL}%{?-v:+%{-v*}}\
%endif\
%{nil}

#
# This macro defines a %%preun script for a kernel package.
#	%%kernel_variant_preun <subpackage>
#
%if 0%{?amzn} >= 2022

%define kernel_variant_preun() \
%{expand:%%preun %{?1}}\
/bin/kernel-install remove %{KVERREL}%{?1:+%{1}} /lib/modules/%{KVERREL}%{?1:+%{1}}/vmlinuz || exit $?\
if [ -x %{_sbindir}/weak-modules ]\
then\
    %{_sbindir}/weak-modules --remove-kernel %{KVERREL}%{?1:+%{1}} || exit $?\
fi\
%{nil}

%else

%define kernel_variant_preun() \
%{expand:%%preun %{?1}}\
%{_sbindir}/new-kernel-pkg --rminitrd --rmmoddep --remove %{KVERREL}%{?1:.%{1}} || exit $?\
%{nil}

%endif

%kernel_variant_preun
%kernel_variant_post

%kernel_variant_preun debug
%kernel_variant_post -v debug

if [ -x %{_sbindir}/ldconfig ]
then
    %{_sbindir}/ldconfig -X || exit $?
fi

###
### file lists
###

%if %{with_headers}
%files headers
%defattr(-,root,root)
/usr/include/*
%endif

# only some architecture builds need kernel-doc
%if %{with_doc}
%files doc
%defattr(-,root,root)
%{_datadir}/doc/kernel-doc-%{rpmversion}/Documentation/*
%dir %{_datadir}/doc/kernel-doc-%{rpmversion}/Documentation
%dir %{_datadir}/doc/kernel-doc-%{rpmversion}
%{_datadir}/man/man9/*
%endif

%if %{with_perf}
%files -n perf%{kbasever}
%defattr(-,root,root)
%{_bindir}/perf
%{_libdir}/libperf-jvmti.so
%{_bindir}/trace
%dir %{_libexecdir}/perf-core
%{_libexecdir}/perf-core/*
%{_datadir}/perf-core/*
%{_datadir}/doc/perf*/*
%{_mandir}/man[1-8]/perf*
%doc linux-%{KVERREL}/tools/perf/Documentation/examples.txt

%files -n %{py_pkg_prefix}-perf%{kbasever}
%defattr(-,root,root)
%{python_sitearch}/*

%if %{with_debuginfo}
%files -f perf-debuginfo.list -n perf%{kbasever}-debuginfo
%defattr(-,root,root)

%files -f %{py_pkg_prefix}-perf-debuginfo.list -n %{py_pkg_prefix}-perf%{kbasever}-debuginfo
%defattr(-,root,root)
%endif
%endif

%if %{with_tools}
%files tools -f cpupower.lang
%defattr(-,root,root)
%{_mandir}/man[1-8]/cpupower*
%{_bindir}/cpupower
%{_datadir}/bash-completion/completions/cpupower
%ifarch %{ix86} x86_64
%{_bindir}/centrino-decode
%{_bindir}/powernow-k8-decode
%{_bindir}/x86_energy_perf_policy
%{_mandir}/man8/x86_energy_perf_policy*
%{_bindir}/turbostat
%{_mandir}/man8/turbostat*
%endif
%{_libdir}/libcpupower.so.1
%{_libdir}/libcpupower.so.0.0.1
%config(noreplace) %{_sysconfdir}/sysconfig/cpupower

%if %{with_debuginfo}
%files tools-debuginfo -f kernel-tools-debuginfo.list
%defattr(-,root,root)
%endif

%ifarch %{cpupowerarchs}
%files tools-devel
%{_libdir}/libcpupower.so
%{_includedir}/cpufreq.h
%endif
# with_tools
%endif

%if %{with_bpftool}
%files -n bpftool%{kbasever}
%{_sbindir}/bpftool
%{_sysconfdir}/bash_completion.d/bpftool
%{_mandir}/man8/bpftool-cgroup.8.gz
%{_mandir}/man8/bpftool-gen.8.gz
%{_mandir}/man8/bpftool-iter.8.gz
%{_mandir}/man8/bpftool-link.8.gz
%{_mandir}/man8/bpftool-map.8.gz
%{_mandir}/man8/bpftool-prog.8.gz
%{_mandir}/man8/bpftool-perf.8.gz
%{_mandir}/man8/bpftool.8.gz
%{_mandir}/man8/bpftool-net.8.gz
%{_mandir}/man8/bpftool-feature.8.gz
%{_mandir}/man8/bpftool-btf.8.gz
%{_mandir}/man8/bpftool-struct_ops.8.gz

%if %{with_debuginfo}
%files -f bpftool-debuginfo.list -n bpftool%{kbasever}-debuginfo
%defattr(-,root,root)
%endif
%endif

%if %{with_libbpf}
%files libbpf
%{_libdir}/libbpf.so.%{libbpf_version}
%{_libdir}/libbpf.so.1

%files libbpf-devel
%{_libdir}/libbpf.so
%{_includedir}/bpf/
%{_libdir}/pkgconfig/libbpf.pc

%files libbpf-static
%{_libdir}/libbpf.a

%if %{with_debuginfo}
%files libbpf-debuginfo -f kernel-libbpf-debuginfo.list
%defattr(-,root,root)
%endif

%endif

%if %{with_mods_extra}
%files modules-extra-common
%{dracutlibdir}/modules.d/51drm-simplefb
%{_udevrulesdir}/61-drm-simplefb.rules
%endif

# This is %%{image_install_path} on an arch where that includes ELF files,
# or empty otherwise.
%define elf_image_install_path %{?kernel_image_elf:%{image_install_path}}

#
# This macro defines the %%files sections for a kernel package
# and its devel and debuginfo packages.
#	%%kernel_variant_files [-k vmlinux] <condition> <subpackage>
#
%define kernel_variant_files(k:) \
%if %{1}\
%{expand:%%files %{?2}}\
%defattr(-,root,root)\
%if 0%{?amzn} >= 2022\
/lib/modules/%{KVERREL}%{?2:+%{2}}/%{?-k:%{-k*}}%{!?-k:vmlinuz}\
%ghost /%{image_install_path}/%{?-k:%{-k*}}%{!?-k:vmlinuz}-%{KVERREL}%{?2:.%{2}}\
%attr(600,root,root) /lib/modules/%{KVERREL}%{?2:+%{2}}/System.map\
%ghost /boot/System.map-%{KVERREL}%{?2:.%{2}}\
%if %{with_fips} \
/lib/modules/%{KVERREL}%{?2:+%{2}}/.vmlinuz.hmac \
%ghost /%{image_install_path}/.vmlinuz-%{KVERREL}%{?2:.%{2}}.hmac \
%endif \
/lib/modules/%{KVERREL}%{?3:+%{3}}/symvers.gz\
/lib/modules/%{KVERREL}%{?2:+%{2}}/config\
%ghost /boot/symvers-%{KVERREL}%{?2:.%{2}}.gz\
%ghost /boot/config-%{KVERREL}%{?2:.%{2}}\
%else\
/%{image_install_path}/%{?-k:%{-k*}}%{!?-k:vmlinuz}-%{KVERREL}%{?2:.%{2}}\
%attr(600,root,root) /boot/System.map-%{KVERREL}%{?2:.%{2}}\
%if %{with_fips} \
/%{image_install_path}/.vmlinuz-%{KVERREL}%{?2:.%{2}}.hmac \
%endif\
/boot/symvers-%{KVERREL}%{?2:.%{2}}.gz\
/boot/config-%{KVERREL}%{?2:.%{2}}\
%endif\
%dir /lib/modules/%{KVERREL}%{?2:.%{2}}\
/lib/modules/%{KVERREL}%{?2:.%{2}}/kernel\
/lib/modules/%{KVERREL}%{?2:.%{2}}/build\
/lib/modules/%{KVERREL}%{?2:.%{2}}/source\
/lib/modules/%{KVERREL}%{?2:.%{2}}/updates\
/lib/modules/%{KVERREL}%{?2:.%{2}}/weak-updates\
%ifarch %{vdso_arches}\
/lib/modules/%{KVERREL}%{?2:.%{2}}/vdso\
%endif\
/lib/modules/%{KVERREL}%{?2:.%{2}}/modules.*\
%ghost /boot/initramfs-%{KVERREL}%{?2:.%{2}}.img\
%{expand:%%files %{?2:%{2}-}devel}\
%defattr(-,root,root)\
%verify(not mtime) /usr/src/kernels/%{KVERREL}%{?2:.%{2}}\
%dir /usr/src/kernels\
%if %{with_mods_extra}\
%{expand:%%files %{?2:%{2}-}modules-extra}\
/lib/modules/%{KVERREL}%{?2:.%{2}}/extra/\
%endif\
%if %{with_debuginfo}\
%ifnarch noarch\
%{expand:%%files -f debuginfo%{?2}.list %{?2:%{2}-}debuginfo}\
%defattr(-,root,root)\
%endif\
%endif\
%endif\
%{nil}

%kernel_variant_files %{with_up}
%kernel_variant_files %{with_debug} debug

#
# Finally kernel-livepatch as it has it's own version/release
# NOTE: Don't move this anywhere else, otherwise it'll need
# it's own Name: and that affects all the packages that
# follow. Aslo having a Version, Release affects other subpackages
# so safely tuck this to the end.
# Other Caveats: This spec file uses a special hack for __spec_install_post
# Hence, all operations in __spec_install_post should not refer to
# either %%{version} or %%{release}
#
%ifarch x86_64 aarch64
%package -n kernel-livepatch-%{rpmversion}-%{buildid}
Summary: Livepatches for the Linux Kernel
Version: 1.0
Release: 0%{?dist}
Requires: kpatch
Requires: kernel = %{?epoch:%{epoch}:}%{rpmversion}-%{pkg_release}
BuildRequires: systemd

%{?systemd_requires}

%description -n kernel-livepatch-%{rpmversion}-%{buildid}
This package contains the live patch modules for bug fixes
against the version of the kernel. This package contains
version 0 (no real livepatches) and helps subscribe to
the kernel livepatch updates for the kernel.

%files -n kernel-livepatch-%{rpmversion}-%{buildid}
%defattr(-,root,root)
%{nil}
%endif

%if %{with_configs_only}
%files configs
/configs/config-*
%endif

%changelog
* Tue Feb 24 2026 Builder <builder@amazon.com>
- builder/9cd680e84f7c77520d59d5c8029da4cb141a11be last changes:
  + [8b3c3511] [2026-02-23] Rebase to 6.12.73 (ellavila@amazon.com)

- linux last changes:
  + [2026-02-19] AL2023 6.12: Update lustrefsx to 2.15.6-fsx27 commit (ec2-user@ip-172-31-73-138.ec2.internal)
  + [2025-05-19] iommu: Skip PASID validation for devices without PASID capability (tdave@nvidia.com)
  + [2025-12-24] AL2023-6.12-Update-ena-driver-to-2.16.1g (darinzon@amazon.com)
  + [2026-01-20] Revert "sched/fair: Proportional newidle balance" (wanjay@amazon.com)
  + [2025-11-21] AL2023 6.12: Update lustrefsx to 2.15.6-fsx25 commit (ec2-user@ip-172-31-25-196.ec2.internal)
  + [2025-11-12] drivers/amazon/net: Update igb_uio (apanyaki@amazon.com)
  + [2025-10-20] AL2023 6.12: Update lustrefsx to 2.15.6-fsx23 commit (ec2-user@ip-172-31-86-109.ec2.internal)
  + [2025-10-06] crypto/rng: Remove reseeding call (ellavila@amazon.com)
  + [2025-09-29] vfio-pci: enable mmap-ing ena device (mngyadam@amazon.de)
  + [2025-10-07] drivers/media/v4l2loopback: ingest version 0.15.1 (mheyne@amazon.de)
  + [2025-09-15] AL2023-6.12-Update-ena-driver-to-2.15.0g (darinzon@amazon.com)
  + [2025-08-25] net/mlx5: HWS, Fix memory leak in hws_pool_buddy_init error path (lkayal@nvidia.com)
  + [2025-06-30] arm64: Implement HAVE_LIVEPATCH (song@kernel.org)
  + [2025-05-21] arm64: stacktrace: Implement arch_stack_walk_reliable() (song@kernel.org)
  + [2025-08-12] net/sched: Fix backlog accounting in qdisc_dequeue_internal (will@willsroot.io)
  + [2024-10-31] RDMA/mlx5: Support querying per-plane IB PortCounters (markzhang@nvidia.com)
  + [2024-09-03] RDMA/mlx5: Support OOO RX WQE consumption (edwards@nvidia.com)
  + [2024-09-03] net/mlx5: Introduce data placement ordering bits (edwards@nvidia.com)
  + [2025-08-21] mm/damon/core: prevent unnecessary overflow in damos_set_effective_quota() (yanquanmin1@huawei.com)
  + [2025-09-03] Updating lustrefsx to 2.15.6 (suschako@amazon.de)
  + [2025-08-20] AL2023 6.12 Update EFA driver to 2.17.2 (mrgolin@amazon.com)
  + [2025-09-03] Revert "mm/hugetlb: fix huge_pmd_unshare() vs GUP-fast race" (simonlie@amazon.de)
  + [2025-08-29] crypto: rng: fix incorrect mutex unlock in crypto_del_rng() (wanjay@amazon.com)
  + [2025-04-01] exfat: fix double free in delayed_free (linkinjeon@kernel.org)
  + [2025-04-01] jfs: fix array-index-out-of-bounds read in add_missing_indices (duttaditya18@gmail.com)
  + [2025-08-01] net: Change IPv4/6 IP fragmentation waiting time to 1 sec (yifeima@amazon.com)
  + [2025-06-13] AL2023 6.12: Update lustrefsx to 2.15.6-fsx19 commit (ec2-user@ip-10-0-70-253.ec2.internal)
  + [2025-05-07] ublk: fix race between io_uring_cmd_complete_in_task and ublk_cancel_cmd (ming.lei@redhat.com)
  + [2025-04-10] virtgpu: don't reset on shutdown (mst@redhat.com)
  + [2024-08-08] virtio: break and reset virtio devices on device_shutdown() (mst@redhat.com)
  + [2025-06-26] Override drivers/char/random only after FIPS-mode RNGs become available (wanjay@amazon.com)
  + [2025-02-24] crypto: ecc: Remove flipping of private key in selftest (ellavila@amazon.com)
  + [2023-06-23] crypto: ecc - Add SP800-56A rev 3 Pair-wise Consistency check (mngyadam@amazon.com)
  + [2023-06-23] crypto: dh - Add SP800-56A rev 3 Pair-wise Consistency check (mngyadam@amazon.com)
  + [2023-03-03] crypto: rng - Use a different crypto_rng for reseeding (herbert.xu@redhat.com)
  + [2022-08-03] random: allow reseeding DRBG with getrandom (dueno@redhat.com)
  + [2023-06-09] crypto: Only allow GCM in FIPS when instantiated via seqiv (samjonas@amazon.com)
  + [2021-08-10] crypto: rng - Override drivers/char/random in FIPS mode (herbert.xu@redhat.com)
  + [2021-08-10] random: Add hook to override device reads and getrandom(2) (herbert.xu@redhat.com)
  + [2023-06-06] crypto: ecdh - zeroize crpytographic keys after use (hailmo@amazon.com)
  + [2017-10-27] Enable Algorithims for Amazon Linux 6.1.y (alakeshh@amazon.com)
  + [2025-05-22] AL2023-6.12-Update-ena-driver-to-2.14.1g (darinzon@amazon.com)
  + [2025-04-12] arm64/module: Use text-poke API for late relocations. (dylanbhatch@google.com)
  + [2025-04-12] arm64: patching: Rename aarch64_insn_copy to text_poke. (dylanbhatch@google.com)
  + [2024-10-23] asm-generic: introduce text-patching.h (rppt@kernel.org)
  + [2025-04-22] AL2023 6.12: Update lustrefsx to 2.15.6-fsx18 commit (ec2-user@ip-172-31-65-34.ec2.internal)
  + [2025-03-05] AL2023 6.12: Update lustre and lnet to 2.15.6-fsx16 commit (ec2-user@ip-10-0-12-233.ec2.internal)
  + [2023-07-11] scripts/sign_file: Add option to keep signing certificate (samjonas@amazon.com)
  + [2019-04-23] KEYS: Make use of platform keyring for module signature verify (robeholmes@gmail.com)
  + [2025-02-12] Revert "memcg: use ratelimited stats flush in the reclaim" (shaoyi@amazon.com)
  + [2025-02-07] ptp: vmclock: Remove goto-based cleanup logic (thomas.weissschuh@linutronix.de)
  + [2025-02-07] ptp: vmclock: Clean up miscdev and ptp clock through devres (thomas.weissschuh@linutronix.de)
  + [2025-02-07] ptp: vmclock: Don't unregister misc device if it was not registered (thomas.weissschuh@linutronix.de)
  + [2025-02-07] ptp: vmclock: Set driver data before its usage (thomas.weissschuh@linutronix.de)
  + [2025-02-07] ptp: vmclock: Add .owner to vmclock_miscdev_fops (dwmw@amazon.co.uk)
  + [2024-10-06] ptp: Add support for the AMZNC10C 'vmclock' device (dwmw@amazon.co.uk)
  + [2023-07-27] ip: Bump default ttl to 127. (kuniyu@amazon.com)
  + [2024-06-13] acpi: Support CONFIG_ACPI without CONFIG_PCI (surajjs@amazon.com)
  + [2024-12-11] arm64: stacktrace: Don't WARN when unwinding other tasks (mark.rutland@arm.com)
  + [2024-12-11] arm64: stacktrace: Skip reporting LR at exception boundaries (mark.rutland@arm.com)
  + [2024-10-17] arm64: stacktrace: unwind exception boundaries (mark.rutland@arm.com)
  + [2024-10-17] arm64: stacktrace: split unwind_consume_stack() (mark.rutland@arm.com)
  + [2024-10-17] arm64: stacktrace: report recovered PCs (mark.rutland@arm.com)
  + [2024-10-17] arm64: stacktrace: report source of unwind data (mark.rutland@arm.com)
  + [2024-10-17] arm64: stacktrace: move dump_backtrace() to kunwind_stack_walk() (mark.rutland@arm.com)
  + [2024-10-17] arm64: use a common struct frame_record (mark.rutland@arm.com)
  + [2024-10-17] arm64: pt_regs: swap 'unused' and 'pmr' fields (mark.rutland@arm.com)
  + [2024-10-17] arm64: pt_regs: rename "pmr_save" -> "pmr" (mark.rutland@arm.com)
  + [2024-10-17] arm64: pt_regs: remove stale big-endian layout (mark.rutland@arm.com)
  + [2024-10-17] arm64: pt_regs: assert pt_regs is a multiple of 16 bytes (mark.rutland@arm.com)
  + [2021-02-22] hwrng: Add Gravition RNG driver (vaerov@amazon.com)
  + [2021-02-22] arm64: Export acpi_psci_use_hvc() symbol (vaerov@amazon.com)
  + [2025-01-08] AL2023-6.12-Update-ena-driver-to-2.13.2g (darinzon@amazon.com)
  + [2024-12-19] media: Import v4l2loopback v0.13.2 (zcgao@amazon.com)
  + [2021-05-12] x86: Disable KASLR when Xen is detected (benh@amazon.com)
  + [2023-01-24] Revert "xen/x2apic: enable x2apic mode when supported for HVM" (samjonas@amazon.com)
  + [2019-11-27] block/xen-blkfront: bump the maximum number of indirect segments up to 64 (fllinden@amazon.com)
  + [2019-08-15] xen: Restore xen-pirqs on resume from hibernation (anchalag@amazon.com)
  + [2019-01-31] xen-netfront: call netif_device_attach on resume (fllinden@amazon.com)
  + [2018-11-10] xen: Only restore the ACPI SCI interrupt in xen_restore_pirqs. (fllinden@amazon.com)
  + [2018-10-26] xen: restore pirqs on resume from hibernation. (fllinden@amazon.com)
  + [2018-10-18] block: xen-blkfront: consider new dom0 features on restore (eduval@amazon.com)
  + [2018-04-09] x86: tsc: avoid system instability in hibernation (eduval@amazon.com)
  + [2018-06-05] xen-blkfront: Fixed blkfront_restore to remove a call to negotiate_mq (anchalag@amazon.com)
  + [2018-03-27] Revert "xen: dont fiddle with event channel masking in suspend/resume" (anchalag@amazon.com)
  + [2017-10-27] PM / hibernate: update the resume offset on SNAPSHOT_SET_SWAP_AREA (cyberax@amazon.com)
  + [2017-08-24] x86/xen: close event channels for PIRQs in system core suspend callback (kamatam@amazon.com)
  + [2017-08-24] xen/events: add xen_shutdown_pirqs helper function (kamatam@amazon.com)
  + [2017-07-21] x86/xen: save and restore steal clock (kamatam@amazon.com)
  + [2017-07-13] xen/time: introduce xen_{save,restore}_steal_clock (kamatam@amazon.com)
  + [2017-01-09] xen-netfront: add callbacks for PM suspend and hibernation support (kamatam@amazon.com)
  + [2017-06-08] xen-blkfront: add callbacks for PM suspend and hibernation (kamatam@amazon.com)
  + [2017-02-11] x86/xen: add system core suspend and resume callbacks (kamatam@amazon.com)
  + [2018-02-22] x86/xen: Introduce new function to map HYPERVISOR_shared_info on Resume (anchalag@amazon.com)
  + [2017-07-13] xenbus: add freeze/thaw/restore callbacks support (kamatam@amazon.com)
  + [2017-07-13] xen/manage: introduce helper function to know the on-going suspend mode (kamatam@amazon.com)
  + [2017-07-12] xen/manage: keep track of the on-going suspend mode (kamatam@amazon.com)
  + [2025-01-23] Lustre client support for 6.12 kernel (ec2-user@ip-172-31-75-90.ec2.internal)
  + [2025-01-23] Config glue for Lustre client (ec2-user@ip-172-31-75-90.ec2.internal)
  + [2025-01-12] AL2023 6.12 Update EFA driver to 2.13.1 (mrgolin@amazon.com)
  + [2024-11-18] page_touching: select ARCH_HAS_DMA_OPS (mheyne@amazon.de)
  + [2024-11-12] efa: fix to account for upstream change (mheyne@amazon.de)
  + [2024-10-04] perf/x86/amd/core: Don't unfreeze LBR (mheyne@amazon.de)
  + [2024-10-01] TEMPORARILY Revert "arm64: Kconfig: Enable hotplug CPU on arm64 if ACPI_PROCESSOR is enabled." (mheyne@amazon.de)
  + [2024-09-20] ena,efa: fixes for kernel 6.11 (mheyne@amazon.de)
  + [2024-07-23] dma: Automatically enable page touching on Caspian (dwmw@amazon.co.uk)
  + [2024-07-24] drivers/amazon/net/ena/ena_xdp: Fix build failure due to xsk_buff_dma_sync_for_cpu() (sjpark@amazon.com)
  + [2024-07-24] drivers/amazon/net/ena/ena_xdp: Use napi_alloc_skb() (sjpark@amazon.com)
  + [2024-07-12] AL2023-6.1-Update-ena-driver-to-2.12.3g (akiyano@amazon.com)
  + [2024-06-17] drivers/amazon/net/ena/config: Add ENA_HAVE_ETHTOOL_RXFH_PARAM (sjpark@amazon.com)
  + [2024-06-17] drivers: Add amazon drivers for EFA, ENA, and igb_uio (sjpark@amazon.com)
  + [2018-02-12] drivers: introduce AMAZON_DRIVER_UPDATES (vallish@amazon.com)
  + [2023-02-09] Enable ptIOMMU for all supported platforms (daviddb@amazon.com)
  + [2022-05-25] Correct read overflow in page touching DMA ops binding (tbarri@amazon.com)
  + [2021-09-17] Introduce page touching DMA ops binding (jgowans@amazon.com)
  + [2021-12-10] virtio-balloon: optionally report offlined memory ranges (fllinden@amazon.com)
  + [2022-01-06] virtio: add hack to allow pre-mapped scatterlists (fllinden@amazon.com)
  + [2022-01-06] mm: add offline page reporting interface (fllinden@amazon.com)
  + [2021-12-09] drivers/base/memory: use MHP_MEMMAP_ON_MEMORY from the probe interface (fllinden@amazon.com)
  + [2021-12-31] memory: fix offline_and_remove_memory use (fllinden@amazon.com)
  + [2021-07-14] arm64/mm: Enable sysfs based memory hot remove probe (rohiwali@amazon.com)
  + [2019-04-03] Sysfs memory probe interface (anshuman.khandual@arm.com)
