# Binary package of the upstream Linux release tarball. COPR has network
# access, so Source URLs are fetched at build time. Prebuilt binary - do
# not strip or generate debuginfo.
%global debug_package %{nil}
%global __strip /bin/true

Name:           rtk-oss
Version:        1.1.0
Release:        1%{?dist}
Summary:        Apache-2.0-only edition of rtk, a CLI proxy that reduces LLM token consumption

License:        Apache-2.0
URL:            https://github.com/rtk-ai/rtk

# Both arch tarballs are listed so the SRPM works for multi-arch COPR builds.
# x86_64 is a static musl build; aarch64 is glibc-linked. Each tarball
# contains the "rtk" binary and the license file at the top level.
Source0:        %{url}/releases/download/v%{version}/rtk-oss-x86_64-unknown-linux-musl.tar.gz#/%{name}-%{version}-x86_64-unknown-linux-musl.tar.gz
Source1:        %{url}/releases/download/v%{version}/rtk-oss-aarch64-unknown-linux-gnu.tar.gz#/%{name}-%{version}-aarch64-unknown-linux-gnu.tar.gz

# Both rtk and rtk-oss install a binary named "rtk"; they cannot coexist.
Conflicts:      rtk

ExclusiveArch:  x86_64 aarch64

BuildRequires:  bash

%description
RTK filters and compresses command outputs before they reach your LLM
context. Single Rust binary, 100+ supported commands, <10ms overhead.

This is the Apache-2.0-only edition: hook core and command filters, no
compression engine. It installs the official prebuilt Linux binary from
upstream GitHub releases. The binary is named "rtk"; it cannot be installed
alongside rtk.

%prep
# Tarball has no enclosing directory; -c creates %%{name}-%%{version}/ for us.
# -T skips the default Source0 unpack; -a N unpacks SourceN after chdir.
%ifarch x86_64
%setup -q -c -n %{name}-%{version} -T -a 0
%endif
%ifarch aarch64
%setup -q -c -n %{name}-%{version} -T -a 1
%endif

%build
# Prebuilt binary - nothing to compile.

%install
install -Dpm0755 rtk %{buildroot}%{_bindir}/rtk

%check
%{buildroot}%{_bindir}/rtk --version | grep -Fqe "%{version}"

%files
%license LICENSE
%{_bindir}/rtk

%changelog
* Wed Oct 28 2026 vitrasti <vitrasti@protonmail.com> - 1.1.0-1
- Initial package for personal COPR
- Install official prebuilt Linux release binary (Apache-2.0-only edition, no engine)
