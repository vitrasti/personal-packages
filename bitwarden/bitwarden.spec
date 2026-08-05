# Repackage spec: downloads Bitwarden's official prebuilt desktop RPM and
# re-wraps its payload. Intended for a personal COPR repo (COPR allows network
# access during builds).

Name:           bitwarden
Version:        2026.7.0
Release:        1%{?dist}
Summary:        Bitwarden Desktop
License:        GPL-3.0-only
URL:            https://bitwarden.com
ExclusiveArch:  x86_64

# Repackaging a prebuilt binary: disable RPM's automatic dependency generation,
# build-id extraction, and binary post-processing so it doesn't choke on the
# bundled Electron/Chromium blobs.
%global _build_id_links none
%define _use_internal_dependency_generator 0
%global __find_requires %{nil}
%global __os_install_post %{nil}

# Fetch + unpack tools
BuildRequires: curl
BuildRequires: cpio

# Runtime deps mirror those declared by Bitwarden's own upstream RPM.
Requires: at-spi2-core
Requires: gtk3
Requires: libXScrnSaver
Requires: libnotify
Requires: nss
Requires: xdg-utils
Requires: (libXtst or libXtst6)
Requires: (libuuid or libuuid1)

%description
Bitwarden Desktop repackaged for COPR.

%prep
curl -L -o bitwarden.rpm "https://github.com/bitwarden/clients/releases/download/desktop-v%{version}/Bitwarden-%{version}-x86_64.rpm"
# Pin the upstream RPM checksum. Update this on every version bump
# (sha256sum Bitwarden-%{version}-x86_64.rpm).
echo "528f413f8dc6c2ff9367135a9d7f012e0e63bf3f819272e225f9b98112f12594  bitwarden.rpm" | sha256sum -c -

%install
mkdir -p %{buildroot}
rpm2cpio bitwarden.rpm | cpio -idmv -D %{buildroot}
rm -rf %{buildroot}/usr/lib
rm -f %{buildroot}/bitwarden.spec
mkdir -p %{buildroot}%{_bindir}
ln -sf /opt/Bitwarden/bitwarden %{buildroot}%{_bindir}/bitwarden

%files
%defattr(-,root,root,-)
/opt/Bitwarden/
/usr/bin/bitwarden
/usr/share/applications/bitwarden.desktop
/usr/share/icons/hicolor/*/apps/bitwarden.png

%changelog
* Wed Aug 05 2026 vitrasti <vitrasti@protonmail.com> - 2026.7.0-1
- Repackage upstream Bitwarden desktop 2026.7.0
- Use SPDX license identifier (GPL-3.0-only)
- Add ExclusiveArch: x86_64 and BuildRequires: curl, cpio
- Verify sha256 of the downloaded upstream RPM in %prep
