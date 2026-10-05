# Personal COPR package; buildroot network access must be enabled.
# Install the published npm application and native prebuilds at build time.
# Application/pnpm versions are pinned; transitive ranges resolve during build.
%global upstream_version 0.2.0-rc.2
%global pnpm_version 11.7.0
%global debug_package %{nil}
%global __strip /bin/true
# Preserve upstream helper/skill shebangs; these are private application assets.
%global __brp_mangle_shebangs_exclude_from %{_libdir}/deepseek-harness/.*
# Private bundled libraries must not become public RPM library Provides.
%global __provides_exclude_from ^%{_libdir}/deepseek-harness/.*$
# These sonames are supplied privately alongside the native modules.
%global __requires_exclude ^(libonnxruntime[.]so|libsherpa-onnx-c-api[.]so|libvips-cpp[.]so[.]8[.]18[.]7)[(].*$

Name:           deepseek-harness
Version:        0.2.0~rc.2
Release:        1%{?dist}
Summary:        Plugin-based AI agent harness with a Web UI and automation profiles

# First-party MIT plus bundled runtime dependencies; retain their license files.
License:        MIT AND Apache-2.0 AND ISC AND BSD-2-Clause AND BSD-3-Clause AND BlueOak-1.0.0 AND MPL-2.0 AND LGPL-3.0-or-later AND 0BSD AND Unlicense AND Python-2.0
URL:            https://github.com/deepseek-ai/deepseek-harness
Source0:        %{url}/raw/dsh-v%{upstream_version}/LICENSE#/%{name}-%{upstream_version}-LICENSE
Source1:        %{url}/raw/dsh-v%{upstream_version}/THIRD_PARTY_NOTICES.md#/%{name}-%{upstream_version}-THIRD_PARTY_NOTICES.md
Source2:        %{url}/raw/dsh-v%{upstream_version}/README.md#/%{name}-%{upstream_version}-README.md

ExclusiveArch:  x86_64
BuildRequires:  nodejs >= 1:22.19.0
BuildRequires:  npm
BuildRequires:  python3
BuildRequires:  patchelf
Requires:       nodejs >= 1:22.19.0
Requires:       bash
# Suggestions do not pull optional desktop tools into Fedora CoreOS images.
Suggests:       git
Suggests:       xdg-utils
Suggests:       python3

%description
DeepSeek Harness (dsh) is an open-source agent harness developed by DeepSeek AI.
It provides a Web UI, headless execution, SDK and ACP profiles, and a
plugin-based architecture powered by Cordis.

This package installs the published npm application and its dependencies
under %{_libdir}/deepseek-harness, using Fedora's Node.js. A private pnpm runtime
supports user plugin installation without a separate global npm installation.

Designed for Fedora CoreOS, rpm-ostree and bootc: application files live in /usr,
and all Harness state and plugins live in $DSH_HOME (default ~/.dsh). Start with
"dsh web --no-open" and connect to the printed URL. Upgrade through the package
manager or rebuild the OS image.

%prep
%setup -q -c -T -n %{name}-%{upstream_version}
cp -p %{SOURCE0} LICENSE
cp -p %{SOURCE1} THIRD_PARTY_NOTICES.md
cp -p %{SOURCE2} README.md

cat > package.json <<'EOF'
{
  "name": "deepseek-harness-rpm",
  "version": "%{upstream_version}",
  "private": true,
  "type": "module",
  "dependencies": {
    "@deepseek-ai/dsh": "%{upstream_version}",
    "pnpm": "%{pnpm_version}"
  }
}
EOF

cat > dsh.mjs <<'EOF'
#!/usr/bin/node
import { fileURLToPath } from 'node:url';
import { runCli } from '@deepseek-ai/dsh/lib/bin.js';
await runCli({
  packageManager: {
    command: process.execPath,
    args: [fileURLToPath(new URL('./node_modules/pnpm/bin/pnpm.mjs', import.meta.url))],
    env: {},
  },
});
EOF

%build
# COPR downloads dependencies here, never when installing/running the RPM.
# Skip arbitrary lifecycle scripts: all native modules have published prebuilds.
export npm_config_cache="$PWD/.npm-cache"
npm install --ignore-scripts --omit=dev --no-audit --no-fund
%{python3} - <<'PY'
import json
from pathlib import Path
import shutil

modules = Path('node_modules')
# Fedora CoreOS is glibc/x86_64; exclude musl and foreign native payloads.
for name in (
    '@img/sharp-linuxmusl-x64', '@img/sharp-libvips-linuxmusl-x64',
    'node-addon-require-builtin-linux-x64-musl',
    '@deepseek-ai/node-addon-system-linux-x64/bin/musl',
    '@koromix/koffi-linux-x64/musl_x64',
    'node-pty/third_party/conpty', 'pnpm/dist/vendor',
):
    shutil.rmtree(modules / name, ignore_errors=True)
for path in (modules / 'node-pty/prebuilds').iterdir():
    if path.name != 'linux-x64':
        shutil.rmtree(path)
for path in (modules / 'pnpm/dist/node_modules/@reflink').iterdir():
    if 'linux-x64' not in path.name:
        shutil.rmtree(path)
# Retain package licenses and disclose the actual resolved dependency set.
inventory = []
for path in sorted(modules.rglob('package.json')):
    package = json.loads(path.read_text())
    if package.get('name') and package.get('version'):
        inventory.append({
            'name': package['name'], 'version': package['version'],
            'license': package.get('license', 'see containing package license'),
            'path': str(path.parent),
        })
Path('BUNDLED-PACKAGES.json').write_text(json.dumps(inventory, indent=2) + '\n')
(modules / '.package-lock.json').unlink(missing_ok=True)
PY
# Reproduce the one necessary postinstall: restore helper executable bits.
node node_modules/@deepseek-ai/dsh-subprocess-local/scripts/ensure-spawn-helper.mjs

%install
install -dm0755 %{buildroot}%{_libdir}/deepseek-harness %{buildroot}%{_bindir}
cp -a --no-preserve=ownership node_modules package.json package-lock.json \
    dsh.mjs BUNDLED-PACKAGES.json %{buildroot}%{_libdir}/deepseek-harness/
chmod 0755 %{buildroot}%{_libdir}/deepseek-harness/dsh.mjs
# Upstream's voice addon retains its CI build path and an empty RUNPATH.
# Only its colocated libraries should be searched, never the working directory.
patchelf --set-rpath '$ORIGIN' \
    %{buildroot}%{_libdir}/deepseek-harness/node_modules/sherpa-onnx-linux-x64/sherpa-onnx.node
ln -s ../%{_lib}/deepseek-harness/dsh.mjs %{buildroot}%{_bindir}/dsh

%check
%{python3} - %{buildroot}%{_bindir}/dsh <<'PY'
from http.cookiejar import CookieJar
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
import urllib.request
from urllib.parse import urljoin

launcher = str(Path(sys.argv[1]).resolve())
with tempfile.TemporaryDirectory(prefix='dsh-check-') as temp:
    env = dict(os.environ, HOME=temp, DSH_HOME=f'{temp}/.dsh',
               XDG_CACHE_HOME=f'{temp}/cache', DSH_TELEMETRY_DISABLED='1')
    def run(*args):
        return subprocess.check_output([launcher, *args], cwd=temp, env=env,
                                       text=True, timeout=60)
    assert run('--version').strip() == '%{upstream_version}'
    assert 'Usage: dsh' in run('--help')
    assert run('plugin', '--profile', 'web', '--version').strip() == '%{pnpm_version}'
    assert 'tool-fs-search' in run('web', '--dump-default-config')
    bundle = Path(temp) / 'test-bundle'
    bundle.mkdir()
    (bundle / 'package.json').write_text(json.dumps({
        'name': 'dsh-rpm-smoke-bundle', 'version': '1.0.0',
        'dsh': {'bundle': {'patch': './cordis.patch.yml'}},
    }))
    (bundle / 'cordis.patch.yml').write_text('[]\n')
    run('plugin', '--profile', 'web', 'add', str(bundle), '--offline', '--ignore-scripts')
    profile = Path(env['DSH_HOME']) / 'profiles/web/package.json'
    assert 'dsh-rpm-smoke-bundle' in json.loads(profile.read_text())['dsh']['profile']['bundles']
    run('plugin', '--profile', 'web', 'remove', 'dsh-rpm-smoke-bundle', '--config.offline=true')
    assert 'dsh-rpm-smoke-bundle' not in json.loads(profile.read_text())['dsh']['profile']['bundles']
    native = """
        const { createRequire } = await import('node:module');
        const require = createRequire(process.argv[1]);
        await require('sharp')({create: {width: 1, height: 1, channels: 3,
            background: 'white'}}).png().toBuffer();
        require('koffi').load('libc.so.6').func('int getpid()')();
        require('node-addon-require-builtin');
        require('sherpa-onnx-node');
        const pty = require('node-pty').spawn('/usr/bin/bash', ['-c', 'exit 0']);
        await new Promise((resolve, reject) => {
            pty.onExit(({exitCode}) => exitCode === 0 ? resolve() : reject(exitCode));
        });
        require('node:child_process').execFileSync(require('@vscode/ripgrep').rgPath, ['--version']);
    """
    subprocess.run(['node', '--input-type=module', '-e', native, launcher],
                   cwd=temp, env=env, check=True, timeout=60)
    log = Path(temp) / 'web.log'
    with log.open('w') as output:
        process = subprocess.Popen([launcher, 'web', '--no-open', '--port', '0'],
                                   cwd=temp, env=env, stdout=output, stderr=subprocess.STDOUT)
        try:
            deadline = time.monotonic() + 60
            while time.monotonic() < deadline:
                text = log.read_text()
                match = re.search(r'dsh web: (http://127[.]0[.]0[.]1:\d+/\?token=\S+)', text)
                if match:
                    break
                if process.poll() is not None:
                    raise RuntimeError(text)
                time.sleep(0.1)
            else:
                raise RuntimeError(f'Web startup timed out:\n{text}')
            url = match[1]
            opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(CookieJar()))
            with opener.open(url, timeout=10) as response:
                html = response.read().decode()
                assert response.status == 200 and '<html' in html
            asset = re.search(r'(?:src|href)="([^"]+[.](?:js|css))"', html)
            assert asset
            with opener.open(urljoin(url, asset[1]), timeout=10) as response:
                assert response.status == 200 and response.read()
            print('Passed: version, help, plugin add/remove, native modules, Web UI/assets')
        finally:
            process.terminate()
            try:
                process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
PY

%files
%license LICENSE THIRD_PARTY_NOTICES.md
%doc README.md
%{_bindir}/dsh
%{_libdir}/deepseek-harness/

%changelog
* Mon Oct 05 2026 vitrasti <vitrasti@protonmail.com> - 0.2.0~rc.2-1
- Initial package for personal COPR, targeting x86_64 Fedora CoreOS
- Install the published npm release and private pnpm during network-enabled builds
- Keep user profiles, plugins and runtime state outside the immutable payload
