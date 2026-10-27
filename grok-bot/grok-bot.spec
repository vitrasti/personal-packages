# Repackage of upstream's official prebuilt Linux x86_64 RPM. Upstream
# installs to /opt/Grok Bot (path contains a space); Chromium's SUID
# sandbox fallback cannot exec from such a path
# (https://github.com/electron/electron/issues/44414), which is fatal on
# Fedora CoreOS, where unprivileged user namespaces are restricted and
# the setuid helper is required. The payload is relocated to
# /opt/grok-bot. Upstream's scriptlets register the vendor dnf repo for
# in-app updates; instead we ship /etc/yum.repos.d/grok-bot.repo
# pointing at this package's COPR, which also marks the install as
# rpm-managed so in-app self-update stays off. No scriptlets.
# Prebuilt Electron binary — do not strip or generate debuginfo.
%global debug_package %{nil}
%global __strip /bin/true
# brp-mangle-shebangs rewrites the bundled node-gyp-build scripts'
# `#!/usr/bin/env node` shebangs to `#!/usr/bin/node`, which (a) modifies
# the payload and (b) makes rpmbuild auto-require /usr/bin/node (the
# nodejs package). The app's node runtime is embedded in the Electron
# binary; the shebangs are inert. Keep the payload verbatim.
%global __spec_install_post \
%(echo '%{__spec_install_post}' | sed -e 's|/usr/lib/rpm/redhat/brp-mangle-shebangs.*||g')

# Upstream release commit; artifacts are pinned to it. Find the current
# one from the update feed (see build-command.md).
%global upstream_commit fe85646036572e2b9a531b337a0dcb56a32f9369
# sha256 of the upstream RPM (artifact pin, verified in %%prep; rpm 6
# removed the standalone checksum tags from the spec syntax).
%global upstream_sha256 b3e66f99ed764cf5092d2a8fbb6948c42f50abfb128c5e30b6d0df0233238fd2

Name:           grok-bot
Version:        0.77.0
Release:        1%{?dist}
Summary:        Grok Bot desktop agent

License:        LicenseRef-Proprietary
URL:            https://x.ai/bot

# Fetched at build time by COPR (and by the local build script, see
# build-command.md); the rename fragment keeps the Source filename
# predictable.
Source0:        https://downloads.cursor.com/grokbot/stable/%{upstream_commit}/linux/x64/%{name}-%{version}-1.x86_64.rpm#/%{name}-%{version}-1.x86_64.rpm

ExclusiveArch:  x86_64

# The app shells out to xdg-open for sign-in.
Requires:       xdg-utils
# Electron dlopens these at runtime, so they are not in the binaries'
# NEEDED lists and auto-detection cannot see them; they come from
# upstream's own RPM/.deb dependency lists.
Requires:       libXss
Requires:       libXtst
Requires:       libnotify
Requires:       libuuid
Requires:       libsecret
Requires:       libdrm
# StatusNotifier tray icon on desktops without a legacy tray.
Recommends:     libappindicator
# Parity with upstream: the executable was named "sand" before 0.24.
Provides:       sand
Conflicts:      sand

BuildRequires:  bash
BuildRequires:  cpio

%description
Grok Bot is xAI's desktop app for always-on AI agents: named Bots with
a shared cloud computer that work inside your tools and apps.

This package repackages upstream's official prebuilt Linux x86_64 RPM.
The app is relocated from upstream's /opt/Grok Bot to /opt/grok-bot so
the setuid chrome-sandbox works on systems with restricted
unprivileged user namespaces (Fedora 43+, Fedora CoreOS); Chromium
cannot exec its SUID helper from a path containing a space. Updates
are owned by the package manager: the shipped
/etc/yum.repos.d/grok-bot.repo points at this package's COPR, which
both feeds the app and marks the install as rpm-managed so in-app
self-update stays off. No scriptlets — safe for rpm-ostree / Fedora
CoreOS / bootc images.

%prep
%setup -q -c -n %{name}-%{version} -T
# Pin the upstream artifact.
echo "%{upstream_sha256}  %{SOURCE0}" | sha256sum -c -
# Unpack the upstream RPM payload (entries are ./opt/... and ./usr/...).
mkdir payload
(cd payload && rpm2cpio %{SOURCE0} | cpio -idm --quiet)

%build
# Prebuilt Electron app — nothing to compile.

%install
install -dm0755 %{buildroot}/opt %{buildroot}%{_sysconfdir}/yum.repos.d \
    %{buildroot}%{_bindir} %{buildroot}%{_datadir}/applications \
    %{buildroot}%{_datadir}/icons
