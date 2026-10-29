# Binary repackage of upstream's prebuilt Linux desktop RPM. Upstream
# names its RPM "opencode"; rename to opencode-desktop so the TUI
# package and the desktop package can coexist. COPR has network access,
# so the Source URL is fetched at build time. Prebuilt Electron binary
# — do not strip or generate debuginfo.
%global debug_package %{nil}
%global __strip /bin/true
# /usr/lib, not /opt: /opt is a symlink on bootc/rpm-ostree and RPM
# cannot unpack a package into it. %{_prefix}/lib stays /usr/lib on
# x86_64 (not %{_libdir}, which is /usr/lib64).
%global instdir %{_prefix}/lib/%{name}

Name:           opencode-desktop
Version:        2.2.0
Release:        2%{?dist}
Summary:        OpenCode desktop client for the terminal AI coding agent

License:        MIT
URL:            https://opencode.ai

# Upstream ships a desktop RPM for x86_64 only (arm64 is .deb/AppImage);
# revisit if upstream adds an aarch64 RPM.
Source0:        https://opencode.ai/files/bin/%{version}/opencode-desktop-linux-x86_64.rpm#/%{name}-%{version}-linux-x86_64.rpm
# Local file in this package directory (must be committed next to the spec).
Source1:        LICENSE

ExclusiveArch:  x86_64

# The app shells out to xdg-open; remaining shared-library deps are
# auto-detected from the Electron payload.
Requires:       xdg-utils

BuildRequires:  bash
BuildRequires:  cpio

%description
OpenCode desktop is an Electron desktop client for the OpenCode open
source AI coding agent. It bundles its own CLI and stages it per user
under ~/.config/ai.opencode.desktop at first launch, so the terminal
`opencode` package is not required.

This package repackages upstream's official prebuilt Linux x86_64 RPM
under the name opencode-desktop. The app is relocated from upstream's
/opt/OpenCode to /usr/lib/opencode-desktop so it unpacks on
bootc/rpm-ostree, where /opt is a symlink. Updates are owned by the
package manager: upstream marks the payload with
resources/package-type=rpm, which disables in-app self-update. No
scriptlets, no runtime writes outside $HOME, and a setuid
chrome-sandbox helper for systems with restricted unprivileged user
namespaces.

%prep
%setup -q -c -n %{name}-%{version} -T
# Unpack the upstream RPM payload (entries are ./opt/... and ./usr/...).
mkdir payload
(cd payload && rpm2cpio %{SOURCE0} | cpio -idm --quiet)
cp -a %{SOURCE1} .

%build
# Prebuilt Electron app — nothing to compile.

%install
install -dm0755 %{buildroot}%{instdir} %{buildroot}/usr
# Relocate off /opt. Copy contents so the pre-created instdir is not nested.
cp -a payload/opt/OpenCode/. %{buildroot}%{instdir}/
cp -a payload/usr/. %{buildroot}/usr/
# Chromium requires a root-owned setuid helper when unprivileged user
# namespaces are restricted (Fedora 43+, Fedora CoreOS).
chmod 4755 %{buildroot}%{instdir}/chrome-sandbox
# Desktop entries and the inert AppArmor profile hardcode the upstream
# path. The binary, bundled CLI, and app.asar do not — app.asar embeds
# one unused desktop file, and rewriting that string would corrupt asar
# offsets. Leave the archive byte-identical.
sed -i "s|/opt/OpenCode|%{instdir}|g" \
    %{buildroot}%{_datadir}/applications/ai.opencode.desktop.desktop \
    %{buildroot}%{_datadir}/applications/opencode-desktop.desktop \
    %{buildroot}%{instdir}/resources/apparmor-profile

%check
test -x %{buildroot}%{instdir}/ai.opencode
# Nothing may land under /opt: that path cannot be unpacked on bootc.
test ! -e %{buildroot}/opt
# The bundled CLI is version-pinned to the app and must run.
grep -Fxq "%{version}" %{buildroot}%{instdir}/resources/opencode-cli.version
%{buildroot}%{instdir}/resources/opencode-cli --version | grep -Fqe "%{version}"
# Self-update must stay disabled for package-manager-managed installs.
grep -Fxq "rpm" %{buildroot}%{instdir}/resources/package-type
# Sandbox helper must keep the setuid bit.
test "$(stat -c %a %{buildroot}%{instdir}/chrome-sandbox)" = "4755"
# Installed desktop entries must point at the relocated binary.
grep -Fq "Exec=%{instdir}/ai.opencode %%U" %{buildroot}%{_datadir}/applications/ai.opencode.desktop.desktop
grep -Fq "Exec=%{instdir}/ai.opencode %%U" %{buildroot}%{_datadir}/applications/opencode-desktop.desktop
# Bundled AppArmor profile must reference the relocated path.
grep -Fq 'profile "ai.opencode" "%{instdir}/ai.opencode"' %{buildroot}%{instdir}/resources/apparmor-profile
# asar must stay byte-identical; it is not a safe place to rewrite paths.
test "$(sha256sum < payload/opt/OpenCode/resources/app.asar)" = \
      "$(sha256sum < %{buildroot}%{instdir}/resources/app.asar)"

%files
%license LICENSE
%{instdir}/
%{_datadir}/applications/ai.opencode.desktop.desktop
%{_datadir}/applications/opencode-desktop.desktop
%{_datadir}/icons/hicolor/32x32/apps/ai.opencode.png
%{_datadir}/icons/hicolor/64x64/apps/ai.opencode.png
%{_datadir}/icons/hicolor/128x128/apps/ai.opencode.png
%{_metainfodir}/ai.opencode.desktop.metainfo.xml

%changelog
* Thu Oct 29 2026 vitrasti <vitrasti@protonmail.com> - 2.2.0-2
- Install under /usr/lib/opencode-desktop instead of /opt/OpenCode.
  On bootc/rpm-ostree /opt is a symlink, and RPM unpack fails with
  "mkdir failed - File exists".

* Tue Oct 27 2026 vitrasti <vitrasti@protonmail.com> - 2.2.0-1
- Update to 2.2.0

* Sat Oct 24 2026 vitrasti <vitrasti@protonmail.com> - 2.1.4-1
- Initial package for personal COPR
- Repackage upstream's prebuilt Linux x86_64 desktop RPM
- Setuid chrome-sandbox for restricted-usernames systems (Fedora CoreOS)
- Keep upstream's package-type=rpm marker so in-app self-update stays off
