# Personal COPR package; enable buildroot network access for hash-checked PyPI downloads.
# Private dependencies avoid replacing Fedora's system Python libraries.
%global appdir %{_libdir}/huggingface-cli
%global debug_package %{nil}
# Preserve the published hf-xet binary and its upstream license/SBOM.
%global __strip /bin/true
%global __provides_exclude_from ^%{appdir}/.*$
# dist-info is private: do not generate system python3dist Requires/Provides.
%global __requires_exclude_from ^%{appdir}/.*[.]dist-info/.*$
# The launcher deliberately uses Python's isolated/no-site/no-bytecode flags.
%global __brp_mangle_shebangs_exclude_from ^%{appdir}/hf[.]py$

Name:           huggingface-cli
Version:        2.1.1
Release:        1%{?dist}
Summary:        Hugging Face Hub CLI with private Python dependencies
# First-party license and bundled Python dependencies. Native hf-xet ships an SBOM.
License:        Apache-2.0 AND Apache-2.0 WITH LLVM-exception AND MIT AND BSD-2-Clause AND BSD-3-Clause AND PSF-2.0 AND MPL-2.0 AND ISC AND Unicode-3.0 AND Zlib
URL:            https://github.com/huggingface/huggingface_hub
Source0:        requirements.txt
Source1:        hf.py
Source2:        check.py
Source3:        README.md
Patch0:         managed-update.patch

ExclusiveArch:  x86_64
BuildRequires:  python3-devel
BuildRequires:  python3dist(pip)
BuildRequires:  python3dist(setuptools)
BuildRequires:  python3dist(wheel)
BuildRequires:  patch
Requires:       python3 >= 3.13
Requires:       ca-certificates
# Both packages own /usr/bin/hf; this CLI is separate from the system library.
Conflicts:      python3-huggingface-hub
Suggests:       git
# Optional Python extensions can use uv to create their user-owned environments.
Suggests:       uv

%description
The hf command manages authentication, downloads and uploads models and datasets,
and interacts with repositories, Spaces, Jobs and the Hugging Face Hub cache.

Application dependencies are installed privately under %{appdir}, using Fedora's
Python interpreter. Credentials and caches use upstream's user-writable paths.
This package supports Fedora CoreOS, rpm-ostree and bootc: nothing installs into
/usr at runtime, and hf update directs users to the OS package/image workflow.

%prep
%setup -q -c -T
cp -p %{SOURCE0} requirements.txt
cp -p %{SOURCE1} hf.py
cp -p %{SOURCE2} check.py
cp -p %{SOURCE3} README.md

%build
# Build PyYAML's pure-Python implementation so Rawhide needs no CPython-specific
# wheel. No isolated backend downloads: setuptools/wheel come from BuildRequires.
export PYYAML_FORCE_LIBYAML=0
export PIP_DISABLE_PIP_VERSION_CHECK=1
%{python3} -m pip --isolated install --index-url https://pypi.org/simple \
    --require-hashes --only-binary=:all: --no-binary=pyyaml \
    --no-build-isolation --no-compile --ignore-installed \
    --target "$PWD/site-packages" -r requirements.txt
# The published wheel is verified before applying the RPM-managed update policy.
patch -d site-packages -p1 < %{PATCH0}
# Only expose hf; private dependency/helper scripts are not runtime entry points.
rm -rf site-packages/bin
%{python3} - <<'PY'
from importlib.metadata import distributions
import json
from pathlib import Path
import shutil

inventory = []
for dist in sorted(distributions(path=['site-packages']), key=lambda d: d.name.lower()):
    files = [str(f) for f in dist.files or []]
    licenses = [f for f in files if '.dist-info/' in f and
                ('license' in f.lower() or 'licence' in f.lower() or 'notice' in f.lower())]
    if not licenses:
        raise RuntimeError(f'Missing license files for {dist.name}')
    for filename in licenses:
        source = Path('site-packages') / filename
        if source.is_file():
            dest = Path('licenses') / dist.name / filename
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, dest)
    inventory.append({'name': dist.name, 'version': dist.version,
                      'license': dist.metadata.get('License-Expression') or
                                 dist.metadata.get('License'),
                      'license_files': licenses})
Path('BUNDLED-PACKAGES.json').write_text(json.dumps(inventory, indent=2) + '\n')
PY

%install
install -dm0755 %{buildroot}%{appdir} %{buildroot}%{_bindir}
cp -a --no-preserve=ownership site-packages %{buildroot}%{appdir}/
install -pm0755 hf.py %{buildroot}%{appdir}/hf.py
ln -s ../%{_lib}/huggingface-cli/hf.py %{buildroot}%{_bindir}/hf

# Ship shell completion without changing user startup files.
export HF_HUB_OFFLINE=1 HF_HUB_DISABLE_TELEMETRY=1 HF_HUB_DISABLE_UPDATE_CHECK=1
for shell in bash zsh fish; do
    SHELL=/usr/bin/$shell %{buildroot}%{_bindir}/hf --show-completion > hf.$shell
done
install -Dpm0644 hf.bash %{buildroot}%{_datadir}/bash-completion/completions/hf
install -Dpm0644 hf.zsh %{buildroot}%{_datadir}/zsh/site-functions/_hf
install -Dpm0644 hf.fish %{buildroot}%{_datadir}/fish/vendor_completions.d/hf.fish

%check
%{python3} check.py %{buildroot}%{_bindir}/hf %{version}

%files
%license licenses/
%doc README.md BUNDLED-PACKAGES.json requirements.txt
%{_bindir}/hf
%{appdir}/
%dir %{_datadir}/bash-completion
%dir %{_datadir}/bash-completion/completions
%{_datadir}/bash-completion/completions/hf
%dir %{_datadir}/zsh
%dir %{_datadir}/zsh/site-functions
%{_datadir}/zsh/site-functions/_hf
%dir %{_datadir}/fish
%dir %{_datadir}/fish/vendor_completions.d
%{_datadir}/fish/vendor_completions.d/hf.fish

%changelog
* Tue Oct 06 2026 vitrasti <vitrasti@protonmail.com> - 2.1.1-1
- Initial x86_64 package with hash-pinned private dependencies
- Support immutable Fedora installations and RPM-managed updates
