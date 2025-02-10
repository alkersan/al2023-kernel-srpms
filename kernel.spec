%define buildid 136.201

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
%global kversion 6.1.128
%define rpmversion %{kversion}

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
%define make_target Image.gz
%define kernel_image arch/%{asmarch}/boot/Image.gz
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
%global libbpf_version 1.1.0
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
# This macro does requires, provides, conflicts, obsoletes for a kernel package.
#	%%kernel_reqprovconf <subpackage>
# It uses any kernel_<subpackage>_conflicts and kernel_<subpackage>_obsoletes
# macros defined above.
#
%define kernel_reqprovconf \
Provides: kernel = %{rpmversion}-%{pkg_release}\
Provides: kernel-%{_target_cpu} = %{rpmversion}-%{pkg_release}%{?1:.%{1}}\
Provides: kernel-drm-nouveau = 16\
Provides: kernel-modeset = 1\
Provides: kernel-uname-r = %{KVERREL}%{?variant}%{?1:.%{1}}\
Requires(pre): %{kernel_prereq}\
Requires(pre): %{initrd_prereq}\
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

Name: kernel%{?variant}
Group: System Environment/Kernel
License: GPLv2 and Redistributable, no modification permitted
URL: http://www.kernel.org/
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
BuildRequires: kmod, patch, bash, tar
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
BuildRequires: elfutils-devel zlib-devel binutils-devel newt-devel %{py_pkg_prefix}-devel bison
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

Source0: linux-%{kversion}.tar.xz
Source1: linux-%{kversion}-patches.tar

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
Source70: macros.kmod-sign
%define split_man_cmd %{SOURCE50}

# udev and dracut rules for module-extras
Source100: drm-simplefb.rules
Source101: dracut-drm-simplefb.module

# Sources for kernel-tools
Source2000: cpupower.init
Source2001: cpupower.config

