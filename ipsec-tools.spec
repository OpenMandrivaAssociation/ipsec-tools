%define major	0
%define libname %mklibname ipsec %{major}
%define libracoon %mklibname racoon %{major}
%define devname %mklibname -d ipsec

Name:		ipsec-tools
Version:	0.7.3
Release:	16
Summary:	Tools for configuring and using IPSEC
License:	BSD
Group:		Networking/Other
Url:		http://ipsec-tools.sourceforge.net/
Source0:	http://prdownloads.sourceforge.net/ipsec-tools/%{name}-%{version}.tar.bz2
Source3:	racoon.conf
Source4:	psk.txt
Source6:	ipsec-setkey-initscript
Source7:	racoon-initscript
Source8:	racoon.sysconfig
Patch0:		ipsec-tools-0.6.2b3-manfix.patch
Patch1:		ipsec-tools-0.5.2-includes.patch
Patch2:		ipsec-tools-0.7.3-install.patch
Patch3:		ipsec-tools-0.7.3-link.patch
Patch4:		ipsec-tools-automake-1.13.patch
# Fedora patches
Patch102:	ipsec-tools-0.7.3-build.patch
Patch103:	ipsec-tools-0.7-acquires.patch
Patch104:	ipsec-tools-0.7.1-loopback.patch
# the following patches were also submitted upstream:
Patch105:	ipsec-tools-0.7-iface.patch
Patch106:	ipsec-tools-0.7-dupsplit.patch
Patch109:	ipsec-tools-0.7-splitcidr.patch
Patch110:	ipsec-tools-0.7.2-natt-linux.patch
Patch111:	ipsec-tools-0.7.1-pie.patch
Patch113:	ipsec-tools-0.7.1-dpd-fixes.patch

BuildRequires:	bison
BuildRequires:	flex-devel
BuildRequires:	krb5-devel
BuildRequires:	pam-devel
BuildRequires:	pkgconfig(openssl)
Requires(pre):	rpm-helper
Requires:	rpm-helper
Provides:	kvpnc-backend

%description
This is the IPsec-Tools package.  You need this package in order to
really use the IPsec functionality in the linux-2.6 and above kernels.  
This package builds:
 
	- libipsec, a PFKeyV2 library
	- setkey, a program to directly manipulate policies and SAs
	- racoon, an IKEv1 keying daemon

%package -n %{libname}
Summary:	The shared libraries used by ipsec-tools
Group:		System/Libraries
Requires(post,preun):	grep
Requires(post,preun):	coreutils
Requires:	grep
Requires:	coreutils
Provides:	libipsec = %{version}-%{release}

%description -n %{libname}
This package contains a shared libraries for the IPsec-Tools package.

%package -n %{libracoon}
Summary:	The shared libraries used by ipsec-tools
Group:		System/Libraries
Conflicts:	%{_lib}ipsec0 < 0.7.3-9

%description -n %{libracoon}
This package contains a shared libraries for the IPsec-Tools package.

%package -n %{devname}
Summary:	Headers for programs for %libname
Group:		Development/C
Requires:	%{libname} = %{version}-%{release}
Requires:	%{libracoon} = %{version}-%{release}
Provides:	%{name}-devel = %{version}-%{release}

%description -n %{devname}
These are development headers for libipsec

%prep
%setup -q
%apply_patches
sed -i 's|-Werror||g' configure*
./bootstrap

%build
%configure2_5x  \
	--prefix=%{_prefix} \
	--mandir=%{_mandir} \
	--libdir=/%{_lib} \
	--sbindir=/sbin \
	--localstatedir=%{_localstatedir}/lib \
	--sysconfdir=%{_sysconfdir}/racoon \
	--with-kernel-headers=%{_includedir} \
	--enable-shared \
	--disable-static \
	--disable-rpath \
	--enable-hybrid \
	--enable-frag \
	--enable-dpd \
	--enable-adminport \
	--enable-gssapi \
	--enable-natt \
	--with-libpam \
	--enable-security-context=no \
	--disable-audit

make

%install
%makeinstall_std

mkdir -p %{buildroot}/etc/racoon/

install -m 0600 %{SOURCE3} %{buildroot}/etc/racoon/racoon.conf
install -m 0600 %{SOURCE4} %{buildroot}/etc/racoon/psk.txt
mkdir -m 0700 -p %{buildroot}/etc/racoon/certs

mkdir -p %{buildroot}/%{_initrddir}
install -m 0755 %{SOURCE6} %{buildroot}/%{_initrddir}/ipsec-setkey
install -m 0755 %{SOURCE7} %{buildroot}/%{_initrddir}/racoon

mkdir -p %{buildroot}%{_sysconfdir}/sysconfig
# racoon.sysconfig
install -m 0644 %{SOURCE8} %{buildroot}%{_sysconfdir}/sysconfig/racoon

# pam file
mkdir -p %{buildroot}%{_sysconfdir}/pam.d
cat > %{buildroot}%{_sysconfdir}/pam.d/racoon <<EOF
#%PAM-1.0
auth       required     pam_nologin.so
auth       include      system-auth
account    include      system-auth
EOF

# default ipsec.conf file
cat > %{buildroot}%{_sysconfdir}/ipsec.conf <<EOF
#!/usr/sbin/setkey -f
#
# File /etc/ipsec.conf

# delete the SAD and SPD
flush;
spdflush;

# Define here your security policies

# Example
# ipsec between two machines:	192.168.1.10 and 192.168.1.20
#
# spdadd 192.168.1.10 192.168.1.20 any -P in ipsec
#       esp/transport//require
#       ah/transport//require;
#
# spdadd 192.168.1.20 192.168.1.10 any -P out ipsec
#       esp/transport//require
#       ah/transport//require;

EOF

# remove some files from the sample dir so we can include it
# in %%doc. Also fix their permissions
rm -f src/racoon/samples/*.in
find src/racoon/samples -type f -exec chmod 0644 {} \;

%post
%_post_service ipsec-setkey
%_post_service racoon

%preun
%_preun_service ipsec-setkey
%_preun_service racoon

%files
%doc ChangeLog NEWS README
%doc src/racoon/samples
%doc src/racoon/doc/*
/sbin/*
%{_mandir}/man*/*
%dir %{_sysconfdir}/racoon
%dir %{_sysconfdir}/racoon/certs
%config(noreplace) %{_sysconfdir}/sysconfig/racoon
%config(noreplace) %{_sysconfdir}/racoon/psk.txt
%config(noreplace) %{_sysconfdir}/racoon/racoon.conf
%config(noreplace) %attr(0600,root,root) %{_sysconfdir}/ipsec.conf
%config(noreplace) %{_sysconfdir}/pam.d/racoon
%attr (0755,root,root) %{_initrddir}/ipsec-setkey
%attr (0755,root,root) %{_initrddir}/racoon
%dir /var/lib/racoon

%files -n %{libname}
/%{_lib}/libipsec.so.%{major}*

%files -n %{libracoon}
/%{_lib}/libracoon.so.%{major}*

%files -n %{devname}
%doc ChangeLog NEWS README
/%{_lib}/libipsec.so
/%{_lib}/libracoon.so
%{_includedir}/*

