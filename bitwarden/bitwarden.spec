# Repackage spec: downloads Bitwarden's official prebuilt desktop RPM and
# re-wraps its payload. Intended for a personal COPR repo (COPR allows network
# access during builds).

Name:           bitwarden
Version:        2026.9.0
Release:        2%{?dist}
Summary:        Bitwarden Desktop
License:        GPL-3.0-only
URL:            https://bitwarden.com
ExclusiveArch:  x86_64

# Install under /usr/lib (not /opt) so the package layers cleanly on
# rpm-ostree/immutable Fedora (Kinoite, Silverblue, CoreOS), where /opt is
# typically a symlink to /var/opt and is not part of the ostree.
%global instdir %{_prefix}/lib/%{name}

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

This package relocates the official Electron bundle from /opt/Bitwarden to
/usr/lib/bitwarden so it can be layered with rpm-ostree on Fedora CoreOS
and other immutable Fedora variants.

%prep
curl -L -o bitwarden.rpm "https://github.com/bitwarden/clients/releases/download/desktop-v%{version}/Bitwarden-%{version}-x86_64.rpm"
# Pin the upstream RPM checksum. Update this on every version bump
# (sha256sum Bitwarden-%{version}-x86_64.rpm).
echo "8e4c992d8c77855af88700928edf347b3ab9bb113d8d972793876c5097ee9a14  bitwarden.rpm" | sha256sum -c -

%install
mkdir -p %{buildroot}
rpm2cpio bitwarden.rpm | cpio -idmv -D %{buildroot}
# Drop upstream build-ids (extracted under /usr/lib) before relocating the app.
rm -rf %{buildroot}/usr/lib
rm -f %{buildroot}/bitwarden.spec

# Relocate the Electron bundle off /opt for rpm-ostree.
install -dm755 %{buildroot}%{instdir}
cp -a %{buildroot}/opt/Bitwarden/. %{buildroot}%{instdir}/
rm -rf %{buildroot}/opt

# Upstream %post uses update-alternatives to /opt/Bitwarden/bitwarden.
# Point /usr/bin/bitwarden at the relocated wrapper instead.
mkdir -p %{buildroot}%{_bindir}
ln -sf %{instdir}/bitwarden %{buildroot}%{_bindir}/bitwarden

# Remaining text files that still mention /opt (wrapper, desktop, apparmor).
sed -i 's|/opt/Bitwarden|%{instdir}|g' \
    %{buildroot}%{instdir}/bitwarden \
    %{buildroot}%{_datadir}/applications/bitwarden.desktop \
    %{buildroot}%{instdir}/resources/apparmor-profile

# Chromium SUID sandbox helper must be setuid root (matches obsidian/brave).
chmod 4755 %{buildroot}%{instdir}/chrome-sandbox

%files
%defattr(-,root,root,-)
%{instdir}/
%{_bindir}/bitwarden
%{_datadir}/applications/bitwarden.desktop
%{_datadir}/icons/hicolor/*/apps/bitwarden.png

%changelog
* Thu Sep 25 2026 vitrasti <vitrasti@protonmail.com> - 2026.9.0-2
- Install app to /usr/lib/bitwarden instead of /opt for rpm-ostree/CoreOS

* Wed Sep 23 2026 vitrasti <vitrasti@protonmail.com> - 2026.9.0-1
- Update to 2026.9.0
- Update pinned sha256 checksum for upstream RPM

* Sun Sep 07 2026 vitrasti <vitrasti@protonmail.com> - 2026.8.0-1
- Update to 2026.8.0
- Update pinned sha256 checksum for upstream RPM

* Wed Aug 05 2026 vitrasti <vitrasti@protonmail.com> - 2026.7.0-1
- Repackage upstream Bitwarden desktop 2026.7.0
- Use SPDX license identifier (GPL-3.0-only)
- Add ExclusiveArch: x86_64 and BuildRequires: curl, cpio
- Verify sha256 of the downloaded upstream RPM in %prep