# __PATCHFILE_TEMPLATE__
Patch0: mm-memcg-throttle-the-memory-reclaim-given-dirty-wri.patch
Patch1: Sysfs-memory-probe-interface.patch
Patch2: arm64-mm-Enable-sysfs-based-memory-hot-remove-probe.patch
Patch3: memory-fix-offline_and_remove_memory-use.patch
Patch4: drivers-base-memory-use-MHP_MEMMAP_ON_MEMORY-from-th.patch
Patch5: mm-add-offline-page-reporting-interface.patch
Patch6: virtio-add-hack-to-allow-pre-mapped-scatterlists.patch
Patch7: virtio-balloon-optionally-report-offlined-memory-ran.patch
Patch8: Introduce-page-touching-DMA-ops-binding.patch
Patch9: Correct-read-overflow-in-page-touching-DMA-ops-bindi.patch
Patch10: x86-Disable-KASLR-when-Xen-is-detected.patch
Patch11: arm64-Export-acpi_psci_use_hvc-symbol.patch
Patch12: hwrng-Add-Gravition-RNG-driver.patch
Patch13: drivers-introduce-AMAZON_DRIVER_UPDATES.patch
Patch14: drivers-amazon-import-5.15-drivers.patch
Patch15: ENA-Update-to-v2.8.1.patch
Patch16: EFA-Update-to-v2.1.1.patch
Patch17: Enable-Algorithims-for-Amazon-Linux-6.1.y.patch
Patch18: xen-manage-keep-track-of-the-on-going-suspend-mode.patch
Patch19: xen-manage-introduce-helper-function-to-know-the-on-.patch
Patch20: xenbus-add-freeze-thaw-restore-callbacks-support.patch
Patch21: x86-xen-Introduce-new-function-to-map-HYPERVISOR_sha.patch
Patch22: x86-xen-add-system-core-suspend-and-resume-callbacks.patch
Patch23: xen-blkfront-add-callbacks-for-PM-suspend-and-hibern.patch
Patch24: xen-netfront-add-callbacks-for-PM-suspend-and-hibern.patch
Patch25: xen-time-introduce-xen_-save-restore-_steal_clock.patch
Patch26: x86-xen-save-and-restore-steal-clock.patch
Patch27: xen-events-add-xen_shutdown_pirqs-helper-function.patch
Patch28: x86-xen-close-event-channels-for-PIRQs-in-system-cor.patch
Patch29: PM-hibernate-update-the-resume-offset-on-SNAPSHOT_SE.patch
Patch30: Revert-xen-dont-fiddle-with-event-channel-masking-in.patch
Patch31: xen-blkfront-Fixed-blkfront_restore-to-remove-a-call.patch
Patch32: x86-tsc-avoid-system-instability-in-hibernation.patch
Patch33: block-xen-blkfront-consider-new-dom0-features-on-res.patch
Patch34: xen-restore-pirqs-on-resume-from-hibernation.patch
Patch35: xen-Only-restore-the-ACPI-SCI-interrupt-in-xen_resto.patch
Patch36: xen-netfront-call-netif_device_attach-on-resume.patch
Patch37: xen-Restore-xen-pirqs-on-resume-from-hibernation.patch
Patch38: block-xen-blkfront-bump-the-maximum-number-of-indire.patch
Patch39: Revert-PCI-MSI-Let-core-code-free-MSI-descriptors.patch
Patch40: Revert-xen-x2apic-enable-x2apic-mode-when-supported-.patch
Patch41: msr-disable-MSR-writes-by-default.patch
Patch42: udp-Fix-memleaks-of-sk-and-zerocopy-skbs-with-TX-tim.patch
Patch43: ENA-Update-to-v2.8.3.patch
Patch44: Revert-selinux-runtime-disable-is-deprecated-add-som.patch
Patch45: AL2023-6.1-Update-ena-driver-to-2.8.6g.patch
Patch46: objtool-Add-generic-symbol-for-relocation-type.patch
Patch47: objtool-Specify-host-arch-for-making-LIBSUBCMD.patch
Patch48: tools-arm64-Make-aarch64-instruction-decoder-availab.patch
Patch49: objtool-arm64-Add-base-definition-for-arm64-backend.patch
Patch50: objtool-arm64-Decode-add-sub-instructions.patch
Patch51: objtool-arm64-Decode-jump-and-call-related-instructi.patch
Patch52: objtool-arm64-Decode-other-system-instructions.patch
Patch53: objtool-arm64-Decode-load-store-instructions.patch
Patch54: objtool-arm64-Decode-LDR-instructions.patch
Patch55: objtool-arm64-Accept-non-instruction-data-in-code-se.patch
Patch56: objtool-check-Support-data-in-text-section.patch
Patch57: objtool-arm64-Handle-supported-relocations-in-altern.patch
Patch58: objtool-arm64-Ignore-replacement-section-for-alterna.patch
Patch59: objtool-arm64-Enable-stack-validation-for-arm64.patch
Patch60: Revert-arm64-alternatives-add-shared-NOP-callback.patch
Patch61: objtool-arm64-Add-annotate_reachable-for-objtools.patch
Patch62: arm64-bug-Add-reachable-annotation-to-warning-macros.patch
Patch63: arm64-kgdb-Add-reachable-annotation-after-kgdb-brk.patch
Patch64: objtool-arm64-Add-unwind_hint-support.patch
Patch65: arm64-Change-symbol-type-annotations.patch
Patch66: arm64-Annotate-unwind_hint-for-symbols-with-empty-st.patch
Patch67: arm64-entry-Annotate-unwind_hint-for-entry.patch
Patch68: arm64-kvm-Annotate-unwind_hint-for-hyp-entry.patch
Patch69: arm64-efi-header-Mark-efi-header-as-data.patch
Patch70: arm64-head-Mark-constants-as-data.patch
Patch71: arm64-crypto-Mark-constant-as-data.patch
Patch72: arm64-crypto-Remove-unnecessary-stackframe.patch
Patch73: arm64-Set-intra-function-call-annotations.patch
Patch74: arm64-sleep-Properly-set-frame-pointer-before-call.patch
Patch75: arm64-entry-Align-stack-size-for-alternative.patch
Patch76: arm64-kernel-Skip-validation-of-proton-pack.c.patch
Patch77: arm64-kvm-vgic-v3-sr-Bug-when-trying-to-read-invalid.patch
Patch78: arm64-Introduce-stack-trace-reliability-checks-in-th.patch
Patch79: erm64-Create-a-list-of-SYM_CODE-functions-check-retu.patch
Patch80: arm64-Implement-arch_stack_walk_reliable.patch
Patch81: arm64-Define-HAVE_DYNAMIC_FTRACE_WITH_ARGS.patch
Patch82: arm64-implement-live-patching.patch
Patch83: arm64-module-Use-aarch64_insn_write-when-updating-re.patch
Patch84: crypto-testmgr-disallow-certain-DRBG-hash-functions-.patch
Patch85: crypto-testmgr-disallow-plain-cbcmac-aes-in-FIPS-mod.patch
Patch86: crypto-testmgr-disallow-plain-ghash-in-FIPS-mode.patch
Patch87: crypto-jitter-replace-LFSR-with-SHA3-256.patch
Patch88: crypto-testmgr-Remove-xts4096-paes-and-xts512-paes.patch
Patch89: crypto-ecdh-zeroize-crpytographic-keys-after-use.patch
Patch90: Revert-drm-fb_helper-improve-CONFIG_FB-dependency.patch
Patch91: random-Add-hook-to-override-device-reads-and-getrand.patch
Patch92: crypto-rng-Override-drivers-char-random-in-FIPS-mode.patch
Patch93: crypto-rsa-allow-only-odd-e-and-restrict-value-in-FI.patch
Patch94: crypto-Only-allow-GCM-in-FIPS-when-instantiated-via-.patch
Patch95: crypto-tcrypt.c-Add-selftest-for-ffdhe-algorithims.patch
Patch96: net-ipv6-Improve-performance-of-inet6_ehashfn.patch
Patch97: random-allow-reseeding-DRBG-with-getrandom.patch
Patch98: crypto-rng-Use-a-different-crypto_rng-for-reseeding.patch
Patch99: crypto-dh-Add-SP800-56A-rev-3-Pair-wise-Consistency-.patch
Patch100: crypto-ecc-Add-SP800-56A-rev-3-Pair-wise-Consistency.patch
Patch101: KEYS-use-kfree_sensitive-with-key.patch
Patch102: mm-add-bdi_set_strict_limit-function.patch
Patch103: mm-add-knob-sys-class-bdi-bdi-strict_limit.patch
Patch104: mm-document-sys-class-bdi-bdi-strict_limit-knob.patch
Patch105: ip-Bump-default-ttl-to-127.patch
Patch106: Enable-ptIOMMU-for-all-supported-platforms.patch
Patch107: KEYS-Make-use-of-platform-keyring-for-module-signatu.patch
Patch108: scripts-sign_file-Add-option-to-keep-signing-certifi.patch
Patch109: AL2023-6.1-Update-ena-driver-to-2.8.9g.patch
Patch110: KVM-arm64-Discard-any-SVE-state-when-entering-KVM-gu.patch
Patch111: arm64-fpsimd-Track-the-saved-FPSIMD-state-type-separ.patch
Patch112: arm64-fpsimd-Have-KVM-explicitly-say-which-FP-regist.patch
Patch113: arm64-fpsimd-Stop-using-TIF_SVE-to-manage-register-s.patch
Patch114: arm64-fpsimd-Load-FP-state-based-on-recorded-data-ty.patch
Patch115: arm64-fpsimd-SME-no-longer-requires-SVE-register-sta.patch
Patch116: arm64-sve-Leave-SVE-enabled-on-syscall-if-we-don-t-c.patch
Patch117: KVM-arm64-Prevent-the-donation-of-no-map-pages.patch
Patch118: KVM-arm64-Prevent-unconditional-donation-of-unmapped.patch
Patch119: cgroup-add-cgroup_favordynmods-command-line-option.patch
Patch120: selftests-bpf-add-generic-BPF-program-tester-loader.patch
Patch121: selftests-bpf-convert-dynptr_fail-and-map_kptr_fail-.patch
Patch122: selftests-bpf-convenience-macro-for-use-with-asm-vol.patch
Patch123: selftests-bpf-Add-dynptr-pruning-tests.patch
Patch124: selftests-bpf-Add-dynptr-var_off-tests.patch
Patch125: selftests-bpf-Add-dynptr-partial-slot-overwrite-test.patch
Patch126: bpf-Refactor-ARG_PTR_TO_DYNPTR-checks-into-process_d.patch
Patch127: bpf-Propagate-errors-from-process_-checks-in-check_f.patch
Patch128: bpf-Rework-process_dynptr_func.patch
Patch129: bpf-Rework-check_func_arg_reg_off.patch
Patch130: bpf-Move-PTR_TO_STACK-alignment-check-to-process_dyn.patch
Patch131: bpf-Use-memmove-for-bpf_dynptr_-read-write.patch
Patch132: bpf-Fix-state-pruning-for-STACK_DYNPTR-stack-slots.patch
Patch133: bpf-Fix-missing-var_off-check-for-ARG_PTR_TO_DYNPTR.patch
Patch134: bpf-Fix-partial-dynptr-stack-slot-reads-writes.patch
Patch135: Revert-perf-x86-amd-core-Fix-overflow-reset-on-hotpl.patch
Patch136: AL2023-6.1-Update-ena-driver-to-2.10.0g.patch
Patch137: arm64-Add-ID_DFR0_EL1.PerfMon-values-for-PMUv3p7-and.patch
Patch138: KVM-arm64-PMU-Move-the-ID_AA64DFR0_EL1.PMUver-limit-.patch
Patch139: KVM-arm64-PMU-Allow-ID_AA64DFR0_EL1.PMUver-to-be-set.patch
Patch140: KVM-arm64-PMU-Allow-ID_DFR0_EL1.PerfMon-to-be-set-fr.patch
Patch141: KVM-arm64-Save-ID-registers-sanitized-value-per-gues.patch
Patch142: KVM-arm64-Use-per-guest-ID-register-for-ID_AA64PFR0_.patch
Patch143: KVM-arm64-Use-per-guest-ID-register-for-ID_AA64DFR0_.patch
Patch144: KVM-arm64-Reuse-fields-of-sys_reg_desc-for-idreg.patch
Patch145: KVM-arm64-Refactor-writings-for-PMUVer-CSV2-CSV3.patch
Patch146: KVM-arm64-Update-id_reg-limit-value-based-on-per-vcp.patch
Patch147: KVM-arm64-Move-non-per-vcpu-flag-checks-out-of-kvm_a.patch
Patch148: KVM-arm64-Enable-writable-for-ID_AA64DFR0_EL1.patch
Patch149: KVM-arm64-Enable-writable-for-ID_DFR0_EL1.patch
Patch150: KVM-arm64-Enable-writable-for-ID_AA64PFR0_EL1.patch
Patch151: KVM-arm64-Enable-writable-for-ID_AA64MMFR-0-1-2-_EL1.patch
Patch152: KVM-arm64-Enable-writable-for-ID_AA64ISAR0_EL0.patch
Patch153: KVM-arm64-Enable-writable-for-ID_AA64ISAR1_EL0.patch
Patch154: KVM-arm64-Enable-writable-for-ID_AA64ISAR2_EL0.patch
Patch155: Revert-objtool-Propagate-early-errors.patch
Patch156: AL2023-6.1-Compile-ENA-driver-with-PHC-flag.patch
Patch157: AL2023-6.1-Update-ENA-driver-to-2.11.0g.patch
Patch158: arm64-pauth-don-t-sign-leaf-functions.patch
Patch159: AL2023-6.1-Update-ena-driver-to-2.11.1g.patch
Patch160: AL2023-6.1-Update-EFA-driver-to-2.8.0.patch
Patch161: Config-glue-for-2.15-Lustre-client.patch
Patch162: Initial-2.15-Lustre-client-commit.patch
Patch163: AL2023-6.1-Update-ena-driver-to-2.12.0g.patch
Patch164: x86-sev-Harden-VC-instruction-emulation-somewhat.patch
Patch165: firmware-psci-Add-definitions-for-PSCI-v1.3-specific.patch
Patch166: arm64-Use-SYSTEM_OFF2-PSCI-call-to-power-off-for-hib.patch
Patch167: ACPICA-Detect-FACS-even-for-hardware-reduced-platfor.patch
Patch168: arm64-acpi-Honour-firmware_signature-field-of-FACS-i.patch
Patch169: dma-contiguous-support-per-numa-CMA-for-all-architec.patch
Patch170: dma-contiguous-support-numa-CMA-for-specified-node.patch
Patch171: arm64-mm-Don-t-remap-pgtables-per-cont-pte-pmd-block.patch
Patch172: arm64-mm-Batch-dsb-and-isb-when-populating-pgtables.patch
Patch173: cifs-use-origin-fullpath-for-automounts.patch
Patch174: AL2023-6.1-Update-ena-driver-to-2.12.3g.patch
Patch175: ptp-Add-vDSO-style-vmclock-support.patch
Patch176: virt-vmgenid-change-implementation-to-use-a-platform.patch
Patch177: virt-vmgenid-add-support-for-devicetree-bindings.patch
Patch178: acpi-Support-CONFIG_ACPI-without-CONFIG_PCI.patch
Patch179: drivers-misc-sysgenid-add-system-generation-id-drive.patch
Patch180: dma-Automatically-enable-page-touching-on-Caspian.patch
Patch181: Add-out-of-tree-mpi3mr-8.9.1-driver.patch
Patch182: scsi-mpi3mr-Sanitise-num_phys.patch
Patch183: scsi-mpi3mr-Avoid-memcpy-field-spanning-write-WARNIN.patch
Patch184: bpf-add-mrtt-and-srtt-as-BPF_SOCK_OPS_RTT_CB-args.patch
Patch185: x86-ioremap-Use-is_ioremap_addr-in-iounmap.patch
Patch186: AL2023-6.1-Update-ena-driver-to-2.13.0g.patch
Patch187: AL2023-6.1-Update-lustrefsx-to-2.15.4-fsx7-commit.patch
Patch188: smb-client-fix-use-after-free-in-smb2_query_info_com.patch
Patch189: blk-throttle-Fix-io-statistics-for-cgroup-v1.patch
Patch190: crypto-jitter-add-RCT-APT-support-for-different-OSRs.patch
Patch191: crypto-jitter-Allow-configuration-of-oversampling-ra.patch
Patch192: crypto-jitter-set-default-OSR-to-3.patch
Patch193: Revert-ext4-don-t-set-SB_RDONLY-after-filesystem-err.patch
Patch194: LU-17887-obd-do-not-update-obd_memory-from-RCU.patch
Patch195: smb-client-Fix-use-after-free-of-network-namespace.patch
Patch196: AL2023-6.1-Update-ena-driver-to-2.13.2g.patch
Patch197: AL2023-6.1-Update-EFA-driver-to-2.13.0.patch
Patch198: AL2023-6.1-Update-lustrefsx-to-2.15.6-fsx13-commit.patch
Patch199: fs-ntfs3-Add-rough-attr-alloc_size-check.patch

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
%package -n perf
Summary: Performance monitoring for the Linux kernel
Group: Development/System
Requires: libzstd
License: GPLv2
%description -n perf
This package contains the perf tool, which enables performance monitoring
of the Linux kernel.

