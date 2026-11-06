# Ghostty is not in the Fedora repositories. It is built from the official
# release source tarball with the zig017 companion package from this COPR
# (Ghostty 1.4.0 mandates Zig 0.17.0; Fedora's zig is 0.16.0).
#
# Fedora CoreOS / rpm-ostree notes:
# - No scriptlets of any kind; safe for ostree layering.
# - All payload installs under /usr (part of the ostree image); nothing in
#   /opt, which is a symlink to /var/opt on bootc/rpm-ostree and where RPM
#   unpack fails.
# - Updates are owned by the package manager (rpm-ostree / dnf from this
#   COPR). Ghostty has no in-app updater on Linux, so there is nothing to
#   disable.
# - The upstream build installs the systemd user unit to
#   /usr/share/systemd/user, which systemd does not search; we move it to
#   /usr/lib/systemd/user so `systemctl --user enable` and the XDG portal's
#   app-<appid> lookup work out of the box.
# - Fedora's ncurses-term (F42+) owns /usr/share/terminfo/g/ghostty, so the
#   upstream copy is dropped on F42+ to avoid a file conflict.
#
# Spec adapted from the scottames/ghostty COPR.

# Zig emits no .note.gnu.build-id, so find-debuginfo --strict-build-id
# (run automatically in %install) aborts the build. Disable the debug
# subpackage, as every other package in this repo does.
%global debug_package %{nil}

# Upstream's libghostty-vt.a is a fat archive whose member names are build
# cache paths (.zig-cache/o/<hash>/...). binutils cannot extract those
# names, so brp-strip/brp-strip-lto fail on it. Turn the rpm strip passes
# off and strip the shipped ELF objects explicitly in %install (same
# approach as the other binary packages in this repo).
%global __strip /bin/true

Name:           ghostty
Version:        1.4.0
Release:        4%{?dist}
Summary:        Fast, feature-rich, and cross-platform terminal emulator that uses platform-native UI and GPU acceleration

License:        MIT
URL:            https://github.com/ghostty-org/ghostty
Source0:        https://release.files.ghostty.org/%{version}/ghostty-%{version}.tar.gz
%global upstream_sha256 cb188ac6c3a8278d5fd7bfef15d8c017104c87f638b5560eb38024a71ae0f005

ExclusiveArch: x86_64 aarch64

BuildRequires: bzip2-devel
BuildRequires: fontconfig-devel
BuildRequires: freetype-devel
BuildRequires: glib2-devel
BuildRequires: gtk4-devel
BuildRequires: gtk4-layer-shell-devel
BuildRequires: harfbuzz-devel
BuildRequires: libadwaita-devel
BuildRequires: libpng-devel
BuildRequires: oniguruma-devel
BuildRequires: pandoc-cli
BuildRequires: pixman-devel
BuildRequires: pkg-config
BuildRequires: pkgconfig(egl)
BuildRequires: wayland-protocols-devel
BuildRequires: zig017 = 0.17.1
BuildRequires: zlib-ng-devel

Requires: fontconfig
Requires: freetype
Requires: glib2
Requires: gtk4
Requires: harfbuzz
Requires: libadwaita
Requires: libpng
Requires: oniguruma
Requires: pixman
Requires: zlib-ng
# The reference build leaves these as raw soname requires; make them
# package-level.
Requires: libglvnd-egl
Requires: gtk4-layer-shell
Requires: libwayland-client
Requires: libX11

%description
%{summary}. It is written in Zig, uses the platform-native GTK4/libadwaita
toolkit on Linux, and renders with GPU acceleration.

%package        devel
Summary:        Development files for libghostty-vt
Requires:       %{name}%{?_isa} = %{version}-%{release}

%description    devel
This package provides the development files for libghostty-vt.

%prep
# rpm 6 (F44+) removed standalone Source checksum tags; verify manually.
echo "%{upstream_sha256}  %{SOURCE0}" | sha256sum -c -
%setup -q -n ghostty-%{version}

