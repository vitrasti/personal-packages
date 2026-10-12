# Personal COPR package. Version is bumped by hand.
# Upstream GitHub tag is v plus the package version.

Name:           hermes-agent
Version:        0.21.7
Release:        1%{?dist}
Summary:        The self-improving AI agent — creates skills from experience, improves them during use, and runs anywhere

License:        MIT
URL:            https://github.com/NousResearch/hermes-agent
Source0:        %{url}/archive/refs/tags/v%{version}.tar.gz#/%{name}-%{version}.tar.gz
Source1:        hermes.sh
# Relax exact PyPI pins so Fedora can satisfy %%pyproject_buildrequires.
# Drop core deps that are not in Fedora.
Patch0:         relax-deps.patch
# Teach upstream's install-method detector about RPM/ostree and refuse
# in-place `hermes update` / `hermes uninstall`.
Patch1:         managed-update.patch
# Always include this patch in the SRPM; COPR creates the SRPM without a
# Fedora-specific macro before building it in individual chroots.
Patch2:         python315-compat.patch
# Make the RPM-built Electron artifact use external package updates.
Patch3:         rpm-desktop-update.patch

ExclusiveArch:  x86_64
BuildRequires:  python3-devel
BuildRequires:  python3dist(wheel)
%if 0%{?fedora} >= 44
BuildRequires:  nodejs22-bin >= 1:22.22.0
BuildRequires:  nodejs22-npm-bin
# Full ICU data is only a weak dep; without it Intl.Segmenter segfaults
# (Rolldown calls it) in mock, which skips weak deps.
BuildRequires:  nodejs22-full-i18n
# Upstream accepts npm <11.10.0 or >=11.17.0; Fedora's Node 22 uses npm 10.
# nodejs22-npm epoch was bumped 1 -> 2 on F45; keep the guard per epoch.
%if 0%{?fedora} >= 45
BuildRequires:  nodejs22-npm < 2:11.10.0
%else
BuildRequires:  nodejs22-npm < 1:11.10.0
%endif
%else
# F43 ships Node 22 as the mainline nodejs package.
BuildRequires:  nodejs >= 1:22.22.0
BuildRequires:  nodejs-npm
BuildRequires:  nodejs-full-i18n
%endif
BuildRequires:  gcc-c++
BuildRequires:  make
BuildRequires:  libX11-devel
BuildRequires:  libXi-devel

# The Electron runtime is prebuilt and retains native libraries inside its
# private tree; do not split its symbols into a separate debuginfo RPM.
%global debug_package %{nil}

# Skill helper scripts may have Node shebangs. Node is optional at runtime.
%global __brp_mangle_shebangs_exclude_from %{_datadir}/hermes-agent/.*
%global __requires_exclude %{?__requires_exclude:%{__requires_exclude}|}^/usr/bin/node$

# Core pyproject.toml dependencies. Versions are unpinned so Fedora's
# python3dist packages can satisfy them. Automatic Requires generation
# cannot see .dist-info because the payload is installed outside sitelib.
Requires:       python3dist(openai)
Requires:       python3dist(certifi)
Requires:       python3dist(truststore)
Requires:       python3dist(python-dotenv)
Requires:       python3dist(fire)
Requires:       python3dist(httpx)
# httpx[socks] extra; Fedora's python3-httpx does not Provide the extra.
Requires:       python3dist(socksio)
Requires:       python3dist(rich)
Requires:       python3dist(tenacity)
Requires:       python3dist(tomli-w)
Requires:       python3dist(ruamel-yaml)
Requires:       python3dist(requests)
Requires:       python3dist(jinja2)
Requires:       python3dist(pydantic)
Requires:       python3dist(prompt-toolkit)
Requires:       python3dist(croniter)
Requires:       python3dist(snowballstemmer)
Requires:       python3dist(packaging)
Requires:       python3dist(markdown)
Requires:       python3dist(pyjwt)
Requires:       python3dist(cryptography)
Requires:       python3dist(urllib3)
Requires:       python3dist(psutil)
Requires:       python3dist(websockets)
Requires:       python3dist(pathspec)
Requires:       python3dist(fastapi)
Requires:       python3dist(uvicorn)
Requires:       python3dist(httptools)
Requires:       python3dist(watchfiles)
Requires:       python3dist(python-multipart)
Requires:       python3dist(ptyprocess)
Requires:       python3dist(pillow)

