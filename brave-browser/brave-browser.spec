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

# Same upstream zip as AUR brave-bin; installed to /usr/lib instead of /opt.
Source0:        https://github.com/brave/brave-browser/releases/download/v%{version}/brave-browser-%{version}-linux-amd64.zip
Source1:        brave-browser
Source2:        brave-browser.desktop

ExclusiveArch:  x86_64

BuildRequires:  unzip

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

This package repacks the official Linux amd64 zip (same source as AUR
brave-bin) and installs the browser under /usr/lib/brave-browser instead
of /opt, so it can be layered with rpm-ostree on Kinoite/Silverblue/CoreOS.

%prep
# Zip has no top-level directory; -c creates the build dir first.
%setup -q -c -n brave
chmod +x brave

%build
# Prebuilt binary bundle — nothing to compile.

%install
install -dm755 %{buildroot}%{instdir}
cp -a . %{buildroot}%{instdir}/

# Chromium SUID sandbox helper must be setuid root.
chmod 4755 %{buildroot}%{instdir}/chrome-sandbox

install -Dm755 %{SOURCE1} %{buildroot}%{_bindir}/brave-browser
ln -sf brave-browser %{buildroot}%{_bindir}/brave
ln -sf brave-browser %{buildroot}%{_bindir}/brave-browser-stable

install -Dm644 %{SOURCE2} %{buildroot}%{_datadir}/applications/%{name}.desktop

for size in 16 24 32 48 64 128 256; do
    install -Dm644 product_logo_${size}.png \
        %{buildroot}%{_datadir}/icons/hicolor/${size}x${size}/apps/%{name}.png
done

install -Dm644 LICENSE %{buildroot}%{_datadir}/licenses/%{name}/LICENSE

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
%{_bindir}/brave
%{_bindir}/brave-browser-stable
%{instdir}/
%{_datadir}/applications/%{name}.desktop
%{_datadir}/icons/hicolor/*/apps/%{name}.png

%changelog
* Wed Sep 24 2026 vitrasti <vitrasti@protonmail.com> - 1.96.59-1
- Initial package based on AUR brave-bin and Nixpkgs brave
- Install browser to /usr/lib/brave-browser instead of /opt for rpm-ostree
