%define LIBMAJ 0
%define libname %mklibname ipsec %LIBMAJ
%define libnamedev %mklibname -d ipsec

Name: ipsec-tools
Version: 0.7.3
Release: 8
Summary: Tools for configuring and using IPSEC
License: BSD
Group: Networking/Other
URL: http://ipsec-tools.sourceforge.net/
Source0: http://prdownloads.sourceforge.net/ipsec-tools/ipsec-tools-%{version}.tar.bz2
Source3: racoon.conf
Source4: psk.txt
Source6: ipsec-setkey-initscript
Source7: racoon-initscript
Source8: racoon.sysconfig
Patch0: ipsec-tools-0.6.2b3-manfix.patch
Patch1: ipsec-tools-0.5.2-includes.patch
Patch2: ipsec-tools-0.7.3-install.patch
Patch3: ipsec-tools-0.7.3-link.patch
# Fedora patches
Patch102: ipsec-tools-0.7.3-build.patch
Patch103: ipsec-tools-0.7-acquires.patch
Patch104: ipsec-tools-0.7.1-loopback.patch
# the following patches were also submitted upstream:
Patch105: ipsec-tools-0.7-iface.patch
Patch106: ipsec-tools-0.7-dupsplit.patch
Patch109: ipsec-tools-0.7-splitcidr.patch
Patch110: ipsec-tools-0.7.2-natt-linux.patch
Patch111: ipsec-tools-0.7.1-pie.patch
Patch113: ipsec-tools-0.7.1-dpd-fixes.patch
BuildRequires: openssl-devel krb5-devel flex bison
BuildRequires: pam-devel
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
%patch2 -p1 -b .install
%patch3 -p0 -b .link
%patch102 -p1 -b .build
%patch103 -p1 -b .acquires
%patch104 -p1 -b .loopback
%patch105 -p1 -b .iface
%patch106 -p1 -b .dupsplit
%patch109 -p1 -b .splitcidr
%patch110 -p1 -b .natt-linux
%patch111 -p1 -b .pie
%patch113 -p1 -b .dpd-fixes

sed -i 's|-Werror||g' configure*


