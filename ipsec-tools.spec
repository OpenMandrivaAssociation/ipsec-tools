%define LIBMAJ 0
%define libname %mklibname ipsec %LIBMAJ
%define libnamedev %mklibname -d ipsec

Name: ipsec-tools
Version: 0.7
Release: %mkrel 1
Summary: Tools for configuring and using IPSEC
License: BSD
Group: Networking/Other
URL: http://ipsec-tools.sourceforge.net/
Source: http://prdownloads.sourceforge.net/ipsec-tools/ipsec-tools-%{version}.tar.bz2
Source3: racoon.conf
Source4: psk.txt
Source6: ipsec-setkey-initscript
Source7: racoon-initscript
Source8: racoon.sysconfig
Patch: ipsec-tools-0.6.2b3-manfix.patch
Patch1: ipsec-tools-0.5.2-includes.patch
BuildRequires: openssl-devel krb5-devel flex bison
BuildRequires: libpam-devel
Requires: %{libname} = %{version}
Requires(pre): rpm-helper
Requires: rpm-helper
Provides: kvpnc-backend

%description
This is the IPsec-Tools package.  You need this package in order to
really use the IPsec functionality in the linux-2.6 and above kernels.  
This package builds:
 
	- libipsec, a PFKeyV2 library
	- setkey, a program to directly manipulate policies and SAs
	- racoon, an IKEv1 keying daemon

%define old_libname %mklibname ipsec-tools 0
%define old_libname_devel %mklibname -d ipsec 0

%package -n %{libname}
Summary: The shared libraries used by ipsec-tools
Group: System/Libraries
Requires(post): grep, coreutils
Requires(preun): grep, coreutils
Requires: grep, coreutils
Provides: libipsec = %{version}-%{release}
Provides: libipsec-tools = %{version}-%{release}
Obsoletes: libipsec-tools
Provides: %old_libname = %{version}-%{release}
Obsoletes: %old_libname

%description -n %{libname}
These are the shared libraries for the IPsec-Tools package.

%package -n %{libnamedev}
Summary: Headers for programs for %libname
Group: Development/C
Requires: %{libname} = %{version}
Provides: libipsec-tools-devel = %{version}-%{release}
Provides: libipsec-devel = %{version}-%{release}
Obsoletes: libipsec-tools-devel 
Provides: %{old_libname}-devel = %{version}-%{release}
Obsoletes: %{old_libname}-devel
Obsoletes: %{old_libname_devel} < 0.7


%description -n %{libnamedev}
These are development headers for libipsec

%prep
%setup -q
%patch0 -p1 -b .manfix
%patch1 -p1 -b .includes

%build
./configure  \
	--prefix=%{_prefix} \
	--mandir=%{_mandir} \
	--libdir=/%{_lib} \
	--sbindir=/sbin \
	--localstatedir=%{_localstatedir} \
	--sysconfdir=%{_sysconfdir}/racoon \
	--with-kernel-headers=%{_includedir} \
	--enable-shared \
	--disable-rpath \
	--enable-hybrid \
	--enable-frag \
	--enable-dpd \
	--enable-adminport \
	--enable-gssapi \
	--enable-natt \
	--with-libpam \
        --enable-security-context=no

# removed: 0.6.1 says it's not supported in linux
# --enable-samode-unspec

make

%install
rm -rf $RPM_BUILD_ROOT
%makeinstall_std

mkdir -p $RPM_BUILD_ROOT/etc/racoon/

install -m 0600 %{SOURCE3} $RPM_BUILD_ROOT/etc/racoon/racoon.conf
install -m 0600 %{SOURCE4} $RPM_BUILD_ROOT/etc/racoon/psk.txt
mkdir -m 0700 -p $RPM_BUILD_ROOT/etc/racoon/certs

mkdir -p $RPM_BUILD_ROOT/%{_initrddir}
install -m 0755 %{SOURCE6} $RPM_BUILD_ROOT/%{_initrddir}/ipsec-setkey
install -m 0755 %{SOURCE7} $RPM_BUILD_ROOT/%{_initrddir}/racoon

mkdir -p %{buildroot}%{_sysconfdir}/sysconfig
# racoon.sysconfig
install -m 0644 %{SOURCE8} %{buildroot}%{_sysconfdir}/sysconfig/racoon

# pam file
mkdir -p %{buildroot}%{_sysconfdir}/pam.d
cat > %{buildroot}%{_sysconfdir}/pam.d/racoon <<EOF
#%PAM-1.0
auth       required     pam_nologin.so
%if %mdkversion < 200700
auth       required     pam_stack.so service=system-auth
account    required     pam_stack.so service=system-auth
%else
auth       include      system-auth
account    include      system-auth
%endif
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
# ipsec between two machines: 192.168.1.10 and 192.168.1.20
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

%clean
rm -rf $RPM_BUILD_ROOT

%post
%_post_service ipsec-setkey
%_post_service racoon

%preun
%_preun_service ipsec-setkey
%_preun_service racoon

%post -n %{libname} -p /sbin/ldconfig

%postun -n %{libname} -p /sbin/ldconfig

%files
%defattr(-,root,root)
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
%defattr(-,root,root)
%doc ChangeLog NEWS README
/%{_lib}/*.so.*

%files -n %{libnamedev}
%defattr(-,root,root)
/%{_lib}/libipsec.la
/%{_lib}/libipsec.a
/%{_lib}/libipsec.so
/%{_lib}/libracoon.la
/%{_lib}/libracoon.a
/%{_lib}/libracoon.so
%{_includedir}/*



