%define _binaries_in_noarch_packages_terminate_build 0

%global hulkrelease 4.9

%global debug_package %{nil}

%global cross_compile gcc-linaro-5.5.0-2017.10-x86_64_aarch64-linux-gnu

Name:	 tegra210-kernel
Version: 4.9
Release: %{hulkrelease}.1.tegra
Summary: Linux Kernel
License: GPLv2 and Apache-2.0 and MIT
URL:	 http://www.kernel.org/
Source0: https://github.com/chainsx/t210-kernel/archive/refs/tags/32.6.1.tar.gz
Source1: http://releases.linaro.org/components/toolchain/binaries/latest-5/aarch64-linux-gnu/%{cross_compile}.tar.xz

BuildRequires: module-init-tools, patch >= 2.5.4, bash >= 2.03, tar
BuildRequires: bzip2, xz, findutils, gzip, m4, make >= 3.78, diffutils, gawk
BuildRequires: gcc >= 3.4.2, binutils >= 2.12
BuildRequires: hostname, bc
BuildRequires: openssl-devel
BuildRequires: ncurses-devel
BuildRequires: elfutils-libelf-devel
BuildRequires: bison
BuildRequires: elfutils

AutoReq: no
AutoProv: yes

Provides: tegra210-kernel-aarch64 = %{version}-%{release}
BuildArch: noarch
ExclusiveArch: noarch, aarch64, x86_64
ExclusiveOS: Linux

%description
The Linux Kernel image for Jetson Nano/Nano 2GB/TX1.

%package image
Summary: image files of the Linux kernel
Provides: tegra210-kernel-aarch64-image = %{version}-%{release}

%description image
image files of the Linux kernel.

%package dtbs
Summary: device-tree files of the Linux kernel
AutoReqProv: no
Provides: tegra210-kernel-aarch64-dtbs = %{version}-%{release}

%description dtbs
device-tree files of the Linux kernel.

%package modules
Summary: kernel modules files of the Linux kernel
AutoReqProv: no
Provides: tegra210-kernel-aarch64-modules = %{version}-%{release}

%description modules
kernel modules files of the Linux kernel.

%prep
%setup -q -n kernel-%{version} -c

%build
tar -xf %{_sourcedir}/%{cross_compile}.tar.xz -C .
export PATH=$PATH:%{_builddir}/kernel-%{version}/%{cross_compile}/bin
cd %{_builddir}/kernel-%{version}/t210-kernel-32.6.1/kernel/kernel-%{version}

make ARCH=arm64 tegra_defconfig CROSS_COMPILE=aarch64-linux-gnu-

make ARCH=arm64 KERNELRELEASE=%{version} CROSS_COMPILE=aarch64-linux-gnu-

%install
cd %{_builddir}/kernel-%{version}/t210-kernel-32.6.1/kernel/kernel-%{version}
export PATH=$PATH:%{_builddir}/kernel-%{version}/%{cross_compile}/bin
make ARCH=arm64 INSTALL_MOD_PATH=$RPM_BUILD_ROOT modules_install KERNELRELEASE=%{version} CROSS_COMPILE=aarch64-linux-gnu-
rm -rf $RPM_BUILD_ROOT/lib/modules/%{version}/source $RPM_BUILD_ROOT/lib/modules/%{version}/build

mkdir -p $RPM_BUILD_ROOT/boot
mkdir kernel-bin
make ARCH=arm64 KERNELRELEASE=%{version} CROSS_COMPILE=aarch64-linux-gnu- install INSTALL_PATH=kernel-bin

install -m 755 kernel-bin/vmlinuz-%{version} $RPM_BUILD_ROOT/boot/vmlinuz-%{version}
install -m 644 kernel-bin/System.map-%{version} $RPM_BUILD_ROOT/boot/System.map-%{version}

