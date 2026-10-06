# Hugging Face CLI for Fedora / Fedora CoreOS

This x86_64 RPM provides `hf` from `huggingface-hub` 2.1.1. It targets Fedora 44,
Fedora 43 and Rawhide, using each release's system Python. Application dependencies
are hash-pinned in `requirements.txt` and installed privately under
`/usr/lib64/huggingface-cli/site-packages`. They do not provide or replace system
Python libraries. The native `hf-xet` wheel uses CPython's stable ABI; PyYAML is
built without its optional C extension to avoid a release-specific Python ABI.

## COPR setup

Use this Git repository as an SCM source, with subdirectory `huggingface-cli`,
spec `huggingface-cli.spec`, and the `rpkg` source-build method. Enable
**buildroot network access**: the binary build downloads pinned PyPI artifacts
and checks their SHA-256 hashes. Enable the `fedora-44-x86_64`,
`fedora-43-x86_64`, and `fedora-rawhide-x86_64` chroots.

The RPM build requires no companion COPR dependency packages. Python's pip,
setuptools and wheel are build-time requirements only. All dependencies retain
their upstream license files; `BUNDLED-PACKAGES.json` records installed versions
and license metadata, and hf-xet retains its upstream SBOM.

## Installation and use

After enabling the COPR repository, use:

```sh
# Fedora
sudo dnf install huggingface-cli

# An rpm-ostree system with package layering enabled
sudo rpm-ostree install huggingface-cli
sudo systemctl reboot

hf version
hf auth login
hf download org/model --local-dir ./model
```

For image-based Fedora CoreOS / bootc deployments, add the COPR repository and
install `huggingface-cli` during the OS image build, then deploy the image through
your normal OS update workflow. There are no install-time downloads, services,
or dependency installations on first launch.

`hf update` directs users to RPM/OS updates instead of invoking pip or an upstream
installer. The launcher uses Python's isolated/no-site mode, ignores `PYTHONPATH`
and user site-packages, and never writes bytecode into `/usr`. Update-check
notifications are disabled by default (`HF_HUB_DISABLE_UPDATE_CHECK=0` opts in).
Normal network access to the Hugging Face Hub is unaffected.

Credentials and caches use upstream defaults under `~/.cache/huggingface`
(or `$HF_HOME` / `$XDG_CACHE_HOME`). Downloads, skills and extensions live in
user-writable paths. Optional Python extensions may need separately installed
`uv` to provision their own environments; the base CLI needs neither pip nor uv.
Bash, Zsh and Fish completions are installed system-wide.

Fedora's `python3-huggingface-hub` also owns `/usr/bin/hf`, so this RPM conflicts
with that package. It does not expose an importable system `huggingface_hub`
library or the optional `tiny-agents` helper.

## Updating the package

Update the version in the spec, then resolve the desired upstream version and
PyYAML pin on Linux x86_64 / Python 3.13 (the minimum supported Python):

```sh
uv pip compile - --python-version 3.13 \
  --python-platform x86_64-manylinux_2_28 --generate-hashes \
  --no-annotate --no-header --output-file requirements.txt <<'EOF'
huggingface-hub==2.1.1
pyyaml==6.0.3
EOF
```

Retain only the x86_64 stable-ABI manylinux hash for hf-xet and the source archive
hash for PyYAML; leave hashes for the pure-Python wheels. Review licenses and the
update patch, then rebuild on all three chroots. Dependencies are only upgraded
when this lock file is deliberately changed.

`%check` runs offline CLI smoke checks, a cached-file download, native imports,
dependency-metadata validation, shell-completion checks, and tests that user
Python paths cannot override private dependencies. It also verifies that
`hf update` exits before accessing PyPI. Rawhide support depends on continued
compatibility of the pinned packages with its system Python.

### Verified builds

Local Fedora-container RPM builds and installed-payload smoke checks passed for:

| Target | Build tag | System Python |
| --- | --- | --- |
| Fedora 44 x86_64 | fc44 | 3.14.7 |
| Fedora 43 x86_64 | fc43 | 3.14.7 |
| Rawhide x86_64 | fc46 | 3.15.0rc3 |

All three passed the same checks as a non-root user with a read-only container
filesystem, writable temporary home and no network. These verify immutable
payload behavior; a Fedora CoreOS VM deployment was not tested.

## Packaging references

- [Fedora's Hugging Face Hub package](https://packages.fedoraproject.org/pkgs/python-huggingface-hub/python3-huggingface-hub/)
- [Upstream CLI documentation](https://huggingface.co/docs/huggingface_hub/guides/cli)
