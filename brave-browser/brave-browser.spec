%global debug_package %{nil}

# Prebuilt Chromium bundle: don't strip vendored binaries (matches AUR
# brave-bin options=(!strip) and this repo's obsidian package).
%global __strip /bin/true
%global _build_id_links none
# Keep chrome-sandbox setuid and leave bundled ELF files untouched.
%global __os_install_post %{nil}

# Install under /usr/lib (not /opt) so the package layers cleanly on
# rpm-ostree/immutable Fedora (Kinoite, Silverblue, CoreOS), where /opt is
# typically a symlink to /var/opt and is not part of the ostree.
%global instdir %{_prefix}/lib/brave-browser

# Bundled Chromium runtime + native libs must not become system Provides/Requires.
%global __provides_exclude_from ^%{instdir}/.*$
%global __requires_exclude_from ^%{instdir}/.*$

Name:           brave-browser
Version:        1.96.59
Release:        1%{?dist}
Summary:        Web browser that blocks ads and trackers by default

License:        MPL-2.0 AND BSD-3-Clause
URL:            https://brave.com

# Official upstream RPM (includes desktop/appdata/man pages). Relocated off /opt.
Source0:        https://github.com/brave/brave-browser/releases/download/v%{version}/brave-browser-%{version}-1.x86_64.rpm

ExclusiveArch:  x86_64

BuildRequires:  cpio

# Runtime deps follow AUR brave-bin + Nixpkgs brave (system libs the
# bundled binary links against; auto-deps are disabled for instdir).
Requires:       alsa-lib
Requires:       at-spi2-atk
Requires:       at-spi2-core
Requires:       cairo
Requires:       cups-libs
Requires:       dbus-libs
Requires:       expat
Requires:       glib2
Requires:       gtk3
Requires:       hicolor-icon-theme
Requires:       libX11
Requires:       libXScrnSaver
Requires:       libXcomposite
Requires:       libXdamage
Requires:       libXext
Requires:       libXfixes
Requires:       libXrandr
Requires:       libXtst
Requires:       libatomic
Requires:       libdrm
Requires:       libuuid
Requires:       libxcb
Requires:       libxkbcommon
Requires:       mesa-libgbm
Requires:       nspr
Requires:       nss
Requires:       pango
Requires:       xdg-utils

Recommends:     libnotify
Recommends:     (plasma-browser-integration if plasma-workspace)
Recommends:     (gnome-browser-connector if gnome-shell)

%description
Brave is a web browser that blocks ads and trackers by default.

This package repacks the official Linux x86_64 RPM (same payload as Nixpkgs
brave, which uses the .deb) and installs the browser under
/usr/lib/brave-browser instead of /opt, so it can be layered with rpm-ostree
on Kinoite/Silverblue/CoreOS. Upstream desktop, appdata, and man pages are
kept.

%prep
# Binary republish of the official RPM — nothing to unpack here.

%build
# Prebuilt binary bundle — nothing to compile.

%install
mkdir -p %{buildroot}
rpm2cpio %{SOURCE0} | cpio -idmv -D %{buildroot}

# Relocate the Chromium bundle off /opt for rpm-ostree.
install -dm755 %{buildroot}%{instdir}
cp -a %{buildroot}/opt/brave.com/brave/. %{buildroot}%{instdir}/
rm -rf %{buildroot}/opt

# Vendor cron hits /opt and is useless on ostree; COPR is the update path.
rm -rf %{buildroot}/etc/cron.daily
rm -rf %{buildroot}/etc/yum.repos.d

# Upstream ships /usr/bin/brave-browser-stable -> /opt/brave.com/brave/brave-browser.
# Point it (and the usual aliases) at the relocated inner wrapper, which
# resolves resources via dirname($0) so it does not hardcode /opt.
rm -f %{buildroot}%{_bindir}/brave-browser-stable \
      %{buildroot}%{_bindir}/brave-browser
ln -sf %{instdir}/brave-browser %{buildroot}%{_bindir}/brave-browser-stable
ln -sf brave-browser-stable %{buildroot}%{_bindir}/brave-browser
ln -sf brave-browser-stable %{buildroot}%{_bindir}/brave

# Remaining text files that still mention /opt.
sed -i 's|/opt/brave.com/brave|%{instdir}|g' \
    %{buildroot}%{_datadir}/gnome-control-center/default-apps/brave-browser.xml \
    %{buildroot}%{instdir}/default-app-block \
    %{buildroot}%{instdir}/apparmor.d/brave-browser-stable

# Chromium SUID sandbox helper must be setuid root.
chmod 4755 %{buildroot}%{instdir}/chrome-sandbox

# Upstream installs icons in %post via xdg-icon-resource using /opt paths.
# Bake them into the payload so they survive rpm-ostree layering.
for size in 16 24 32 48 64 128 256; do
    install -Dm644 %{buildroot}%{instdir}/product_logo_${size}.png \
        %{buildroot}%{_datadir}/icons/hicolor/${size}x${size}/apps/%{name}.png
done

# Fedora ships /usr/share/appdata as a symlink to metainfo.
install -Dm644 %{buildroot}%{_datadir}/appdata/brave-browser.appdata.xml \
    %{buildroot}%{_metainfodir}/brave-browser.appdata.xml
rm -rf %{buildroot}%{_datadir}/appdata

install -Dm644 %{buildroot}%{instdir}/LICENSE \
    %{buildroot}%{_datadir}/licenses/%{name}/LICENSE

%post
/bin/touch --no-create %{_datadir}/icons/hicolor &>/dev/null || :
gtk-update-icon-cache -f -t %{_datadir}/icons/hicolor &>/dev/null || :
update-desktop-database -q %{_datadir}/applications &>/dev/null || :

%postun
/bin/touch --no-create %{_datadir}/icons/hicolor &>/dev/null || :
gtk-update-icon-cache -f -t %{_datadir}/icons/hicolor &>/dev/null || :
update-desktop-database -q %{_datadir}/applications &>/dev/null || :

%files
%license %{_datadir}/licenses/%{name}/LICENSE
%{_bindir}/brave-browser
%{_bindir}/brave-browser-stable
%{_bindir}/brave
%{instdir}/
%{_datadir}/applications/brave-browser.desktop
%{_datadir}/applications/com.brave.Browser.desktop
%{_metainfodir}/brave-browser.appdata.xml
%{_datadir}/gnome-control-center/default-apps/brave-browser.xml
%{_datadir}/icons/hicolor/*/apps/%{name}.png
%{_mandir}/man1/brave-browser.1*
%{_mandir}/man1/brave-browser-stable.1*

%changelog
* Wed Sep 24 2026 vitrasti <vitrasti@protonmail.com> - 1.96.59-1
- Initial package based on the official Brave RPM / Nixpkgs brave / AUR brave-bin
- Keep upstream .desktop, appdata, and man pages
- Install browser to /usr/lib/brave-browser instead of /opt for rpm-ostree
