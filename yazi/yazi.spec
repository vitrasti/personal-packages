# Tests off by default for reliable personal COPR builds; enable with --with check.
%bcond_with check

%global __brp_mangle_shebangs   /usr/bin/true
%global _default_patch_fuzz     2
%global build_cflags            %{build_cflags} -std=gnu17

Name:           yazi
Version:        26.9.1
Release:        2%{?dist}
Summary:        Blazing fast terminal file manager

License:        BSD-2-Clause AND (0BSD OR MIT OR Apache-2.0) AND (MIT OR Zlib OR Apache-2.0) AND Unicode-3.0 AND (MIT OR Apache-2.0) AND (BSD-2-Clause OR Apache-2.0 OR MIT) AND (MIT OR Apache-2.0 OR Zlib) AND MIT AND (MIT OR Apache-2.0 OR NCSA) AND (Apache-2.0 OR BSL-1.0) AND (Unlicense OR MIT) AND Apache-2.0 AND (CC0-1.0 OR Apache-2.0) AND BSD-3-Clause AND MPL-2.0 AND ISC AND Zlib AND ((MIT OR Apache-2.0) AND Unicode-3.0) AND (Apache-2.0 WITH LLVM-exception) AND (Apache-2.0 OR MIT) AND CC0-1.0 AND (Apache-2.0 WITH LLVM-exception OR Apache-2.0 OR MIT) AND (Zlib OR Apache-2.0 OR MIT) AND BSL-1.0
SourceLicense:  MIT

URL:            https://github.com/sxyazi/yazi
Source:         %{url}/archive/v%{version}/%{name}-%{version}.tar.gz

BuildRequires:  cargo-rpm-macros >= 25
BuildRequires:  rust >= 1.95.0
BuildRequires:  gcc
BuildRequires:  ImageMagick
BuildRequires:  make
# Provide %%{bash,fish,zsh}_completions_dir macros used in %%install
BuildRequires:  bash-completion
BuildRequires:  fish
BuildRequires:  zsh

Recommends:     7zip
Recommends:     chafa
Recommends:     ImageMagick

%global _description %{expand:
%{summary}.}

%description %{_description}

%package bash-completion
BuildArch:      noarch
Summary:        Bash completion files for %{name}
Provides:       %{name}-bash-completion = %{version}-%{release}

Requires:       bash-completion
Requires:       %{name} = %{version}-%{release}

%description bash-completion
This package installs Bash completion files for %{name}

%package fish-completion
BuildArch:      noarch
Summary:        Fish completion files for %{name}
Provides:       %{name}-fish-completion = %{version}-%{release}

Requires:       fish
Requires:       %{name} = %{version}-%{release}

%description fish-completion
This package installs Fish completion files for %{name}

%package zsh-completion
BuildArch:      noarch
Summary:        Zsh completion files for %{name}
Provides:       %{name}-zsh-completion = %{version}-%{release}

Requires:       zsh
Requires:       %{name} = %{version}-%{release}

%description zsh-completion
This package installs Zsh completion files for %{name}

%prep
%autosetup -n %{name}-%{version} -p1
# COPR needs network access here; keep the versions and git revision in Cargo.lock.
cargo vendor --locked
# Fedora's vendor configuration only replaces crates.io, not git sources.
# Keep upstream's ratatui-core fix, using the copy vendored from the locked commit.
sed -i 's|^ratatui-core = { git = "https://github.com/yazi-rs/ratatui.git", branch = "fix_buffer_diff_wide_cells" }$|ratatui-core = { path = "vendor/ratatui-core" }|' Cargo.toml
grep -Fxq 'ratatui-core = { path = "vendor/ratatui-core" }' Cargo.toml
%cargo_prep -v vendor
# Refresh the git-to-path lock entry only after enabling the vendored sources.
cargo update --offline -p ratatui-core

%build
export YAZI_GEN_COMPLETIONS=1
# Release tarballs have no .git; skip vergen git SHA (sets VERGEN_GIT_SHA=no-gitcl).
export YAZI_NO_GITCL=1
%cargo_build
%{cargo_license_summary}
%{cargo_license} > LICENSE.dependencies
%{cargo_vendor_manifest}
# The manifest generator excludes path dependencies; include the patched crate.
printf '%s\n' 'ratatui-core v0.1.2' >> cargo-vendor.txt

%install
# Non-crate workspace: Fedora Rust guidelines say not to use %%cargo_install;
# copy binaries from the rpm profile used by %%cargo_build.
install -Dpm755 target/rpm/ya %{buildroot}%{_bindir}/ya
install -Dpm755 target/rpm/%{name} %{buildroot}%{_bindir}/%{name}

install -Dpm644 yazi-boot/completions/%{name}.bash %{buildroot}%{bash_completions_dir}/%{name}
install -Dpm644 yazi-boot/completions/%{name}.fish %{buildroot}%{fish_completions_dir}/%{name}.fish
install -Dpm644 yazi-boot/completions/_%{name} %{buildroot}%{zsh_completions_dir}/_%{name}

install -Dpm644 assets/%{name}.desktop %{buildroot}%{_datadir}/applications/%{name}.desktop

for size in {1024,512,256,128,64,32,16}; do
    mkdir -p %{buildroot}%{_datadir}/icons/hicolor/"$size"x"$size"/apps
    magick assets/logo.png -resize "$size"x"$size"\! %{buildroot}%{_datadir}/icons/hicolor/"$size"x"$size"/apps/%{name}.png
done

%if %{with check}
%check
%cargo_test
%endif

%files
%license cargo-vendor.txt
%license LICENSE
%license LICENSE-ICONS
%license LICENSE.dependencies
%doc CODE_OF_CONDUCT.md
%doc CONTRIBUTING.md
%doc README.md
%{_bindir}/ya
%{_bindir}/%{name}
%{_datadir}/applications/%{name}.desktop
%{_datadir}/icons/hicolor/*/apps/%{name}.png

%files bash-completion
%{bash_completions_dir}/%{name}

%files fish-completion
%{fish_completions_dir}/%{name}.fish

%files zsh-completion
%{zsh_completions_dir}/_%{name}

%changelog
* Tue Sep 08 2026 vitrasti <vitrasti@protonmail.com> - 26.9.1-2
- Vendor locked dependencies and resolve the ratatui-core path patch offline
- Keep prep offline without the failing optional-config loop
- Include the patched ratatui-core in bundled dependency metadata

* Mon Sep 07 2026 vitrasti <vitrasti@protonmail.com> - 26.9.1-1
- Update to 26.9.1
- Use vendored path patch for git ratatui-core; install from target/rpm

* Sun Aug 16 2026 vitrasti <vitrasti@protonmail.com> - 26.8.15-1
- Update to 26.8.15
- Set YAZI_NO_GITCL for tarball builds (new yazi-version/vergen)

* Sun Aug 09 2026 vitrasti <vitrasti@protonmail.com> - 26.5.6-1
- Initial release for personal copr repo.
