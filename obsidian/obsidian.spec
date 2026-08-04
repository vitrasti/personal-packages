%global debug_package %{nil}

# Prebuilt, self-contained Electron bundle: don't let RPM strip the vendored
# binaries (matches Arch's options=(!strip)).
%global __strip /bin/true

# Install location for the whole Electron application bundle.
%global instdir %{_prefix}/lib/%{name}

# The bundle ships its own Electron runtime plus vendored shared libraries
# (libffmpeg, ANGLE, swiftshader, vulkan...). The obsidian binary loads them via
# RPATH=$ORIGIN, so they must NOT be advertised as system Provides, nor pulled
# in as system Requires (nothing on Fedora provides them).
%global __provides_exclude_from ^%{instdir}/.*$
%global __requires_exclude ^lib(EGL|GLESv2|ffmpeg|vk_swiftshader|vulkan)\.so.*$

Name:           obsidian
Version:        1.13.4
Release:        1%{?dist}
Summary:        Knowledge base that works on a local folder of Markdown files

# Proprietary; Arch uses LicenseRef-Obsidian
License:        LicenseRef-Obsidian
URL:            https://obsidian.md

Source0:        https://github.com/obsidianmd/obsidian-releases/releases/download/v%{version}/obsidian-%{version}.tar.gz
Source1:        obsidian.desktop
Source2:        LICENSE-Obsidian

ExclusiveArch:  x86_64

Requires:       hicolor-icon-theme

# Informational: this package bundles its own Electron runtime.
Provides:       bundled(electron)

%description
Obsidian is a powerful knowledge base that works on top of a local folder of
plain text Markdown files.

Unlike the Arch Linux package, which strips the bundled Electron and relies on
a system electron package, this build keeps the Electron runtime that ships in
the upstream release, since Fedora does not provide a separate Electron package.

%prep
%autosetup -n obsidian-%{version}

%build
# Prebuilt binary bundle — nothing to compile.

%install
# Ship the entire upstream application bundle (Electron runtime + resources).
install -dm755 %{buildroot}%{instdir}
cp -a . %{buildroot}%{instdir}/

# Launcher: a plain symlink is enough. Electron resolves its resources and its
# vendored libraries (RPATH=$ORIGIN) relative to the real binary path via
# /proc/self/exe, so no wrapper script is required.
install -dm755 %{buildroot}%{_bindir}
ln -sf %{instdir}/obsidian %{buildroot}%{_bindir}/obsidian

# The Chromium SUID sandbox helper must be setuid root, otherwise Electron
# aborts with "The SUID sandbox helper binary was found, but is not configured
# correctly".
chmod 4755 %{buildroot}%{instdir}/chrome-sandbox

# Desktop entry
install -Dm644 %{SOURCE1} %{buildroot}%{_datadir}/applications/%{name}.desktop

# Icon (shipped inside the bundle resources)
install -Dm644 resources/icon.png \
  %{buildroot}%{_datadir}/icons/hicolor/512x512/apps/%{name}.png

# License
install -Dm644 %{SOURCE2} \
  %{buildroot}%{_datadir}/licenses/%{name}/LICENSE-Obsidian

%post
/bin/touch --no-create %{_datadir}/icons/hicolor &>/dev/null || :
gtk-update-icon-cache -f -t %{_datadir}/icons/hicolor &>/dev/null || :
update-desktop-database -q %{_datadir}/applications &>/dev/null || :

%postun
/bin/touch --no-create %{_datadir}/icons/hicolor &>/dev/null || :
gtk-update-icon-cache -f -t %{_datadir}/icons/hicolor &>/dev/null || :
update-desktop-database -q %{_datadir}/applications &>/dev/null || :

%files
%license %{_datadir}/licenses/%{name}/LICENSE-Obsidian
%{_bindir}/obsidian
%{instdir}/
%{_datadir}/applications/%{name}.desktop
%{_datadir}/icons/hicolor/512x512/apps/%{name}.png

%changelog
* Tue Aug 04 2026 vitrasti <vitrasti@protonmail.com> - 1.13.4-1
- Initial package based on the official Arch Linux PKGBUILD