%package -n perf-debuginfo
Summary: Debug information for package perf
Group: Development/Debug
Requires: %{name}-debuginfo-common-%{_target_cpu} = %{version}-%{release}
AutoReqProv: no
%description -n perf-debuginfo
This package provides debug information for the perf package.

# Note that this pattern only works right to match the .build-id
# symlinks because of the trailing nonmatching alternation and
# the leading .*, because of find-debuginfo.sh's buggy handling
# of matching the pattern against the symlinks file.
%{expand:%%global _find_debuginfo_opts %{?_find_debuginfo_opts} -p '.*%%{_bindir}/perf(\.debug)?|.*%%{_libexecdir}/perf-core/.*|.*%%{_libdir}/traceevent/plugins/.*|.*%%{_libdir}/libperf-jvmti.so(\.debug)?|XXX' -o perf-debuginfo.list}

%package -n %{py_pkg_prefix}-perf
Summary: Python bindings for apps which will manipulate perf events
Group: Development/Libraries
%description -n %{py_pkg_prefix}-perf
The python-perf package contains a module that permits applications
written in the Python programming language to use the interface
to manipulate perf events.

%package -n %{py_pkg_prefix}-perf-debuginfo
Summary: Debug information for package perf python bindings
Group: Development/Debug
Requires: %{name}-debuginfo-common-%{_target_cpu} = %{version}-%{release}
AutoReqProv: no
%description -n %{py_pkg_prefix}-perf-debuginfo
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
Provides: kernel-tools-libs = %{version}-%{release}
%endif

%description tools
This package contains the tools/ directory from the kernel source
and the supporting documentation.

%package tools-devel
Summary: Assortment of tools for the Linux kernel
Group: Development/System
License: GPLv2
Requires: kernel-tools = %{version}-%{release}
%ifarch %{cpupowerarchs}
Provides:  cpupowerutils-devel = 1:009-0.6.p1
Obsoletes: cpupowerutils-devel < 1:009-0.6.p1
%endif
%if 0%{?amzn} >= 2022
Obsoletes: kernel-tools-libs-devel < 5.15
Provides: kernel-tools-libs-devel = %{version}-%{release}
%endif

%description tools-devel
This package contains the development files for the tools/ directory from
the kernel source.

%package tools-debuginfo
Summary: Debug information for package kernel-tools
Group: Development/Debug
Requires: %{name}-debuginfo-common-%{_target_cpu} = %{version}-%{release}
AutoReqProv: no
%description tools-debuginfo
This package provides debug information for package kernel-tools.

# Note that this pattern only works right to match the .build-id
# symlinks because of the trailing nonmatching alternation and
# the leading .*, because of find-debuginfo.sh's buggy handling
# of matching the pattern against the symlinks file.
%{expand:%%global _find_debuginfo_opts %{?_find_debuginfo_opts} -p '.*%%{_bindir}/centrino-decode(\.debug)?|.*%%{_bindir}/powernow-k8-decode(\.debug)?|.*%%{_bindir}/cpupower(\.debug)?|.*%%{_libdir}/libcpupower.*|XXX' -o kernel-tools-debuginfo.list}
%endif

%if %{with_bpftool}

%package -n bpftool
Summary: Inspection and simple manipulation of eBPF programs and maps
License: GPLv2
%description -n bpftool
This package contains the bpftool, which allows inspection and simple
manipulation of eBPF programs and maps.

%package -n bpftool-debuginfo
Summary: Debug information for package bpftool
Group: Development/Debug
Requires: %{name}-debuginfo-common-%{_target_cpu} = %{version}-%{release}
AutoReqProv: no
%description -n bpftool-debuginfo
This package provides debug information for the bpftool package.

%{expand:%%global _find_debuginfo_opts %{?_find_debuginfo_opts} -p '.*%%{_sbindir}/bpftool(\.debug)?|XXX' -o bpftool-debuginfo.list}

# with_bpftool
%endif

%if %{with_libbpf}

%package libbpf
Summary: Libbpf library
License: LGPLv2 or BSD
Provides: libbpf = %{libbpf_version}
%description libbpf
This package contains the libbpf library built from kernel sources. 

%package libbpf-devel
Summary: Development files for libbpf
Requires: kernel-headers >= %{kversion}
Requires: zlib
Provides: libbpf-devel = %{libbpf_version}
%description libbpf-devel
The libbpf-devel package contains libraries header files for
developing applications that use libbpf

%package libbpf-static
Summary: Static library for libbpf development
Provides: libbpf-static = %{libbpf_version}
%description libbpf-static
The libbpf-static package contains static library for
developing applications that use libbpf

# with_libbpf
%endif

%if %{with_mods_extra}
%package modules-extra-common
Summary: Common files for the kernel modules extra package
Group: System Environment/Kernel
%description modules-extra-common
This package provides some global configuration files used to ensure
that some of the modules in the kernel-modules-extra package are
properly loaded at boot time.
%endif

