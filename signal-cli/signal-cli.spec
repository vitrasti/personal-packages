# Binary package of the upstream GraalVM native image release tarball.
# COPR has network access, so the Source URL is fetched at build time.
# Prebuilt native image — do not strip or generate debuginfo.
# No JVM is required at runtime (JRE 25 is baked into the image).
%global debug_package %{nil}
%global __strip /bin/true

Name:           signal-cli
Version:        0.14.9
Release:        1%{?dist}
Summary:        Commandline interface for the Signal messenger

License:        GPL-3.0-only
URL:            https://github.com/AsamK/signal-cli

# Upstream GraalVM native image: a single self-contained x86_64 binary with
# the libsignal-client natives bundled. x86_64 only — upstream publishes no
# native image for other architectures.
Source0:        %{url}/releases/download/v%{version}/signal-cli-%{version}-Linux-native.tar.gz
# Local file in this package directory (must be committed next to the spec).
Source1:        LICENSE

ExclusiveArch:  x86_64

%description
signal-cli is a commandline interface for the Signal messenger. It supports
registering, verifying, sending and receiving messages, and can run as a
daemon with JSON-RPC and D-BUS interfaces.

This package installs the official prebuilt GraalVM native image from
upstream GitHub releases: a single self-contained x86_64 binary with no
Java runtime requirement.

%prep
# Tarball contains a single top-level binary named "signal-cli" and no
# enclosing directory; -c creates %{name}-%{version}/ for us.
# -T skips the default Source0 unpack; -a 0 unpacks Source0 after chdir.
%setup -q -c -n %{name}-%{version} -T -a 0
cp -a %{SOURCE1} .

%build
# Prebuilt binary — nothing to compile.

%install
install -Dpm0755 signal-cli %{buildroot}%{_bindir}/signal-cli

%check
%{buildroot}%{_bindir}/signal-cli --version | grep -Fqe "%{version}"

%files
%license LICENSE
%{_bindir}/signal-cli

%changelog
* Wed Oct 07 2026 vitrasti <vitrasti@protonmail.com> - 0.14.9-1
- Initial package for personal COPR
- Install official prebuilt GraalVM native image (x86_64 only)
- No JVM runtime requirement