%build
# zig's default step is "install". Running it here writes to --prefix (/usr);
# mockbuild cannot, so the build fails with AccessDenied. rpmbuild also wipes
# the buildroot at the start of %%install, so stage the install there instead.
:

%install
# Link the system fontconfig/freetype/harfbuzz rather than letting zig vendor
# them. Without -fsys=, zig statically links its own copies *and* exports their
# symbols from the executable, while GTK4 separately pulls in the system libs.
# The executable wins global symbol resolution, so GTK's Fc*/FT_*/hb_* calls are
# interposed into the vendored copies while operating on system-lib state.
DESTDIR=%{buildroot} zig build \
    --summary all \
    --prefix "%{_prefix}" \
    -fsys=fontconfig \
    -fsys=freetype \
    -fsys=harfbuzz \
    -Dversion-string=%{version}-%{release} \
    -Doptimize=ReleaseFast \
    -Dcpu=baseline \
    -Dpie=true \
    -Dstrip=false \
    -Demit-docs \
    -Demit-themes=true

%if 0%{?fedora} >= 42
    rm -f "%{buildroot}%{_prefix}/share/terminfo/g/ghostty"
%endif

# The build installs the user unit to share/systemd/user, which is not in
# systemd's user-unit search path. Move it where system installs are found.
install -d %{buildroot}%{_prefix}/lib/systemd/user
mv "%{buildroot}%{_prefix}/share/systemd/user/app-com.mitchellh.ghostty.service" \
   "%{buildroot}%{_prefix}/lib/systemd/user/"
rmdir "%{buildroot}%{_prefix}/share/systemd/user"

# Upstream's pkg-config-generator embeds the absolute BUILDROOT path in
# prefix= (DESTDIR staging), which check-buildroot rejects as an
# RPATH-style violation. Rewrite to the real prefix.
sed -i 's|^prefix=.*|prefix=%{_prefix}|' \
    %{buildroot}%{_prefix}/share/pkgconfig/libghostty-vt.pc \
    %{buildroot}%{_prefix}/share/pkgconfig/libghostty-vt-static.pc

# brp-strip is disabled above (see the fat-archive note), so strip the two
# shipped ELF objects here. The static archive is left untouched: its
# members still link, but their names cannot be handled by binutils tools.
/usr/bin/strip -g %{buildroot}%{_bindir}/ghostty
/usr/bin/strip -g %{buildroot}%{_prefix}/lib/libghostty-vt.so.0.1.0

%check
test -x "%{buildroot}%{_bindir}/ghostty"
test -f "%{buildroot}%{_prefix}/lib/libghostty-vt.so.0.1.0"
test -f "%{buildroot}%{_prefix}/share/applications/com.mitchellh.ghostty.desktop"
test -f "%{buildroot}%{_prefix}/lib/systemd/user/app-com.mitchellh.ghostty.service"
test ! -e "%{buildroot}%{_prefix}/share/systemd/user"
%if 0%{?fedora} >= 42
    test ! -e "%{buildroot}%{_prefix}/share/terminfo/g/ghostty"
%endif
# The version string is compiled in via -Dversion-string. Use --version:
# the `version` subcommand initializes GTK and fails without a display.
%{buildroot}%{_bindir}/ghostty --version 2>&1 | grep -q "%{version}"

