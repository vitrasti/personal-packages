%global debug_package %{nil}
# Repackaged prebuilt binaries ship many bundled .so files; disable build-id
# link generation to avoid duplicate/missing build-id errors during rpmbuild.
%global _build_id_links none

# KOReader bundles all of its libraries privately under /usr/lib/koreader.
# Do NOT let the dependency generator advertise those as system-wide Provides
# (e.g. libSDL3.so.0, libssl.so, libcrypto.so) or generate internal Requires
# on them. Real system deps are declared explicitly below.
%global __provides_exclude_from ^%{_prefix}/lib/koreader/.*$
%global __requires_exclude_from ^%{_prefix}/lib/koreader/.*$

Name:           koreader
Version:        2026.07.1
Release:        1%{?dist}
Summary:        Ebook reader supporting PDF, DjVu, EPUB, FB2 and many more formats

License:        AGPL-3.0-only
URL:            https://github.com/koreader/koreader
Source0:        https://github.com/koreader/koreader/releases/download/v%{version}/koreader_%{version}-1_amd64.deb

ExclusiveArch:  x86_64

# Runtime (matches current AUR koreader-bin; upstream moved from SDL2 → SDL3)
Requires:       SDL3
Requires:       google-noto-sans-fonts
# System libraries the bundled binaries link against (auto-dep generation is
# disabled for the private lib dir, so declare the non-glibc ones explicitly).
Requires:       libstdc++
Requires:       libgcc
# Optional but useful on Fedora:
Recommends:      google-noto-serif-fonts
Recommends:      google-droid-sans-fonts

BuildRequires:  binutils
BuildRequires:  tar
BuildRequires:  xz
# data.tar may be .xz or .zst depending on release
BuildRequires:  zstd

%description
KOReader is a document viewer optimized for e-ink devices and also available
on desktop Linux. Supported formats include EPUB, PDF, DjVu, XPS, CBZ, FB2,
MOBI, TXT, HTML, and more.

This package installs the official Linux build by extracting the upstream
amd64 .deb (same approach as AUR koreader-bin).

%prep
# Extract the .deb
rm -rf dpkgdir
mkdir dpkgdir
ar x %{SOURCE0}
# data.tar.* name varies by release
for f in data.tar.*; do
  case "$f" in
    *.zst) tar --use-compress-program=unzstd -xf "$f" -C dpkgdir ;;
    *)     tar -xf "$f" -C dpkgdir ;;
  esac
done

%build
# Binary package — nothing to compile

%install
cp -a dpkgdir/* %{buildroot}/

# Normalize paths if the deb used /usr/lib vs /usr/lib64 (usually /usr)
# Leave as shipped unless you hit multilib layout issues.

%files
# The .deb installs everything under /usr. Note it uses /usr/lib (not
# /usr/lib64), and app/icon/metainfo IDs are "rocks.koreader.KOReader".
%{_bindir}/koreader
%{_prefix}/lib/koreader/
%{_datadir}/applications/rocks.koreader.KOReader.desktop
%{_datadir}/icons/hicolor/*/apps/rocks.koreader.KOReader.*
%{_datadir}/metainfo/rocks.koreader.KOReader.metainfo.xml
%{_mandir}/man1/koreader.1*
%license %{_docdir}/koreader/copyright
%doc %{_docdir}/koreader/COPYING
%doc %{_docdir}/koreader/changelog.Debian.gz

%changelog
* Tue Aug 04 2026 vitrasti <vitrasti@protonmail.com> - 2026.07.1-1
- Update to 2026.07.1
- Fix %%files to match actual .deb layout (/usr/lib, rocks.koreader.KOReader
  desktop/icon/metainfo IDs, man page)

* Tue Aug 04 2026 vitrasti <vitrasti@protonmail.com> - 2026.07-1
- Initial package based on official amd64 .deb / AUR koreader-bin
