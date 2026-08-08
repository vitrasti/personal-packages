%global             full_name zen-browser
%global             application_name zen
%global             debug_package %{nil}

Name:               zen-browser
Version:            1.21.10b
Release:            2%{?dist}
Summary:            Zen Browser

# Install under /usr/lib (not /opt) so the package layers cleanly on
# rpm-ostree/immutable Fedora, where /opt is typically a symlink to /var/opt.
%global instdir %{_prefix}/lib/%{application_name}

# Bundled browser runtime + native libs must not become system Provides/Requires.
%global __provides_exclude_from ^%{instdir}/.*$
%global __requires_exclude_from ^%{instdir}/.*$

License:            MPLv2.0
URL:                https://github.com/zen-browser/desktop

Source0:            https://github.com/zen-browser/desktop/releases/download/%{version}/zen.linux-x86_64.tar.xz
Source1:            %{full_name}.desktop
Source2:            policies.json
Source3:            %{full_name}

ExclusiveArch:      x86_64

BuildRequires:      patchelf

Recommends:         (plasma-browser-integration if plasma-workspace)
Recommends:         (gnome-browser-connector if gnome-shell)

Requires(post):     gtk-update-icon-cache

%description
Zen Browser is a fork of Firefox that aims to improve the browsing experience
by focusing on a simple, performant, private and beautifully designed browser.

%prep
%setup -q -n %{application_name}

%install
%__rm -rf %{buildroot}

%__install -d %{buildroot}{%{instdir},%{_bindir},%{_datadir}/applications,%{_datadir}/icons/hicolor/128x128/apps,%{_datadir}/icons/hicolor/64x64/apps,%{_datadir}/icons/hicolor/48x48/apps,%{_datadir}/icons/hicolor/32x32/apps,%{_datadir}/icons/hicolor/16x16/apps}

%__cp -r * %{buildroot}%{instdir}

%__install -D -m 0644 %{SOURCE1} -t %{buildroot}%{_datadir}/applications
%__install -D -m 0444 %{SOURCE2} -t %{buildroot}%{instdir}/distribution
%__install -D -m 0755 %{SOURCE3} -t %{buildroot}%{_bindir}

patchelf --set-rpath '$ORIGIN' %{buildroot}%{instdir}/libonnxruntime.so

%__ln_s %{instdir}/browser/chrome/icons/default/default128.png %{buildroot}%{_datadir}/icons/hicolor/128x128/apps/%{full_name}.png
%__ln_s %{instdir}/browser/chrome/icons/default/default64.png  %{buildroot}%{_datadir}/icons/hicolor/64x64/apps/%{full_name}.png
%__ln_s %{instdir}/browser/chrome/icons/default/default48.png  %{buildroot}%{_datadir}/icons/hicolor/48x48/apps/%{full_name}.png
%__ln_s %{instdir}/browser/chrome/icons/default/default32.png  %{buildroot}%{_datadir}/icons/hicolor/32x32/apps/%{full_name}.png
%__ln_s %{instdir}/browser/chrome/icons/default/default16.png  %{buildroot}%{_datadir}/icons/hicolor/16x16/apps/%{full_name}.png

%post
gtk-update-icon-cache -f -t %{_datadir}/icons/hicolor

%files
%{_datadir}/applications/%{full_name}.desktop
%{_datadir}/icons/hicolor/*/apps/%{full_name}.png
%{_bindir}/%{full_name}
%{instdir}/

%changelog
* Sat Aug 08 2026 vitrasti <vitrasti@protonmail.com> - 1.21.10b-2
- Install browser to /usr/lib/zen instead of /opt for rpm-ostree compatibility

* Mon Aug 03 2026 vitrasti <vitrasti@protonmail.com> - 1.21.10b-1
- Initial x86_64 package