#
# This macro creates a kernel-<subpackage>-debuginfo package.
#	%%kernel_debuginfo_package <subpackage>
#
%define kernel_debuginfo_package() \
%package %{?1:%{1}-}debuginfo\
Summary: Debug information for package %{name}%{?1:-%{1}}\
Group: Development/Debug\
Requires: %{name}-debuginfo-common-%{_target_cpu} = %{version}-%{release}\
Provides: %{name}%{?1:-%{1}}-debuginfo-%{_target_cpu} = %{version}-%{release}\
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
Provides: kernel%{?1:-%{1}}-devel-%{_target_cpu} = %{version}-%{release}\
Provides: kernel-devel-%{_target_cpu} = %{version}-%{release}%{?1:.%{1}}\
Provides: kernel-devel = %{version}-%{release}%{?1:.%{1}}\
Provides: kernel-devel-uname-r = %{KVERREL}%{?1:.%{1}}\
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
%description -n kernel%{?variant}%{?1:-%{1}}-devel\
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
Provides: kernel%{?1:-%{1}}-modules-extra-%{_target_cpu} = %{version}-%{release}\
Provides: kernel%{?1:-%{1}}-modules-extra-%{_target_cpu} = %{version}-%{release}%{?1:.%{1}}\
Provides: kernel%{?1:-%{1}}-modules-extra = %{version}-%{release}%{release}%{?1:.%{1}}\
Provides: installonlypkg(kernel-module)\
Provides: kernel%{?1:-%{1}}-modules-extra-uname-r = %{KVERREL}%{?1:+%{1}}\
Requires: kernel-uname-r = %{KVERREL}%{?1:+%{1}}\
Requires: kernel-modules-extra-common >= %{rpmversion}-%{pkg_release}\
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
ApplyPatch mm-memcg-throttle-the-memory-reclaim-given-dirty-wri.patch
ApplyPatch Sysfs-memory-probe-interface.patch
ApplyPatch arm64-mm-Enable-sysfs-based-memory-hot-remove-probe.patch
ApplyPatch memory-fix-offline_and_remove_memory-use.patch
ApplyPatch drivers-base-memory-use-MHP_MEMMAP_ON_MEMORY-from-th.patch
ApplyPatch mm-add-offline-page-reporting-interface.patch
ApplyPatch virtio-add-hack-to-allow-pre-mapped-scatterlists.patch
ApplyPatch virtio-balloon-optionally-report-offlined-memory-ran.patch
ApplyPatch Introduce-page-touching-DMA-ops-binding.patch
ApplyPatch Correct-read-overflow-in-page-touching-DMA-ops-bindi.patch
ApplyPatch x86-Disable-KASLR-when-Xen-is-detected.patch
ApplyPatch arm64-Export-acpi_psci_use_hvc-symbol.patch
ApplyPatch hwrng-Add-Gravition-RNG-driver.patch
ApplyPatch drivers-introduce-AMAZON_DRIVER_UPDATES.patch
ApplyPatch drivers-amazon-import-5.15-drivers.patch
ApplyPatch ENA-Update-to-v2.8.1.patch
ApplyPatch EFA-Update-to-v2.1.1.patch
ApplyPatch Enable-Algorithims-for-Amazon-Linux-6.1.y.patch
ApplyPatch xen-manage-keep-track-of-the-on-going-suspend-mode.patch
ApplyPatch xen-manage-introduce-helper-function-to-know-the-on-.patch
ApplyPatch xenbus-add-freeze-thaw-restore-callbacks-support.patch
ApplyPatch x86-xen-Introduce-new-function-to-map-HYPERVISOR_sha.patch
ApplyPatch x86-xen-add-system-core-suspend-and-resume-callbacks.patch
ApplyPatch xen-blkfront-add-callbacks-for-PM-suspend-and-hibern.patch
ApplyPatch xen-netfront-add-callbacks-for-PM-suspend-and-hibern.patch
ApplyPatch xen-time-introduce-xen_-save-restore-_steal_clock.patch
ApplyPatch x86-xen-save-and-restore-steal-clock.patch
ApplyPatch xen-events-add-xen_shutdown_pirqs-helper-function.patch
ApplyPatch x86-xen-close-event-channels-for-PIRQs-in-system-cor.patch
ApplyPatch PM-hibernate-update-the-resume-offset-on-SNAPSHOT_SE.patch
ApplyPatch Revert-xen-dont-fiddle-with-event-channel-masking-in.patch
ApplyPatch xen-blkfront-Fixed-blkfront_restore-to-remove-a-call.patch
ApplyPatch x86-tsc-avoid-system-instability-in-hibernation.patch
ApplyPatch block-xen-blkfront-consider-new-dom0-features-on-res.patch
ApplyPatch xen-restore-pirqs-on-resume-from-hibernation.patch
ApplyPatch xen-Only-restore-the-ACPI-SCI-interrupt-in-xen_resto.patch
ApplyPatch xen-netfront-call-netif_device_attach-on-resume.patch
ApplyPatch xen-Restore-xen-pirqs-on-resume-from-hibernation.patch
ApplyPatch block-xen-blkfront-bump-the-maximum-number-of-indire.patch
ApplyPatch Revert-PCI-MSI-Let-core-code-free-MSI-descriptors.patch
ApplyPatch Revert-xen-x2apic-enable-x2apic-mode-when-supported-.patch
ApplyPatch msr-disable-MSR-writes-by-default.patch
ApplyPatch udp-Fix-memleaks-of-sk-and-zerocopy-skbs-with-TX-tim.patch
ApplyPatch ENA-Update-to-v2.8.3.patch
ApplyPatch Revert-selinux-runtime-disable-is-deprecated-add-som.patch
ApplyPatch AL2023-6.1-Update-ena-driver-to-2.8.6g.patch
ApplyPatch objtool-Add-generic-symbol-for-relocation-type.patch
ApplyPatch objtool-Specify-host-arch-for-making-LIBSUBCMD.patch
ApplyPatch tools-arm64-Make-aarch64-instruction-decoder-availab.patch
ApplyPatch objtool-arm64-Add-base-definition-for-arm64-backend.patch
ApplyPatch objtool-arm64-Decode-add-sub-instructions.patch
ApplyPatch objtool-arm64-Decode-jump-and-call-related-instructi.patch
ApplyPatch objtool-arm64-Decode-other-system-instructions.patch
ApplyPatch objtool-arm64-Decode-load-store-instructions.patch
ApplyPatch objtool-arm64-Decode-LDR-instructions.patch
ApplyPatch objtool-arm64-Accept-non-instruction-data-in-code-se.patch
ApplyPatch objtool-check-Support-data-in-text-section.patch
ApplyPatch objtool-arm64-Handle-supported-relocations-in-altern.patch
ApplyPatch objtool-arm64-Ignore-replacement-section-for-alterna.patch
ApplyPatch objtool-arm64-Enable-stack-validation-for-arm64.patch
ApplyPatch Revert-arm64-alternatives-add-shared-NOP-callback.patch
ApplyPatch objtool-arm64-Add-annotate_reachable-for-objtools.patch
ApplyPatch arm64-bug-Add-reachable-annotation-to-warning-macros.patch
ApplyPatch arm64-kgdb-Add-reachable-annotation-after-kgdb-brk.patch
ApplyPatch objtool-arm64-Add-unwind_hint-support.patch
ApplyPatch arm64-Change-symbol-type-annotations.patch
ApplyPatch arm64-Annotate-unwind_hint-for-symbols-with-empty-st.patch
ApplyPatch arm64-entry-Annotate-unwind_hint-for-entry.patch
ApplyPatch arm64-kvm-Annotate-unwind_hint-for-hyp-entry.patch
ApplyPatch arm64-efi-header-Mark-efi-header-as-data.patch
ApplyPatch arm64-head-Mark-constants-as-data.patch
ApplyPatch arm64-crypto-Mark-constant-as-data.patch
ApplyPatch arm64-crypto-Remove-unnecessary-stackframe.patch
ApplyPatch arm64-Set-intra-function-call-annotations.patch
ApplyPatch arm64-sleep-Properly-set-frame-pointer-before-call.patch
ApplyPatch arm64-entry-Align-stack-size-for-alternative.patch
ApplyPatch arm64-kernel-Skip-validation-of-proton-pack.c.patch
ApplyPatch arm64-kvm-vgic-v3-sr-Bug-when-trying-to-read-invalid.patch
ApplyPatch arm64-Introduce-stack-trace-reliability-checks-in-th.patch
ApplyPatch erm64-Create-a-list-of-SYM_CODE-functions-check-retu.patch
ApplyPatch arm64-Implement-arch_stack_walk_reliable.patch
ApplyPatch arm64-Define-HAVE_DYNAMIC_FTRACE_WITH_ARGS.patch
ApplyPatch arm64-implement-live-patching.patch
ApplyPatch arm64-module-Use-aarch64_insn_write-when-updating-re.patch
ApplyPatch crypto-testmgr-disallow-certain-DRBG-hash-functions-.patch
ApplyPatch crypto-testmgr-disallow-plain-cbcmac-aes-in-FIPS-mod.patch
ApplyPatch crypto-testmgr-disallow-plain-ghash-in-FIPS-mode.patch
ApplyPatch crypto-jitter-replace-LFSR-with-SHA3-256.patch
ApplyPatch crypto-testmgr-Remove-xts4096-paes-and-xts512-paes.patch
ApplyPatch crypto-ecdh-zeroize-crpytographic-keys-after-use.patch
ApplyPatch Revert-drm-fb_helper-improve-CONFIG_FB-dependency.patch
ApplyPatch random-Add-hook-to-override-device-reads-and-getrand.patch
ApplyPatch crypto-rng-Override-drivers-char-random-in-FIPS-mode.patch
ApplyPatch crypto-rsa-allow-only-odd-e-and-restrict-value-in-FI.patch
ApplyPatch crypto-Only-allow-GCM-in-FIPS-when-instantiated-via-.patch
ApplyPatch crypto-tcrypt.c-Add-selftest-for-ffdhe-algorithims.patch
ApplyPatch net-ipv6-Improve-performance-of-inet6_ehashfn.patch
ApplyPatch random-allow-reseeding-DRBG-with-getrandom.patch
ApplyPatch crypto-rng-Use-a-different-crypto_rng-for-reseeding.patch
ApplyPatch crypto-dh-Add-SP800-56A-rev-3-Pair-wise-Consistency-.patch
ApplyPatch crypto-ecc-Add-SP800-56A-rev-3-Pair-wise-Consistency.patch
ApplyPatch KEYS-use-kfree_sensitive-with-key.patch
ApplyPatch mm-add-bdi_set_strict_limit-function.patch
ApplyPatch mm-add-knob-sys-class-bdi-bdi-strict_limit.patch
ApplyPatch mm-document-sys-class-bdi-bdi-strict_limit-knob.patch
ApplyPatch ip-Bump-default-ttl-to-127.patch
ApplyPatch Enable-ptIOMMU-for-all-supported-platforms.patch
ApplyPatch KEYS-Make-use-of-platform-keyring-for-module-signatu.patch
ApplyPatch scripts-sign_file-Add-option-to-keep-signing-certifi.patch
ApplyPatch AL2023-6.1-Update-ena-driver-to-2.8.9g.patch
ApplyPatch KVM-arm64-Discard-any-SVE-state-when-entering-KVM-gu.patch
ApplyPatch arm64-fpsimd-Track-the-saved-FPSIMD-state-type-separ.patch
ApplyPatch arm64-fpsimd-Have-KVM-explicitly-say-which-FP-regist.patch
ApplyPatch arm64-fpsimd-Stop-using-TIF_SVE-to-manage-register-s.patch
ApplyPatch arm64-fpsimd-Load-FP-state-based-on-recorded-data-ty.patch
ApplyPatch arm64-fpsimd-SME-no-longer-requires-SVE-register-sta.patch
ApplyPatch arm64-sve-Leave-SVE-enabled-on-syscall-if-we-don-t-c.patch
ApplyPatch KVM-arm64-Prevent-the-donation-of-no-map-pages.patch
ApplyPatch KVM-arm64-Prevent-unconditional-donation-of-unmapped.patch
ApplyPatch cgroup-add-cgroup_favordynmods-command-line-option.patch
ApplyPatch selftests-bpf-add-generic-BPF-program-tester-loader.patch
ApplyPatch selftests-bpf-convert-dynptr_fail-and-map_kptr_fail-.patch
ApplyPatch selftests-bpf-convenience-macro-for-use-with-asm-vol.patch
ApplyPatch selftests-bpf-Add-dynptr-pruning-tests.patch
ApplyPatch selftests-bpf-Add-dynptr-var_off-tests.patch
ApplyPatch selftests-bpf-Add-dynptr-partial-slot-overwrite-test.patch
ApplyPatch bpf-Refactor-ARG_PTR_TO_DYNPTR-checks-into-process_d.patch
ApplyPatch bpf-Propagate-errors-from-process_-checks-in-check_f.patch
ApplyPatch bpf-Rework-process_dynptr_func.patch
ApplyPatch bpf-Rework-check_func_arg_reg_off.patch
ApplyPatch bpf-Move-PTR_TO_STACK-alignment-check-to-process_dyn.patch
ApplyPatch bpf-Use-memmove-for-bpf_dynptr_-read-write.patch
ApplyPatch bpf-Fix-state-pruning-for-STACK_DYNPTR-stack-slots.patch
ApplyPatch bpf-Fix-missing-var_off-check-for-ARG_PTR_TO_DYNPTR.patch
ApplyPatch bpf-Fix-partial-dynptr-stack-slot-reads-writes.patch
ApplyPatch Revert-perf-x86-amd-core-Fix-overflow-reset-on-hotpl.patch
ApplyPatch AL2023-6.1-Update-ena-driver-to-2.10.0g.patch
ApplyPatch arm64-Add-ID_DFR0_EL1.PerfMon-values-for-PMUv3p7-and.patch
ApplyPatch KVM-arm64-PMU-Move-the-ID_AA64DFR0_EL1.PMUver-limit-.patch
ApplyPatch KVM-arm64-PMU-Allow-ID_AA64DFR0_EL1.PMUver-to-be-set.patch
ApplyPatch KVM-arm64-PMU-Allow-ID_DFR0_EL1.PerfMon-to-be-set-fr.patch
ApplyPatch KVM-arm64-Save-ID-registers-sanitized-value-per-gues.patch
ApplyPatch KVM-arm64-Use-per-guest-ID-register-for-ID_AA64PFR0_.patch
ApplyPatch KVM-arm64-Use-per-guest-ID-register-for-ID_AA64DFR0_.patch
ApplyPatch KVM-arm64-Reuse-fields-of-sys_reg_desc-for-idreg.patch
ApplyPatch KVM-arm64-Refactor-writings-for-PMUVer-CSV2-CSV3.patch
ApplyPatch KVM-arm64-Update-id_reg-limit-value-based-on-per-vcp.patch
ApplyPatch KVM-arm64-Move-non-per-vcpu-flag-checks-out-of-kvm_a.patch
ApplyPatch KVM-arm64-Enable-writable-for-ID_AA64DFR0_EL1.patch
ApplyPatch KVM-arm64-Enable-writable-for-ID_DFR0_EL1.patch
ApplyPatch KVM-arm64-Enable-writable-for-ID_AA64PFR0_EL1.patch
ApplyPatch KVM-arm64-Enable-writable-for-ID_AA64MMFR-0-1-2-_EL1.patch
ApplyPatch KVM-arm64-Enable-writable-for-ID_AA64ISAR0_EL0.patch
ApplyPatch KVM-arm64-Enable-writable-for-ID_AA64ISAR1_EL0.patch
ApplyPatch KVM-arm64-Enable-writable-for-ID_AA64ISAR2_EL0.patch
ApplyPatch Revert-objtool-Propagate-early-errors.patch
ApplyPatch AL2023-6.1-Compile-ENA-driver-with-PHC-flag.patch
ApplyPatch AL2023-6.1-Update-ENA-driver-to-2.11.0g.patch
ApplyPatch arm64-pauth-don-t-sign-leaf-functions.patch
ApplyPatch AL2023-6.1-Update-ena-driver-to-2.11.1g.patch
ApplyPatch AL2023-6.1-Update-EFA-driver-to-2.8.0.patch
ApplyPatch Config-glue-for-2.15-Lustre-client.patch
ApplyPatch Initial-2.15-Lustre-client-commit.patch
ApplyPatch AL2023-6.1-Update-ena-driver-to-2.12.0g.patch
ApplyPatch x86-sev-Harden-VC-instruction-emulation-somewhat.patch
ApplyPatch firmware-psci-Add-definitions-for-PSCI-v1.3-specific.patch
ApplyPatch arm64-Use-SYSTEM_OFF2-PSCI-call-to-power-off-for-hib.patch
ApplyPatch ACPICA-Detect-FACS-even-for-hardware-reduced-platfor.patch
ApplyPatch arm64-acpi-Honour-firmware_signature-field-of-FACS-i.patch
ApplyPatch dma-contiguous-support-per-numa-CMA-for-all-architec.patch
ApplyPatch dma-contiguous-support-numa-CMA-for-specified-node.patch
ApplyPatch arm64-mm-Don-t-remap-pgtables-per-cont-pte-pmd-block.patch
ApplyPatch arm64-mm-Batch-dsb-and-isb-when-populating-pgtables.patch
ApplyPatch cifs-use-origin-fullpath-for-automounts.patch
ApplyPatch AL2023-6.1-Update-ena-driver-to-2.12.3g.patch
ApplyPatch ptp-Add-vDSO-style-vmclock-support.patch
ApplyPatch virt-vmgenid-change-implementation-to-use-a-platform.patch
ApplyPatch virt-vmgenid-add-support-for-devicetree-bindings.patch
ApplyPatch acpi-Support-CONFIG_ACPI-without-CONFIG_PCI.patch
ApplyPatch drivers-misc-sysgenid-add-system-generation-id-drive.patch
ApplyPatch dma-Automatically-enable-page-touching-on-Caspian.patch
ApplyPatch Add-out-of-tree-mpi3mr-8.9.1-driver.patch
ApplyPatch scsi-mpi3mr-Sanitise-num_phys.patch
ApplyPatch scsi-mpi3mr-Avoid-memcpy-field-spanning-write-WARNIN.patch
ApplyPatch bpf-add-mrtt-and-srtt-as-BPF_SOCK_OPS_RTT_CB-args.patch
ApplyPatch x86-ioremap-Use-is_ioremap_addr-in-iounmap.patch
ApplyPatch AL2023-6.1-Update-ena-driver-to-2.13.0g.patch
ApplyPatch AL2023-6.1-Update-lustrefsx-to-2.15.4-fsx7-commit.patch
ApplyPatch smb-client-fix-use-after-free-in-smb2_query_info_com.patch
ApplyPatch blk-throttle-Fix-io-statistics-for-cgroup-v1.patch
ApplyPatch crypto-jitter-add-RCT-APT-support-for-different-OSRs.patch
ApplyPatch crypto-jitter-Allow-configuration-of-oversampling-ra.patch
ApplyPatch crypto-jitter-set-default-OSR-to-3.patch
ApplyPatch Revert-ext4-don-t-set-SB_RDONLY-after-filesystem-err.patch
ApplyPatch LU-17887-obd-do-not-update-obd_memory-from-RCU.patch
ApplyPatch smb-client-Fix-use-after-free-of-network-namespace.patch
ApplyPatch AL2023-6.1-Update-ena-driver-to-2.13.2g.patch
ApplyPatch AL2023-6.1-Update-EFA-driver-to-2.13.0.patch
ApplyPatch AL2023-6.1-Update-lustrefsx-to-2.15.6-fsx13-commit.patch
ApplyPatch fs-ntfs3-Add-rough-attr-alloc_size-check.patch

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

    # Make sure the files lists start with absolute paths or rpmbuild fails.
    sed -e 's/^lib*/\/lib/' $RPM_BUILD_ROOT/mod-extra.list >> ../kernel${Flavour:+-${Flavour}}-modules-extra.list
    rm -f $RPM_BUILD_ROOT/mod-extra.list
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