%files
%license LICENSE
%{_bindir}/ghostty
%{_prefix}/share/applications/com.mitchellh.ghostty.desktop
%{_prefix}/share/bash-completion/completions/ghostty.bash
%{_prefix}/share/bat/syntaxes/ghostty.sublime-syntax
%{_prefix}/share/fish/vendor_completions.d/ghostty.fish
%{_prefix}/share/ghostty
%{_prefix}/share/icons/hicolor/1024x1024/apps/com.mitchellh.ghostty.png
%{_prefix}/share/icons/hicolor/128x128/apps/com.mitchellh.ghostty.png
%{_prefix}/share/icons/hicolor/128x128@2/apps/com.mitchellh.ghostty.png
%{_prefix}/share/icons/hicolor/16x16/apps/com.mitchellh.ghostty.png
%{_prefix}/share/icons/hicolor/16x16@2/apps/com.mitchellh.ghostty.png
%{_prefix}/share/icons/hicolor/256x256/apps/com.mitchellh.ghostty.png
%{_prefix}/share/icons/hicolor/256x256@2/apps/com.mitchellh.ghostty.png
%{_prefix}/share/icons/hicolor/32x32/apps/com.mitchellh.ghostty.png
%{_prefix}/share/icons/hicolor/32x32@2/apps/com.mitchellh.ghostty.png
%{_prefix}/share/icons/hicolor/512x512/apps/com.mitchellh.ghostty.png
%{_prefix}/share/kio/servicemenus/com.mitchellh.ghostty.desktop
%{_mandir}/man1/ghostty.1*
%{_mandir}/man5/ghostty.5*
%{_prefix}/share/nautilus-python/extensions/ghostty.py
%{_prefix}/share/nvim/site/compiler/ghostty.vim
%{_prefix}/share/nvim/site/ftdetect/ghostty.vim
%{_prefix}/share/nvim/site/ftplugin/ghostty.vim
%{_prefix}/share/nvim/site/syntax/ghostty.vim
%{_prefix}/share/vim/vimfiles/compiler/ghostty.vim
%{_prefix}/share/vim/vimfiles/ftdetect/ghostty.vim
%{_prefix}/share/vim/vimfiles/ftplugin/ghostty.vim
%{_prefix}/share/vim/vimfiles/syntax/ghostty.vim
%{_prefix}/share/zsh/site-functions/_ghostty
%{_prefix}/share/dbus-1/services/com.mitchellh.ghostty.service
%{_prefix}/share/locale/*/LC_MESSAGES/com.mitchellh.ghostty.mo
%{_prefix}/share/metainfo/com.mitchellh.ghostty.metainfo.xml
%{_prefix}/lib/systemd/user/app-com.mitchellh.ghostty.service
%{_prefix}/lib/libghostty-vt.so.0
%{_prefix}/lib/libghostty-vt.so.0.1.0

%{_prefix}/share/terminfo/x/xterm-ghostty
%if 0%{?fedora} < 42
    %{_prefix}/share/terminfo/g/ghostty
%endif

%files devel
%{_prefix}/include/ghostty/vt.h
%{_prefix}/include/ghostty/vt/
%{_prefix}/lib/libghostty-vt.so
%{_prefix}/lib/libghostty-vt.a
%{_prefix}/share/pkgconfig/libghostty-vt.pc
%{_prefix}/share/pkgconfig/libghostty-vt-static.pc

%changelog
* Fri Nov 06 2026 vitrasti <vitrasti@protonmail.com> - 1.4.0-4
- Update the pinned zig017 build dependency to 0.17.1

* Wed Nov 04 2026 vitrasti <vitrasti@protonmail.com> - 1.4.0-3
- Match gzipped man pages. brp-compress renames ghostty.1 and ghostty.5
  to *.gz, so the uncompressed %%files entries were missing.

* Wed Nov 04 2026 vitrasti <vitrasti@protonmail.com> - 1.4.0-2
- Do not run zig build in %%build. Its default step installs to /usr, which
  mockbuild cannot write, so the COPR build failed with AccessDenied.
  Stage the install in %%install with DESTDIR.

* Tue Nov 03 2026 vitrasti <vitrasti@protonmail.com> - 1.4.0-1
- Initial package for personal COPR (spec adapted from the scottames/ghostty
  COPR)
- Install the systemd user unit to /usr/lib/systemd/user, which systemd
  actually searches (upstream's share/ location is not found on Fedora
  CoreOS)
- Require libglvnd-egl, gtk4-layer-shell, libwayland-client and libX11 at
  package level instead of leaving raw soname requires
- Disable the debug subpackage and rpm's strip passes; Zig emits no build
  ID and the fat static archive has unextractable member names
- Rewrite the generated pkg-config prefix so check-buildroot passes
