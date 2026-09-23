# Personal COPR package. Version is bumped by hand.
# Upstream GitHub tag is v2026.9.21 (pyproject version 0.21.4).
%global tag_version 2026.9.21

Name:           hermes-agent
Version:        0.21.4
Release:        1%{?dist}
Summary:        The self-improving AI agent — creates skills from experience, improves them during use, and runs anywhere

License:        MIT
URL:            https://github.com/NousResearch/hermes-agent
Source0:        %{url}/archive/refs/tags/v%{tag_version}.tar.gz#/%{name}-%{version}.tar.gz
Source1:        hermes.sh
# Relax exact PyPI pins and requires-python so Fedora 44 (Python 3.14) can
# satisfy %%pyproject_buildrequires. Drop core deps that are not in Fedora.
Patch0:         relax-deps.patch
# Teach upstream's install-method detector about RPM/ostree and refuse
# in-place `hermes update` / `hermes uninstall`.
Patch1:         managed-update.patch

BuildArch:      noarch
BuildRequires:  python3-devel
BuildRequires:  python3dist(wheel)

# Skill helper scripts may have Node shebangs. Node is optional
# (Suggests: nodejs); do not hard-require it on Fedora CoreOS.
%global __brp_mangle_shebangs_exclude_from %{_datadir}/hermes-agent/.*
%global __requires_exclude %{?__requires_exclude:%{__requires_exclude}|}^/usr/bin/node$

# Core pyproject.toml dependencies. Versions are unpinned so Fedora's
# python3dist packages can satisfy them. Automatic Requires generation
# cannot see .dist-info because the payload is installed outside sitelib.
Requires:       python3dist(openai)
Requires:       python3dist(certifi)
Requires:       python3dist(python-dotenv)
Requires:       python3dist(fire)
Requires:       python3dist(httpx)
# httpx[socks] extra; Fedora's python3-httpx does not Provide the extra.
Requires:       python3dist(socksio)
Requires:       python3dist(rich)
Requires:       python3dist(tenacity)
Requires:       python3dist(pyyaml)
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
# deps by default, and Chromium/Node do not belong on Fedora CoreOS.
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

%prep
%autosetup -p1 -n hermes-agent-%{tag_version}

%generate_buildrequires
%pyproject_buildrequires

%build
export HERMES_RPM_BUILD=1
%pyproject_wheel

%install
export HERMES_RPM_BUILD=1
%pyproject_install

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

%changelog
* Wed Sep 23 2026 vitrasti <vitrasti@protonmail.com> - 0.21.4-1
- Initial release for personal copr repo.