%if %{with_up}
install -D -m644 %{SOURCE70} %{buildroot}%{_rpmconfigdir}/macros.d/macros.kmod-sign
%endif

# Install udev and dracut rules for modules-extra
%if %{with_mods_extra}
mkdir -p %{buildroot}%{_udevrulesdir}
install -m644 %{SOURCE100} %{buildroot}%{_udevrulesdir}/61-drm-simplefb.rules
mkdir -p %{buildroot}%{_libdir}/dracut/modules.d/51drm-simplefb
install -D -m 755 %{SOURCE101} %{buildroot}%{dracutlibdir}/modules.d/51drm-simplefb/module-setup.sh
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


%define set_need_to_run_dracut() \
if [ ! -f %{_localstatedir}/lib/rpm-state/%{name}/installing_%{KVERREL}%{?1:+%{1}} ]; then\
	mkdir -p %{_localstatedir}/lib/rpm-state/%{name}\
	touch %{_localstatedir}/lib/rpm-state/%{name}/need_to_run_dracut_%{KVERREL}%{?1:+%{1}}\
fi\
%{nil}

%define check_and_run_dracut() \
if [ -f %{_localstatedir}/lib/rpm-state/%{name}/need_to_run_dracut_%{KVERREL}%{?1:+%{1}} ]; then\
	rm -f %{_localstatedir}/lib/rpm-state/%{name}/need_to_run_dracut_%{KVERREL}%{?1:+%{1}}\
	echo "Running: dracut -f --kver %{KVERREL}%{?1:+%{1}}"\
	dracut -f --kver "%{KVERREL}%{?1:+%{1}}" || exit $?\
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
/sbin/depmod -a %{KVERREL}%{?1:+%{1}}\
%{expand:%%set_need_to_run_dracut}\
%{nil}\
%{expand:%%postun %{?1:%{1}-}modules-extra}\
/sbin/depmod -a %{KVERREL}%{?1:+%{1}}\
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
%files -n perf
%defattr(-,root,root)
%{_bindir}/perf
%{_libdir}/libperf-jvmti.so
%{_bindir}/trace
%dir %{_libexecdir}/perf-core
%{_libexecdir}/perf-core/*
%{_datadir}/perf-core/*
%{_datadir}/doc/perf*/*
%dir %{_libdir}/traceevent/plugins
%{_libdir}/traceevent/plugins/*
%{_mandir}/man[1-8]/perf*
%{_prefix}/lib/perf/examples/*
%{_prefix}/lib/perf/include/*
%doc linux-%{KVERREL}/tools/perf/Documentation/examples.txt

%files -n %{py_pkg_prefix}-perf
%defattr(-,root,root)
%{python_sitearch}/*

%if %{with_debuginfo}
%files -f perf-debuginfo.list -n perf-debuginfo
%defattr(-,root,root)

%files -f %{py_pkg_prefix}-perf-debuginfo.list -n %{py_pkg_prefix}-perf-debuginfo
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
%{_libdir}/libcpupower.so.0
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
%files -n bpftool
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
%files -f bpftool-debuginfo.list -n bpftool-debuginfo
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
%{_rpmconfigdir}/macros.d/macros.kmod-sign\
%if %{with_mods_extra}\
%{expand:%%files -f kernel-%{?3:%{2}-}modules-extra.list %{?2:%{2}-}modules-extra}\
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
Requires: kernel = %{rpmversion}-%{pkg_release}
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

%changelog
* Mon Feb 10 2025 Builder <builder@amazon.com>
- builder/824bf58dbeedac25f5fb785e1bc26fdf9fe8184c last changes:
  + [824bf58d] [2025-02-10] 6.1: Rebase to 6.1.128 (pjy@amazon.com)

- linux last changes:
  + [2024-08-19] fs/ntfs3: Add rough attr alloc_size check (almaz.alexandrovich@paragon-software.com)
  + [2025-01-10] AL2023 6.1: Update lustrefsx to 2.15.6-fsx13 commit (ec2-user@ip-10-0-1-13.ec2.internal)
  + [2024-12-18] AL2023 6.1 Update EFA driver to 2.13.0 (mrgolin@amazon.com)
  + [2025-01-02] AL2023-6.1-Update-ena-driver-to-2.13.2g (darinzon@amazon.com)
  + [2024-11-02] smb: client: Fix use-after-free of network namespace. (kuniyu@amazon.com)
  + [2024-11-25] LU-17887 obd: do not update obd_memory from RCU (doebel@amazon.de)
  + [2024-11-05] Revert "ext4: don't set SB_RDONLY after filesystem errors" (mngyadam@amazon.com)
  + [2024-08-12] crypto: jitter - set default OSR to 3 (smueller@chronox.de)
  + [2023-09-21] crypto: jitter - Allow configuration of oversampling rate (smueller@chronox.de)
  + [2023-09-21] crypto: jitter - add RCT/APT support for different OSRs (smueller@chronox.de)
  + [2023-05-08] blk-throttle: Fix io statistics for cgroup v1 (hanjinke.666@bytedance.com)
  + [2023-10-30] smb: client: fix use-after-free in smb2_query_info_compound() (pc@manguebit.com)
  + [2024-10-02] AL2023 6.1: Update lustrefsx to 2.15.4-fsx7 commit (ec2-user@ip-172-31-75-126.ec2.internal)
  + [2024-09-18] AL2023-6.1-Update-ena-driver-to-2.13.0g (darinzon@amazon.com)
  + [2024-08-15] x86/ioremap: Use is_ioremap_addr() in iounmap() (max8rr8@gmail.com)
  + [2024-04-26] bpf: add mrtt and srtt as BPF_SOCK_OPS_RTT_CB args (lulie@linux.alibaba.com)
  + [2024-08-07] scsi: mpi3mr: Avoid memcpy field-spanning write WARNING (mngyadam@amazon.com)
  + [2024-08-07] scsi: mpi3mr: Sanitise num_phys (mngyadam@amazon.com)
  + [2024-08-07] Add out-of-tree mpi3mr 8.9.1 driver (mngyadam@amazon.com)
  + [2024-07-23] dma: Automatically enable page touching on Caspian (dwmw@amazon.co.uk)
  + [2021-02-24] drivers/misc: sysgenid: add system generation id driver (acatan@amazon.com)
  + [2024-06-13] acpi: Support CONFIG_ACPI without CONFIG_PCI (surajjs@amazon.com)
  + [2024-04-17] virt: vmgenid: add support for devicetree bindings (sudanl@amazon.com)
  + [2024-04-17] virt: vmgenid: change implementation to use a platform driver (sudanl@amazon.com)
  + [2024-07-24] ptp: Add vDSO-style vmclock support (dwmw@amazon.co.uk)
  + [2024-07-12] AL2023-6.1-Update-ena-driver-to-2.12.3g (akiyano@amazon.com)
  + [2022-12-18] cifs: use origin fullpath for automounts (pc@cjr.nz)
  + [2024-06-05] arm64: mm: Batch dsb and isb when populating pgtables (ryan.roberts@arm.com)
  + [2024-06-05] arm64: mm: Don't remap pgtables per-cont(pte|pmd) block (ryan.roberts@arm.com)
  + [2023-07-12] dma-contiguous: support numa CMA for specified node (yajun.deng@linux.dev)
  + [2023-05-12] dma-contiguous: support per-numa CMA for all architectures (yajun.deng@linux.dev)
  + [2024-03-11] arm64: acpi: Honour firmware_signature field of FACS, if it exists (dwmw@amazon.co.uk)
  + [2024-03-11] ACPICA: Detect FACS even for hardware reduced platforms (dwmw@amazon.co.uk)
  + [2024-03-11] arm64: Use SYSTEM_OFF2 PSCI call to power off for hibernate (dwmw@amazon.co.uk)
  + [2024-03-18] firmware/psci: Add definitions for PSCI v1.3 specification (ALPHA) (dwmw@amazon.co.uk)
  + [2024-01-05] x86/sev: Harden #VC instruction emulation somewhat (bp@alien8.de)
  + [2024-03-19] AL2023-6.1-Update-ena-driver-to-2.12.0g (evostrov@amazon.com)
  + [2024-03-09] Initial 2.15 Lustre client commit (jacwolf@amazon.com)
  + [2024-03-09] Config glue for 2.15 Lustre client (jacwolf@amazon.com)
  + [2024-02-20] AL2023 6.1 Update EFA driver to 2.8.0 (mrgolin@amazon.com)
  + [2024-02-07] AL2023-6.1-Update-ena-driver-to-2.11.1g (darinzon@amazon.com)
  + [2023-01-31] arm64: pauth: don't sign leaf functions (mark.rutland@arm.com)
  + [2023-11-28] AL2023 6.1 Update ENA driver to 2.11.0g (darinzon@amazon.com)
  + [2023-11-28] AL2023 6.1 Compile ENA driver with PHC flag (darinzon@amazon.com)
  + [2023-12-13] Revert "objtool: Propagate early errors" (apanyaki@amazon.com)
  + [2023-06-23] KVM: arm64: Enable writable for ID_AA64ISAR2_EL0 (surajjs@amazon.com)
  + [2023-06-23] KVM: arm64: Enable writable for ID_AA64ISAR1_EL0 (surajjs@amazon.com)
  + [2023-06-22] KVM: arm64: Enable writable for ID_AA64ISAR0_EL0 (surajjs@amazon.com)
  + [2023-06-07] KVM: arm64: Enable writable for ID_AA64MMFR{0, 1, 2}_EL1 (jingzhangos@google.com)
  + [2023-06-07] KVM: arm64: Enable writable for ID_AA64PFR0_EL1 (jingzhangos@google.com)
  + [2023-06-07] KVM: arm64: Enable writable for ID_DFR0_EL1 (jingzhangos@google.com)
  + [2023-06-07] KVM: arm64: Enable writable for ID_AA64DFR0_EL1 (jingzhangos@google.com)
  + [2023-06-02] KVM: arm64: Move non per vcpu flag checks out of kvm_arm_update_id_reg() (surajjs@amazon.com)
  + [2023-06-02] KVM: arm64: Update id_reg limit value based on per vcpu flags (surajjs@amazon.com)
  + [2023-06-02] KVM: arm64: Refactor writings for PMUVer/CSV2/CSV3 (jingzhangos@google.com)
  + [2023-06-02] KVM: arm64: Reuse fields of sys_reg_desc for idreg (jingzhangos@google.com)
  + [2023-06-02] KVM: arm64: Use per guest ID register for ID_AA64DFR0_EL1.PMUVer (jingzhangos@google.com)
  + [2023-06-02] KVM: arm64: Use per guest ID register for ID_AA64PFR0_EL1.[CSV2|CSV3] (jingzhangos@google.com)
  + [2023-06-02] KVM: arm64: Save ID registers' sanitized value per guest (jingzhangos@google.com)
  + [2022-11-13] KVM: arm64: PMU: Allow ID_DFR0_EL1.PerfMon to be set from userspace (maz@kernel.org)
  + [2022-11-13] KVM: arm64: PMU: Allow ID_AA64DFR0_EL1.PMUver to be set from userspace (maz@kernel.org)
  + [2022-11-13] KVM: arm64: PMU: Move the ID_AA64DFR0_EL1.PMUver limit to VM creation (maz@kernel.org)
  + [2022-11-13] arm64: Add ID_DFR0_EL1.PerfMon values for PMUv3p7 and IMP_DEF (maz@kernel.org)
  + [2023-10-31] AL2023-6.1-Update-ena-driver-to-2.10.0g (darinzon@amazon.com)
  + [2023-10-22] Revert "perf/x86/amd/core: Fix overflow reset on hotplug" (shaoyi@amazon.com)
  + [2023-01-21] bpf: Fix partial dynptr stack slot reads/writes (memxor@gmail.com)
  + [2023-01-21] bpf: Fix missing var_off check for ARG_PTR_TO_DYNPTR (memxor@gmail.com)
  + [2023-01-21] bpf: Fix state pruning for STACK_DYNPTR stack slots (memxor@gmail.com)
  + [2022-12-08] bpf: Use memmove for bpf_dynptr_{read,write} (memxor@gmail.com)
  + [2022-12-08] bpf: Move PTR_TO_STACK alignment check to process_dynptr_func (memxor@gmail.com)
  + [2022-12-08] bpf: Rework check_func_arg_reg_off (memxor@gmail.com)
  + [2022-12-08] bpf: Rework process_dynptr_func (memxor@gmail.com)
  + [2022-12-08] bpf: Propagate errors from process_* checks in check_func_arg (memxor@gmail.com)
  + [2022-12-08] bpf: Refactor ARG_PTR_TO_DYNPTR checks into process_dynptr_func (memxor@gmail.com)
  + [2023-01-21] selftests/bpf: Add dynptr partial slot overwrite tests (memxor@gmail.com)
  + [2023-01-21] selftests/bpf: Add dynptr var_off tests (memxor@gmail.com)
  + [2023-01-21] selftests/bpf: Add dynptr pruning tests (memxor@gmail.com)
  + [2023-01-21] selftests/bpf: convenience macro for use with 'asm volatile' blocks (eddyz87@gmail.com)
  + [2022-12-07] selftests/bpf: convert dynptr_fail and map_kptr_fail subtests to generic tester (andrii@kernel.org)
  + [2022-12-07] selftests/bpf: add generic BPF program tester-loader (andrii@kernel.org)
  + [2023-09-27] cgroup: add cgroup_favordynmods= command-line option (luizcap@amazon.com)
  + [2023-05-18] KVM: arm64: Prevent unconditional donation of unmapped regions from the host (will@kernel.org)
  + [2022-11-10] KVM: arm64: Prevent the donation of no-map pages (qperret@google.com)
  + [2022-11-15] arm64/sve: Leave SVE enabled on syscall if we don't context switch (broonie@kernel.org)
  + [2022-11-15] arm64/fpsimd: SME no longer requires SVE register state (broonie@kernel.org)
  + [2022-11-15] arm64/fpsimd: Load FP state based on recorded data type (broonie@kernel.org)
  + [2022-11-15] arm64/fpsimd: Stop using TIF_SVE to manage register saving in KVM (broonie@kernel.org)
  + [2022-11-15] arm64/fpsimd: Have KVM explicitly say which FP registers to save (broonie@kernel.org)
  + [2022-11-15] arm64/fpsimd: Track the saved FPSIMD state type separately to TIF_SVE (broonie@kernel.org)
  + [2022-11-15] KVM: arm64: Discard any SVE state when entering KVM guests (broonie@kernel.org)
  + [2023-08-08] AL2023 6.1 Update ena driver to 2.8.9g (darinzon@amazon.com)
  + [2023-07-11] scripts/sign_file: Add option to keep signing certificate (samjonas@amazon.com)
  + [2019-04-23] KEYS: Make use of platform keyring for module signature verify (robeholmes@gmail.com)
  + [2023-02-09] Enable ptIOMMU for all supported platforms (daviddb@amazon.com)
  + [2023-07-27] ip: Bump default ttl to 127. (kuniyu@amazon.com)
  + [2022-11-18] mm: document /sys/class/bdi/<bdi>/strict_limit knob (shr@devkernel.io)
  + [2022-11-18] mm: add knob /sys/class/bdi/<bdi>/strict_limit (shr@devkernel.io)
  + [2022-11-18] mm: add bdi_set_strict_limit() function (shr@devkernel.io)
  + [2023-06-09] KEYS: use kfree_sensitive with key (mngyadam@amazon.com)
  + [2023-06-23] crypto: ecc - Add SP800-56A rev 3 Pair-wise Consistency check (mngyadam@amazon.com)
  + [2023-06-23] crypto: dh - Add SP800-56A rev 3 Pair-wise Consistency check (mngyadam@amazon.com)
  + [2023-03-03] crypto: rng - Use a different crypto_rng for reseeding (herbert.xu@redhat.com)
  + [2022-08-03] random: allow reseeding DRBG with getrandom (dueno@redhat.com)
  + [2023-02-14] net/ipv6: Improve performance of inet6_ehashfn() (trawets@amazon.com)
  + [2023-06-17] crypto: tcrypt.c - Add selftest for ffdhe algorithims (hailmo@amazon.com)
  + [2023-06-09] crypto: Only allow GCM in FIPS when instantiated via seqiv (samjonas@amazon.com)
  + [2023-06-06] crypto: rsa - allow only odd e and restrict value in FIPS mode (mngyadam@amazon.com)
  + [2021-08-10] crypto: rng - Override drivers/char/random in FIPS mode (herbert.xu@redhat.com)
  + [2021-08-10] random: Add hook to override device reads and getrandom(2) (herbert.xu@redhat.com)
  + [2023-04-13] Revert "drm: fb_helper: improve CONFIG_FB dependency" (samjonas@amazon.com)
  + [2023-06-06] crypto: ecdh - zeroize crpytographic keys after use (hailmo@amazon.com)
  + [2023-06-06] crypto: testmgr - Remove xts4096(paes) and xts512(paes) (hailmo@amazon.com)
  + [2023-04-21] crypto: jitter - replace LFSR with SHA3-256 (smueller@chronox.de)
  + [2022-12-29] crypto: testmgr - disallow plain ghash in FIPS mode (nstange@suse.de)
  + [2022-12-29] crypto: testmgr - disallow plain cbcmac(aes) in FIPS mode (nstange@suse.de)
  + [2023-01-17] crypto: testmgr - disallow certain DRBG hash functions in FIPS mode (vdronov@redhat.com)
  + [2021-11-02] arm64: module: Use aarch64_insn_write when updating relocations later on (surajjs@amazon.com)
  + [2021-05-03] arm64: implement live patching (surajjs@amazon.com)
  + [2023-02-02] arm64: Define HAVE_DYNAMIC_FTRACE_WITH_ARGS (madvenka@linux.microsoft.com)
  + [2021-03-15] arm64: Implement arch_stack_walk_reliable() (madvenka@linux.microsoft.com)
  + [2021-05-26] erm64: Create a list of SYM_CODE functions, check return PC against list (madvenka@linux.microsoft.com)
  + [2021-05-26] arm64: Introduce stack trace reliability checks in the unwinder (madvenka@linux.microsoft.com)
  + [2021-10-15] arm64: kvm: vgic-v3-sr: Bug when trying to read invalid APRs (surajjs@amazon.com)
  + [2022-06-23] arm64: kernel: Skip validation of proton-pack.c (chenzhongjin@huawei.com)
  + [2022-06-23] arm64: entry: Align stack size for alternative (chenzhongjin@huawei.com)
  + [2022-06-23] arm64: sleep: Properly set frame pointer before call (chenzhongjin@huawei.com)
  + [2022-06-23] arm64: Set intra-function call annotations (chenzhongjin@huawei.com)
  + [2022-06-23] arm64: crypto: Remove unnecessary stackframe (chenzhongjin@huawei.com)
  + [2022-06-23] arm64: crypto: Mark constant as data (chenzhongjin@huawei.com)
  + [2022-06-23] arm64: head: Mark constants as data (chenzhongjin@huawei.com)
  + [2022-06-23] arm64: efi-header: Mark efi header as data (chenzhongjin@huawei.com)
  + [2022-06-23] arm64: kvm: Annotate unwind_hint for hyp entry (chenzhongjin@huawei.com)
  + [2022-06-23] arm64: entry: Annotate unwind_hint for entry (chenzhongjin@huawei.com)
  + [2022-06-23] arm64: Annotate unwind_hint for symbols with empty stack (chenzhongjin@huawei.com)
  + [2022-06-23] arm64: Change symbol type annotations (chenzhongjin@huawei.com)
  + [2022-06-23] objtool: arm64: Add unwind_hint support (chenzhongjin@huawei.com)
  + [2022-06-23] arm64: kgdb: Add reachable annotation after kgdb brk (chenzhongjin@huawei.com)
  + [2022-06-23] arm64: bug: Add reachable annotation to warning macros (chenzhongjin@huawei.com)
  + [2022-06-23] objtool: arm64: Add annotate_reachable() for objtools (chenzhongjin@huawei.com)
  + [2023-03-28] Revert "arm64: alternatives: add shared NOP callback" (surajjs@amazon.com)
  + [2022-06-23] objtool: arm64: Enable stack validation for arm64 (chenzhongjin@huawei.com)
  + [2022-06-23] objtool: arm64: Ignore replacement section for alternative callback (chenzhongjin@huawei.com)
  + [2022-06-23] objtool: arm64: Handle supported relocations in alternatives (chenzhongjin@huawei.com)
  + [2022-06-23] objtool: check: Support data in text section (chenzhongjin@huawei.com)
  + [2022-06-23] objtool: arm64: Accept non-instruction data in code sections (chenzhongjin@huawei.com)
  + [2022-06-23] objtool: arm64: Decode LDR instructions (chenzhongjin@huawei.com)
  + [2022-06-23] objtool: arm64: Decode load/store instructions (chenzhongjin@huawei.com)
  + [2022-06-23] objtool: arm64: Decode other system instructions (chenzhongjin@huawei.com)
  + [2022-06-23] objtool: arm64: Decode jump and call related instructions (chenzhongjin@huawei.com)
  + [2022-06-23] objtool: arm64: Decode add/sub instructions (chenzhongjin@huawei.com)
  + [2022-06-23] objtool: arm64: Add base definition for arm64 backend (chenzhongjin@huawei.com)
  + [2022-06-23] tools: arm64: Make aarch64 instruction decoder available to tools (chenzhongjin@huawei.com)
  + [2023-03-14] objtool: Specify host-arch for making LIBSUBCMD (surajjs@amazon.com)
  + [2023-03-14] objtool: Add generic symbol for relocation type (surajjs@amazon.com)
  + [2023-05-17] AL2023 6.1 Update ena driver to 2.8.6g (akiyano@amazon.com)
  + [2023-04-14] Revert "selinux: runtime disable is deprecated, add some ssleep() discomfort" (luizcap@amazon.com)
  + [2023-03-30] ENA: Update to v2.8.3 (samjonas@amazon.com)
  + [2023-03-03] udp: Fix memleaks of sk and zerocopy skbs with TX timestamp. (kuniyu@amazon.com)
  + [2023-03-20] msr: disable MSR writes by default (luizcap@amazon.com)
  + [2023-01-24] Revert "xen/x2apic: enable x2apic mode when supported for HVM" (samjonas@amazon.com)
  + [2023-01-20] Revert "PCI/MSI: Let core code free MSI descriptors" (samjonas@amazon.com)
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
  + [2017-10-27] Enable Algorithims for Amazon Linux 6.1.y (alakeshh@amazon.com)
  + [2023-01-10] EFA: Update to v2.1.1 (shaoyi@amazon.com)
  + [2023-01-10] ENA: Update to v2.8.1 (shaoyi@amazon.com)
  + [2023-01-10] drivers/amazon: import 5.15 drivers (shaoyi@amazon.com)
  + [2018-02-12] drivers: introduce AMAZON_DRIVER_UPDATES (vallish@amazon.com)
  + [2021-02-22] hwrng: Add Gravition RNG driver (vaerov@amazon.com)
  + [2021-02-22] arm64: Export acpi_psci_use_hvc() symbol (vaerov@amazon.com)
  + [2021-05-12] x86: Disable KASLR when Xen is detected (benh@amazon.com)
  + [2022-05-25] Correct read overflow in page touching DMA ops binding (tbarri@amazon.com)
  + [2021-09-17] Introduce page touching DMA ops binding (jgowans@amazon.com)
  + [2021-12-10] virtio-balloon: optionally report offlined memory ranges (fllinden@amazon.com)
  + [2022-01-06] virtio: add hack to allow pre-mapped scatterlists (fllinden@amazon.com)
  + [2022-01-06] mm: add offline page reporting interface (fllinden@amazon.com)
  + [2021-12-09] drivers/base/memory: use MHP_MEMMAP_ON_MEMORY from the probe interface (fllinden@amazon.com)
  + [2021-12-31] memory: fix offline_and_remove_memory use (fllinden@amazon.com)
  + [2021-07-14] arm64/mm: Enable sysfs based memory hot remove probe (rohiwali@amazon.com)
  + [2019-04-03] Sysfs memory probe interface (anshuman.khandual@arm.com)
  + [2021-09-15] mm, memcg: throttle the memory reclaim given dirty/writeback pages to avoid early OOMs (shaoyi@amazon.com)