# Optional extras. Suggests (not Recommends): rpm-ostree installs weak
# deps by default; Electron already ships Chromium in the RPM.
Suggests:       nodejs
Suggests:       ripgrep
Suggests:       ffmpeg-free
Suggests:       chromium

%description
The self-improving AI agent built by Nous Research. It creates skills from
experience, improves them during use, and can run on a laptop, VPS, or an
immutable Fedora CoreOS / Kinoite / bootc image.

This RPM installs the agent under %{_datadir}/hermes-agent (upstream is not
src-layout and would pollute system site-packages with top-level modules).
Runtime state lives in $HERMES_HOME (default ~/.hermes). Lazy PyPI installs
are disabled so the package does not write under /usr at runtime.
`hermes update` / `hermes uninstall` are refused; upgrade via rpm-ostree or
a bootc image rebuild.
The x86_64 package also contains a prebuilt Electron desktop app. Run
`hermes desktop` or `hermes gui` to launch it with this RPM's agent backend.

%prep
%autosetup -N -p1 -n hermes-agent-%{version}
%autopatch -p1 -m 0 -M 1
# Fedora 45+ defaults to Python 3.15; its packaged dependencies use 3.15.
%if 0%{?fedora} >= 45
%patch -P 2 -p1
%endif
%patch -P 3 -p1

%generate_buildrequires
%pyproject_buildrequires

%build
export HERMES_RPM_BUILD=1
%pyproject_wheel
# COPR networking is enabled for this personal project. Lockfile-controlled
# downloads, native bindings and Electron packaging happen only in the build.
node --version
npm --version
npm ci
node apps/desktop/scripts/stage-native-deps.mjs --source "$PWD" --out "$PWD/apps/desktop/build/native-deps"
export HERMES_PAYLOAD_VERSION=%{version}
npm run build --workspace apps/desktop
npm run builder --workspace apps/desktop -- --native-deps "$PWD/apps/desktop/build/native-deps" --linux --x64 --dir
test -x apps/desktop/release/linux-unpacked/Hermes
test -f apps/desktop/release/linux-unpacked/resources/app.asar

%install
export HERMES_RPM_BUILD=1
%pyproject_install

install -d -m0755 %{buildroot}%{_libexecdir}/hermes-agent/desktop
cp -a apps/desktop/release/linux-unpacked/. %{buildroot}%{_libexecdir}/hermes-agent/desktop/
# Chromium requires a root-owned setuid helper when unprivileged user
# namespaces are disabled. RPM installs the buildroot payload as root.
chmod 4755 %{buildroot}%{_libexecdir}/hermes-agent/desktop/chrome-sandbox

# Keep the setuptools entry point, and put the RPM wrapper on /usr/bin/hermes.
mv %{buildroot}%{_bindir}/hermes %{buildroot}%{_bindir}/hermes-cli
install -Dpm0755 %{SOURCE1} %{buildroot}%{_bindir}/hermes

# Private payload dir: upstream ships top-level modules (cli.py, utils.py)
# that must not land in %%{python3_sitelib}.
install -d -m0755 %{buildroot}%{_datadir}/hermes-agent
find %{buildroot}%{python3_sitelib} -mindepth 1 -maxdepth 1 \
    -exec mv {} %{buildroot}%{_datadir}/hermes-agent/ \;