mkdir -p $RPM_BUILD_ROOT/boot/dtb-%{version}/overlays
rm -rf arch/arm64/boot/dts/_ddot_
install -m 644 $(find arch/arm64/boot/dts/ -name "*.dtb") $RPM_BUILD_ROOT/boot/dtb-%{version}/
install -m 644 $(find arch/arm64/boot/dts/ -name "*.dtbo") $RPM_BUILD_ROOT/boot/dtb-%{version}/overlays/


%postun
version_old=0
if [ "$1" == "0" ]; then
    version_old=old
else
    version_tmp=0
    name_len=`echo -n %{name}-|wc -c`
    for item in `rpm -qa %{name} 2>/dev/null`
    do
        cur_version=${item:name_len}
        cpu_version=${cur_version##*.}
        if [ "$cpu_version" == "%{_target_cpu}" ]; then
            cur_version=${cur_version%.*}
            cur_version=$cur_version.tegra.$cpu_version
            if [[ "$cur_version" != "%{version}" && "$cur_version" > "$version_tmp" ]]; then
                version_tmp=$cur_version
            fi
        fi
    done
    if [[ "$version_tmp" < "%{version}" ]]; then
        version_old=$version_tmp
    fi
fi
if [ "$version_old" != "0" ]; then
    if [ -f /boot/vmlinuz-$version_old ] && [ -d /boot/dtb-$version_old ] && ( [ "$version_old" == "old" ] || [ -d /lib/modules/$version_old ] ); then
        ls /boot/dtb-$version_old/overlays/*.dtbo > /dev/null 2>&1
        if [ "$?" == "0" ]; then
            ls /boot/dtb-$version_old/*.dtb > /dev/null 2>&1
            if [ "$?" == "0" ]; then
                rm -rf /boot/*.dtb /boot/overlays
                mkdir /boot/overlays
                install -m 755 /boot/vmlinuz-$version_old /boot/vmlinuz-$version_old
                for file in `ls /boot/dtb-$version_old/*.dtb 2>/dev/null`
                do
                    if [ -f $file ]; then
                        install -m 644 $file /boot/`basename $file`
                    fi
                done
                install -m 644 $(find /boot/dtb-$version_old/overlays/ -name "*.dtbo") /boot/overlays/
                if ls /boot/dtb-$version_old/overlays/*.dtb > /dev/null 2>&1; then
                    install -m 644 $(find /boot/dtb-$version_old/overlays/ -name "*.dtb") /boot/overlays/
                fi
            else
                echo "warning: files in /boot/dtb-$version_old/*.dtb missing when resetting kernel as $version_old, something may go wrong when starting this device next time."
            fi
        else
            echo "warning: files in /boot/dtb-$version_old/overlays missing when resetting kernel as $version_old, something may go wrong when starting this device next time."
        fi
    else
        echo "warning: files missing when resetting kernel as $version_old, something may go wrong when starting this device next time."
    fi
fi

%posttrans

mkdir -p /boot/overlays
install -m 755 /boot/vmlinuz-%{version} /boot/vmlinuz-%{version}
for file in `ls /boot/dtb-%{version}/*.dtb 2>/dev/null`
do
    if [ -f $file ]; then
        install -m 644 $file /boot/`basename $file`
    fi
done
install -m 644 $(find /boot/dtb-%{version}/overlays/ -name "*.dtbo") /boot/overlays/
if ls /boot/dtb-%{version}/overlays/*.dtb > /dev/null 2>&1; then
    install -m 644 $(find /boot/dtb-%{version}/overlays/ -name "*.dtb") /boot/overlays/
fi

%files image
%defattr (-, root, root)
%doc
/boot/System.map-*
/boot/vmlinuz-*

%files dtbs
%defattr (-, root, root)
%doc
/boot/dtb-*

%files modules
%defattr (-, root, root)
%doc
/lib/modules/%{version}
/lib/firmware

%changelog
* Mon Feb 22 2021 chainsx<chainsx@outlook.com> - 4.9-tegra-4.9.1
- initial project