# Relocate the app to the space-free path (see package header).
cp -a "payload/opt/Grok Bot" %{buildroot}/opt/%{name}
cp -a payload/usr/share/applications/grok-bot.desktop %{buildroot}%{_datadir}/applications/
cp -a payload/usr/share/icons/hicolor %{buildroot}%{_datadir}/icons/
# Wrapper on PATH: the desktop entry runs `grok-bot %U`. Chromium
# bundles an older fontconfig; skipping the cache version check avoids
# a warning on every launch.
cat > %{buildroot}%{_bindir}/%{name} <<'EOF'
#!/bin/sh
export FONTCONFIG_NO_CHECK_CACHE_VERSION=1
exec /opt/grok-bot/grok-bot "$@"
EOF
chmod 0755 %{buildroot}%{_bindir}/%{name}
# The SUID sandbox helper is required when unprivileged user namespaces
# are restricted (Fedora 43+, Fedora CoreOS).
chmod 4755 %{buildroot}/opt/%{name}/chrome-sandbox
# Point the bundled AppArmor profile at the relocated path; it stays
# inert unless explicitly loaded.
sed -i "s|/opt/Grok Bot/|/opt/%{name}/|g" %{buildroot}/opt/%{name}/resources/apparmor-profile
# Mark the install as rpm-managed (disables in-app self-update) and
# keep updates in this COPR instead of the vendor's repo.
cat > %{buildroot}%{_sysconfdir}/yum.repos.d/%{name}.repo <<EOF
[grok-bot]
name=Grok Bot (vitrasti personal-packages COPR)
baseurl=https://download.copr.fedorainfracloud.org/results/vitrasti/personal-packages/fedora-\$releasever-\$basearch/
type=rpm-md
gpgcheck=1
gpgkey=https://download.copr.fedorainfracloud.org/results/vitrasti/personal-packages/pubkey.gpg
enabled=1
skip_if_unavailable=1
EOF

%check
test -x %{buildroot}/opt/%{name}/grok-bot
# The payload is verbatim apart from the documented rewrites; the asar
# is never touched.
test "$(sha256sum < "payload/opt/Grok Bot/resources/app.asar")" = \
      "$(sha256sum < %{buildroot}/opt/%{name}/resources/app.asar)"
# Sandbox helper must keep the setuid bit.
test "$(stat -c %a %{buildroot}/opt/%{name}/chrome-sandbox)" = "4755"
# Wrapper must exec the relocated binary.
grep -Fxq 'exec /opt/grok-bot/grok-bot "$@"' %{buildroot}%{_bindir}/%{name}
# Visible desktop entry must point at the wrapper on PATH.
grep -Fq 'Exec=grok-bot %%U' %{buildroot}%{_datadir}/applications/grok-bot.desktop
# Bundled AppArmor profile must reference the relocated path.
grep -Fq 'profile "grok-bot" "/opt/grok-bot/grok-bot"' %{buildroot}/opt/%{name}/resources/apparmor-profile
# Update marker must point at this COPR, never the vendor's repo, and
# be enabled.
grep -Fq 'baseurl=https://download.copr.fedorainfracloud.org/results/vitrasti/personal-packages/fedora-$releasever-$basearch/' \
     %{buildroot}%{_sysconfdir}/yum.repos.d/%{name}.repo
grep -Fxq 'enabled=1' %{buildroot}%{_sysconfdir}/yum.repos.d/%{name}.repo
# No stale reference to the upstream install path may survive.
! grep -rqF "/opt/Grok Bot" %{buildroot}/opt/%{name}
# Payload fidelity: no shebang may have been mangled by a BRP.
head -n1 %{buildroot}/opt/%{name}/resources/app.asar.unpacked/dist/deps/node-gyp-build/bin.js \
    | grep -Fxq '#!/usr/bin/env node'

%files
/opt/%{name}/
%{_bindir}/%{name}
%{_sysconfdir}/yum.repos.d/%{name}.repo
%{_datadir}/applications/grok-bot.desktop
%{_datadir}/icons/hicolor/16x16/apps/grok-bot.png
%{_datadir}/icons/hicolor/24x24/apps/grok-bot.png
%{_datadir}/icons/hicolor/32x32/apps/grok-bot.png
%{_datadir}/icons/hicolor/48x48/apps/grok-bot.png
%{_datadir}/icons/hicolor/64x64/apps/grok-bot.png
%{_datadir}/icons/hicolor/128x128/apps/grok-bot.png
%{_datadir}/icons/hicolor/256x256/apps/grok-bot.png
%{_datadir}/icons/hicolor/512x512/apps/grok-bot.png

%changelog
* Tue Oct 27 2026 vitrasti <vitrasti@protonmail.com> - 0.77.0-1
- Initial package for personal COPR
- Repackage upstream's official prebuilt Linux x86_64 RPM
- Relocate /opt/Grok Bot to /opt/grok-bot (SUID sandbox cannot exec
  from a path with a space; electron#44414) for Fedora CoreOS
- Setuid chrome-sandbox for restricted-userns systems
- Ship grok-bot.repo pointing at this COPR so in-app self-update stays off