# Bundled skills / optional assets / locales are data, not importable packages.
cp -a skills optional-skills %{buildroot}%{_datadir}/hermes-agent/
if [ -d optional-mcps ]; then
    cp -a optional-mcps %{buildroot}%{_datadir}/hermes-agent/
fi
if [ -d locales ]; then
    cp -a locales %{buildroot}%{_datadir}/hermes-agent/
fi

# Upstream install-method stamp (next to the code tree, not $HERMES_HOME).
printf 'rpm\n' > %{buildroot}%{_datadir}/hermes-agent/.install_method

# Keep imports working for hermes-cli / hermes-acp / hermes-agent.
install -d -m0755 %{buildroot}%{python3_sitelib}
printf '%s\n' '%{_datadir}/hermes-agent' \
    > %{buildroot}%{python3_sitelib}/hermes-agent.pth

# Byte-compile modules outside sitelib (Python packaging guidelines).
%py_byte_compile %{python3} %{buildroot}%{_datadir}/hermes-agent/

%check
export PYTHONPATH=%{buildroot}%{_datadir}/hermes-agent
export HERMES_DISABLE_LAZY_INSTALLS=1
export PYTHONDONTWRITEBYTECODE=1
export HERMES_BUNDLED_SKILLS=%{buildroot}%{_datadir}/hermes-agent/skills
export HERMES_OPTIONAL_SKILLS=%{buildroot}%{_datadir}/hermes-agent/optional-skills
%{buildroot}%{_bindir}/hermes-cli --help >/dev/null
%{buildroot}%{_bindir}/hermes-cli update 2>&1 | grep -E "managed by RPM|rpm-ostree|bootc"

%files
%doc README.md
%license LICENSE
%{_bindir}/hermes
%{_bindir}/hermes-cli
%{_bindir}/hermes-acp
%{_bindir}/hermes-agent
%{python3_sitelib}/hermes-agent.pth
%{_datadir}/hermes-agent/
%{_libexecdir}/hermes-agent/desktop/

%changelog
* Mon Oct 12 2026 vitrasti <vitrasti@protonmail.com> - 0.21.7-1
- Update to 0.21.7
- Refresh relax-deps.patch: upstream nemo-relay pin moved to 0.10

* Mon Oct 12 2026 vitrasti <vitrasti@protonmail.com> - 0.21.6-7
- Fix nodejs22-npm BuildRequires epoch for Fedora 45 and rawhide (npm epoch 2)

* Mon Oct 12 2026 vitrasti <vitrasti@protonmail.com> - 0.21.6-6
- BuildRequire full Node ICU data; Intl.Segmenter crashed Vite without it
- Drop the desktop build memory tweaks; memory was not the cause

* Mon Oct 12 2026 vitrasti <vitrasti@protonmail.com> - 0.21.6-5
- Use mainline nodejs and nodejs-npm on Fedora 43
- Reduce desktop renderer build memory for 2 GiB COPR builders

* Sun Oct 11 2026 vitrasti <vitrasti@protonmail.com> - 0.21.6-4
- Build and ship the x86_64 Electron desktop app with the RPM backend

* Sun Oct 11 2026 vitrasti <vitrasti@protonmail.com> - 0.21.6-3
- Allow Python 3.15 when building on Fedora 45 and newer

* Sun Oct 11 2026 vitrasti <vitrasti@protonmail.com> - 0.21.6-2
- Keep the dependency array closed after removing nemo-relay

* Sun Oct 11 2026 vitrasti <vitrasti@protonmail.com> - 0.21.6-1
- Update to 0.21.6
- Refresh relax-deps.patch for upstream dependency markers
- Refresh managed-update.patch for the uninstall command

* Wed Sep 30 2026 vitrasti <vitrasti@protonmail.com> - 0.21.5-1
- Update to 0.21.5

* Wed Sep 23 2026 vitrasti <vitrasti@protonmail.com> - 0.21.4-1
- Initial release for personal copr repo.
