# Binary package of the upstream Linux release tarball (same approach as
# AUR qbittorrent-tui-bin). COPR has network access, so Source URLs are
# fetched at build time. Prebuilt Go binary — do not strip or generate
# debuginfo.
%global debug_package %{nil}
%global __strip /bin/true

Name:           qbt-tui
Version:        0.1.5
Release:        1%{?dist}
Summary:        Terminal user interface for qBittorrent

License:        MIT
URL:            https://github.com/nickvanw/qbittorrent-tui

# Always list both arch tarballs so the SRPM works for multi-arch COPR builds.
# Each tarball contains the "qbt-tui" binary and README.md at the top level.
# goreleaser name: qbt-tui_<version>_linux_<amd64|arm64>.tar.gz
Source0:        %{url}/releases/download/v%{version}/qbt-tui_%{version}_linux_amd64.tar.gz#/%{name}-%{version}-linux-x64.tar.gz
Source1:        %{url}/releases/download/v%{version}/qbt-tui_%{version}_linux_arm64.tar.gz#/%{name}-%{version}-linux-arm64.tar.gz

# Local file in this package directory (must be committed next to the spec).
# Upstream tags do not ship a LICENSE file in the release tarball.
Source2:        LICENSE

ExclusiveArch:  x86_64 aarch64

BuildRequires:  bash

%description
qbt-tui is a terminal-based user interface for monitoring and managing
qBittorrent via its Web UI API. It provides live torrent status, filtering,
and basic torrent actions (add, pause, resume, delete) from a remote server
or container.

This package installs the official prebuilt Linux binary from upstream
GitHub releases (same approach as AUR qbittorrent-tui-bin).

%prep
# Tarball has no enclosing directory; -c creates %%{name}-%%{version}/ for us.
# -T skips the default Source0 unpack; -a N unpacks SourceN after chdir.
%ifarch x86_64
%setup -q -c -n %{name}-%{version} -T -a 0
%endif
%ifarch aarch64
%setup -q -c -n %{name}-%{version} -T -a 1
%endif
cp -a %{SOURCE2} .

%build
# Prebuilt binary — nothing to compile.

%install
install -Dpm0755 qbt-tui %{buildroot}%{_bindir}/qbt-tui

%check
# Upstream cobra CLI has no --version flag. Confirm the binary runs.
%{buildroot}%{_bindir}/qbt-tui --help | grep -Fqe "qbt-tui"

%files
%license LICENSE
%doc README.md
%{_bindir}/qbt-tui

%changelog
* Fri Sep 25 2026 vitrasti <vitrasti@protonmail.com> - 0.1.5-1
- Initial package for personal COPR
- Based on AUR qbittorrent-tui-bin / upstream goreleaser Linux tarballs
- Install official prebuilt Linux release binary
