# Binary package of the upstream Linux release tarball (same approach as
# AUR pi-coding-agent-bin). COPR has network access, so Source URLs are
# fetched at build time. Prebuilt Bun binary - do not strip or generate
# debuginfo.
%global debug_package %{nil}
%global __strip /bin/true

Name:           pi
Version:        1.1.0
Release:        1%{?dist}
Summary:        AI coding agent CLI with read, bash, edit, write tools and session management

License:        MIT
URL:            https://github.com/earendil-works/pi

# Always list both arch tarballs so the SRPM works for multi-arch COPR builds.
# Each tarball contains a top-level "pi/" bundle: prebuilt binary plus assets
# (theme, export-html, wasm, native prebuilds, docs, examples) that the binary
# resolves relative to its own path, so the bundle must stay intact.
Source0:        %{url}/releases/download/v%{version}/pi-linux-x64.tar.gz#/%{name}-%{version}-linux-x64.tar.gz
Source1:        %{url}/releases/download/v%{version}/pi-linux-arm64.tar.gz#/%{name}-%{version}-linux-arm64.tar.gz
# Local file in this package directory (must be committed next to the spec).
Source2:        LICENSE

ExclusiveArch:  x86_64 aarch64

# The binary auto-downloads rg/fd to ~/.pi/bin when missing, but prefers
# system binaries on PATH.
Suggests:       ripgrep
Suggests:       fd
Suggests:       git

BuildRequires:  bash

%description
Pi is an AI coding agent for the terminal with read, bash, edit, write tools,
session management, a TUI, and extension support.

This package installs the official prebuilt Linux standalone binary from
upstream GitHub releases (same approach as AUR pi-coding-agent-bin). The
bundle lives under %{_libdir}/pi and is exposed via a %{_bindir}/pi symlink,
so it layers cleanly on rpm-ostree/immutable Fedora including Fedora CoreOS
(no /opt). All state is kept in ~/.pi.

On rpm-ostree systems `pi update self` cannot replace the binary in read-only
/usr; update via your package manager (COPR) instead.

%prep
# Tarball contains a top-level "pi/" bundle directory.
%ifarch x86_64
%setup -q -c -n %{name}-%{version} -T -a 0
%endif
%ifarch aarch64
%setup -q -c -n %{name}-%{version} -T -a 1
%endif
cp -a %{SOURCE2} .

%build
# Prebuilt binary - nothing to compile.

%install
install -d %{buildroot}%{_libdir}
cp -a --no-preserve=ownership pi %{buildroot}%{_libdir}/pi
install -d %{buildroot}%{_bindir}
ln -s ../%{_lib}/pi/pi %{buildroot}%{_bindir}/pi

%check
%{buildroot}%{_libdir}/pi/pi --version | grep -Fqe "%{version}"

%files
%license LICENSE
%{_libdir}/pi
%exclude %{_libdir}/pi/examples/extensions/*/.gitignore
%{_bindir}/pi

%changelog
* Fri Oct 09 2026 vitrasti <vitrasti@protonmail.com> - 1.1.0-1
- Update to 1.1.0

* Tue Oct 06 2026 vitrasti <vitrasti@protonmail.com> - 1.0.4-1
- Update to 1.0.4

* Sun Oct 04 2026 vitrasti <vitrasti@protonmail.com> - 1.0.2-1
- Initial package for personal COPR
- Based on AUR pi-coding-agent-bin packaging
- Install official prebuilt Linux release bundle under /usr/lib{,64}/pi
- Expose via /usr/bin/pi symlink (rpm-ostree/Fedora CoreOS friendly)
