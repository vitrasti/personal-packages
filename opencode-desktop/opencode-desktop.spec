# Binary repackage of upstream's prebuilt Linux desktop RPM. Upstream
# names its RPM "opencode"; rename to opencode-desktop so the TUI
# package and the desktop package can coexist. COPR has network access,
# so the Source URL is fetched at build time. Prebuilt Electron binary
# — do not strip or generate debuginfo.
%global debug_package %{nil}
%global __strip /bin/true

Name:           opencode-desktop
Version:        2.2.0
Release:        1%{?dist}
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
under the name opencode-desktop; the app lives in /opt/OpenCode.
Updates are owned by the package manager: upstream marks the payload
with resources/package-type=rpm, which disables in-app self-update.
This keeps the package compatible with rpm-ostree / Fedora CoreOS /
bootc images: no scriptlets, no runtime writes outside $HOME, and a
setuid chrome-sandbox helper for systems with restricted unprivileged
user namespaces.

%prep
%setup -q -c -n %{name}-%{version} -T
# Unpack the upstream RPM payload (entries are ./opt/... and ./usr/...).
mkdir payload
(cd payload && rpm2cpio %{SOURCE0} | cpio -idm --quiet)
cp -a %{SOURCE1} .

%build
# Prebuilt Electron app — nothing to compile.

%install
install -dm0755 %{buildroot}/opt %{buildroot}/usr
cp -a payload/opt/. %{buildroot}/opt/
cp -a payload/usr/. %{buildroot}/usr/
# Chromium requires a root-owned setuid helper when unprivileged user
# namespaces are restricted (Fedora 43+, Fedora CoreOS).
chmod 4755 %{buildroot}/opt/OpenCode/chrome-sandbox

%check
test -x %{buildroot}/opt/OpenCode/ai.opencode
# The bundled CLI is version-pinned to the app and must run.
grep -Fxq "%{version}" %{buildroot}/opt/OpenCode/resources/opencode-cli.version
%{buildroot}/opt/OpenCode/resources/opencode-cli --version | grep -Fqe "%{version}"
# Self-update must stay disabled for package-manager-managed installs.
grep -Fxq "rpm" %{buildroot}/opt/OpenCode/resources/package-type
# Sandbox helper must keep the setuid bit.
test "$(stat -c %a %{buildroot}/opt/OpenCode/chrome-sandbox)" = "4755"
# Visible desktop entry must point at the installed app.
grep -Fq "Exec=/opt/OpenCode/ai.opencode %U" %{buildroot}%{_datadir}/applications/ai.opencode.desktop.desktop

%files
%license LICENSE
/opt/OpenCode/
%{_datadir}/applications/ai.opencode.desktop.desktop
%{_datadir}/applications/opencode-desktop.desktop
%{_datadir}/icons/hicolor/32x32/apps/ai.opencode.png
%{_datadir}/icons/hicolor/64x64/apps/ai.opencode.png
%{_datadir}/icons/hicolor/128x128/apps/ai.opencode.png
%{_metainfodir}/ai.opencode.desktop.metainfo.xml

%changelog
* Tue Oct 27 2026 vitrasti <vitrasti@protonmail.com> - 2.2.0-1
- Update to 2.2.0

* Sat Oct 24 2026 vitrasti <vitrasti@protonmail.com> - 2.1.4-1
- Initial package for personal COPR
- Repackage upstream's prebuilt Linux x86_64 desktop RPM
- Setuid chrome-sandbox for restricted-usernames systems (Fedora CoreOS)
- Keep upstream's package-type=rpm marker so in-app self-update stays off