%build
./bootstrap
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
%doc ChangeLog NEWS README
/%{_lib}/*.so.*

%files -n %{libnamedev}
/%{_lib}/libipsec.so
/%{_lib}/libracoon.so
%{_includedir}/*





%changelog
* Mon May 09 2011 Funda Wang <fwang@mandriva.org> 0.7.3-5mdv2011.0
+ Revision: 672779
- add fedora  patches to fix build

  + Oden Eriksson <oeriksson@mandriva.com>
    - mass rebuild

* Fri Dec 03 2010 Oden Eriksson <oeriksson@mandriva.com> 0.7.3-4mdv2011.0
+ Revision: 605980
- rebuild

* Wed Apr 28 2010 Funda Wang <fwang@mandriva.org> 0.7.3-3mdv2010.1
+ Revision: 539967
- fix linkage problem

* Fri Feb 26 2010 Oden Eriksson <oeriksson@mandriva.com> 0.7.3-2mdv2010.1
+ Revision: 511579
- rebuilt against openssl-0.9.8m

* Sat Sep 26 2009 Frederik Himpe <fhimpe@mandriva.org> 0.7.3-1mdv2010.0
+ Revision: 449597
- Update to new version 0.7.3
- Add patch from PLD fixing double installation of header file

* Sun May 03 2009 Frederik Himpe <fhimpe@mandriva.org> 0.7.2-1mdv2010.0
+ Revision: 371015
- Update to new version 0.7.2
- Remove security patch integrated upstream
- Add Fedora patches
- Set %%define _disable_ld_no_undefined 1 to fix undefined references
- Explicitly disable audit support to make it build even if
  libaudit-devel is installed

* Sat Aug 23 2008 Frederik Himpe <fhimpe@mandriva.org> 0.7.1-1mdv2009.0
+ Revision: 275249
- Add patch fixing security problem CVE-2008-3652
- Update to version 0.7.1 (fixes CVE-2008-3651)

* Tue Jun 17 2008 Thierry Vignaud <tv@mandriva.org> 0.7-2mdv2009.0
+ Revision: 221638
- rebuild
- kill re-definition of %%buildroot on Pixel's request

  + Pixel <pixel@mandriva.com>
    - do not call ldconfig in %%post/%%postun, it is now handled by filetriggers
    - adapt to %%_localstatedir now being /var instead of /var/lib (#22312)

  + Olivier Blin <oblin@mandriva.com>
    - restore BuildRoot

* Wed Oct 17 2007 Andreas Hasenack <andreas@mandriva.com> 0.7-1mdv2008.1
+ Revision: 99702
- updated to version 0.7
- comply with new devel package policy (drop soname from it)
- drop patches which are no longer needed (gcc-misc, werror)
- disable security context or else we need selinux

* Thu Aug 23 2007 Thierry Vignaud <tv@mandriva.org> 0.6.7-1mdv2008.0
+ Revision: 69963
- patch 4: fix build by disabling -Werror which make build randomly fails for no good reason when newer gcc spit out more warnings
- fileutils, sh-utils & textutils have been obsoleted by coreutils a long time ago


* Sat Apr 07 2007 Andreas Hasenack <andreas@mandriva.com> 0.6.7-1mdv2007.1
+ Revision: 151144
- updated to version 0.6.7, fixing a DoS (CVE-2007-1841)

* Thu Sep 14 2006 Andreas Hasenack <andreas@mandriva.com> 0.6.6-2mdv2007.0
+ Revision: 61328
- added PAM configuration file (PAM auth tested)

* Thu Sep 14 2006 Andreas Hasenack <andreas@mandriva.com> 0.6.6-1mdv2007.0
+ Revision: 61275
- added buildrequires for libpam-devel due to new pam support
- using mkrel
- enabled pam support
- added support for parallel initscripts
- bunzipped patches and some source files
- updated to version 0.6.6
- added gcc patch
- don't run auto-tools, it's introducing a build error
- Import ipsec-tools

* Sun Feb 05 2006 Andreas Hasenack <andreas@mandriva.com> 0.6.5-1mdk
- updated to version 0.6.5

* Wed Jan 25 2006 Andreas Hasenack <andreas@mandriva.com> 0.6.4-1mdk
- updated to version 0.6.4
- removed openssl0.9.8 patch, not needed anymore

* Sun Nov 13 2005 Oden Eriksson <oeriksson@mandriva.com> 0.6.2b3-2mdk
- added P3 from fedora to make it build against openssl-0.9.8a

* Wed Oct 05 2005 Andreas Hasenack <andreas@mandriva.com> 0.6.2b3-1mdk
- updated to version 0.6.2b3
- removed signwarn patch, already applied
- removed warning patch, no longer needed
- redid x86_64 patch
- redid manfix patch
- removed --enable-samode-unspec ./configure option, it's said to not work
  with linux
- added "remote anonymous" section to default racoon.conf, taken from sample file
  in the documentation directory
- added libracoon to file list in devel package

* Thu Sep 08 2005 Gwenole Beauchesne <gbeauchesne@mandriva.com> 0.5.2-5mdk
- don't forcibly redefine bcopy() & bzero()

* Wed Jun 29 2005 Andreas Hasenack <andreas@mandriva.com> 0.5.2-4mdk
- added a sample ipsec.conf file
- use proper exit codes in the ipsec-setkey and racoon initscripts
- only load ipv6 ipsec related modules if NETWORKING_IPV6=yes
  (ipsec-setkey init script)
- added more documentation to %%doc
- removed reload option from the racoon initscript since it's not
  supported anyway (was equal to restart)

* Thu Jun 23 2005 Andreas Hasenack <andreas@mandriva.com> 0.5.2-3mdk
- more fixes for paths in the manpage

* Tue Jun 14 2005 Andreas Hasenack <andreas@mandriva.com> 0.5.2-2mdk
- fix patch referenced in manpage

* Tue Jun 14 2005 Andreas Hasenack <andreas@mandriva.com> 0.5.2-1mdk
- updated to version 0.5.2
- using /etc/racoon for sysconfdir directory (fixes #16234)
- added patch to fix a signedess warning with gcc4
- included missing /var/lib/racoon directory, fixing #16409 (why isn't
  rpm warning about this directory which wasn't being packaged?)
- added a sysconfig file so that the admin can give racoon some command
  line arguments if needed

* Wed May 04 2005 Couriousous <couriousous@mandriva.org> 0.5.1-2mdk
- Fix x86_64 build

* Sun May 01 2005 Couriousous <couriousous@mandriva.org> 0.5.1-1mdk
- 0.5.1
- Enable more features
- Patch to fix gssapi warning

* Fri Mar 25 2005 Couriousous <couriousous@mandrake.org> 0.5-4mdk
- Security fix (CAN-2005-0398)

* Thu Mar 03 2005 Couriousous <couriousous@mandrake.org> 0.5-3mdk
- Fix conflict with openswan ( #14133 )

* Wed Feb 23 2005 Christiaan Welvaart <cjw@daneel.dyndns.org> 0.5-2mdk
- add BuildRequires: bison

* Sat Feb 19 2005 Couriousous <couriousous@mandrake.org> 0.5-1mdk
- 0.5
- Change library name libipsec-tools to libipsec

* Sun Dec 26 2004 Couriousous <couriousous@mandrake.org> 0.4-2mdk
- Add Provide kvpnc-backend

* Thu Sep 23 2004 Couriousous <couriousous@sceen.net> 0.4-1mdk
- 0.4
- Add startup scripts
- Enable -devel package

* Fri Jul 16 2004 Christiaan Welvaart <cjw@daneel.dyndns.org> 0.2.5-2mdk
- add BuildRequires: flex

* Fri Apr 09 2004 Florin <florin@mandrakesoft.com> 0.2.5-1mdk
- 0.2.5 (security update)
- /sbin now contains the binaries and not /usr/sbin anymore

