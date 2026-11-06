# Ghostty 1.4.0 mandates Zig 0.17.0 (build.zig.zon minimum_zig_version), while
# Fedora's zig package is 0.16.0 even on rawhide. This package repackages the
# official upstream prebuilt Zig 0.17.1 toolchain so Ghostty can be built in
# this COPR independently of Fedora's default Zig release.
%global debug_package %{nil}

Name:           zig017
Version:        0.17.1
Release:        1%{?dist}
Summary:        General-purpose programming language and toolchain

License:        MIT
URL:            https://ziglang.org
Source0:        https://ziglang.org/download/%{version}/zig-x86_64-linux-%{version}.tar.xz
Source1:        https://ziglang.org/download/%{version}/zig-aarch64-linux-%{version}.tar.xz

# Both provide /usr/bin/zig; only one may be installed.
Conflicts:      zig

%ifarch x86_64
%global upstream_source %{SOURCE0}
%global upstream_sha256 3581863e3cbcfd0fce0efc682ce7e9e93da96668a977791d356a26d2a7e9b17a
%endif
%ifarch aarch64
%global upstream_source %{SOURCE1}
%global upstream_sha256 a1546d5646eb184437918d6635ca6b762a0e889eac09cef720ee7a1ed3fe7795
%endif

ExclusiveArch:  x86_64 aarch64

BuildRequires:  coreutils

%description
Zig is a general-purpose programming language and toolchain for maintaining
robust, optimal, and reusable software.

This package repackages the official upstream prebuilt compiler so Ghostty can
be built with Zig %{version}, independently of Fedora's default Zig release.

%prep
%setup -q -c -T -n zig-%{version}

# rpm 6 (F44+) removed standalone Source checksum tags; verify manually.
actual_sum="$(sha256sum %{upstream_source} | cut -d' ' -f1)"
if [ "%{upstream_sha256}" != "$actual_sum" ]; then
    echo "ERROR: checksum verification failed for %{upstream_source}" >&2
    echo "Expected: %{upstream_sha256}" >&2
    echo "Actual:   $actual_sum" >&2
    exit 1
fi

tar -xf %{upstream_source} --strip-components=1

%build
# Upstream prebuilt compiler repackaging; nothing to build.

%install
install -Dpm 0755 zig %{buildroot}%{_bindir}/zig
mkdir -p %{buildroot}%{_prefix}/lib
cp -a lib %{buildroot}%{_prefix}/lib/zig

%check
test "$(%{buildroot}%{_bindir}/zig version)" = "%{version}"

%files
%license LICENSE
%doc README.md
%{_bindir}/zig
%{_prefix}/lib/zig/

%changelog
* Fri Nov 06 2026 vitrasti <vitrasti@protonmail.com> - 0.17.1-1
- Update to 0.17.1
- Update pinned sha256 checksums for both upstream toolchains

* Tue Nov 03 2026 vitrasti <vitrasti@protonmail.com> - 0.17.0-1
- Initial package for personal COPR; repackaged upstream prebuilt Zig,
  required to build Ghostty 1.4.0 (spec adapted from the scottames/ghostty COPR)
