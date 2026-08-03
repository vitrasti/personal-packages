%global debug_package %{nil}

# Keep these in sync with upstream packaging
%global jdkver 25.0.2+10
%global jdkver_url 25.0.2_10
%global jdkmaj 25
%global jfxver 25.0.2

Name:           cryptomator
Version:        1.19.3
Release:        1%{?dist}
Summary:        Multiplatform transparent client-side encryption for cloud storage

License:        GPL-3.0-only
URL:            https://cryptomator.org/

# Application source
Source0:        https://github.com/cryptomator/cryptomator/archive/refs/tags/%{version}.tar.gz#/cryptomator-%{version}.tar.gz

# Build toolchain (bundled, not system JDK)
Source1:        https://github.com/adoptium/temurin%{jdkmaj}-binaries/releases/download/jdk-%{jdkver}/OpenJDK%{jdkmaj}U-jdk_x64_linux_hotspot_%{jdkver_url}.tar.gz
Source2:        https://download2.gluonhq.com/openjfx/%{jfxver}/openjfx-%{jfxver}_linux-x64_bin-jmods.zip

ExclusiveArch:  x86_64

BuildRequires:  maven
BuildRequires:  unzip
BuildRequires:  tar
BuildRequires:  gzip

Requires:       fuse3
Requires:       alsa-lib
Requires:       hicolor-icon-theme
Requires:       libXtst
Requires:       libXrender

Recommends:     libsecret

%description
Cryptomator provides transparent, client-side encryption for your cloud storage.
Files are encrypted before they leave your device (Dropbox, Google Drive,
OneDrive, etc.).

%prep
%setup -q -n cryptomator-%{version}

# Unpack JDK and OpenJFX jmods into the build root (sibling of source)
cd %{_builddir}
tar xfz %{SOURCE1}
mkdir -p openjfx-%{jfxver}-jmods
unzip -j %{SOURCE2} \
  '*/javafx.base.jmod' \
  '*/javafx.controls.jmod' \
  '*/javafx.fxml.jmod' \
  '*/javafx.graphics.jmod' \
  -d openjfx-%{jfxver}-jmods

%build
export JAVA_HOME="%{_builddir}/jdk-%{jdkver}"
JMODS_PATH="%{_builddir}/openjfx-%{jfxver}-jmods"

# JEP 493: older jlink needs explicit JDK jmods on the module path
if ! "$JAVA_HOME/bin/jlink" --help 2>&1 | grep -q "Linking from run-time image enabled"; then
  JMODS_PATH="${JMODS_PATH}:${JAVA_HOME}/jmods"
fi

cd %{_builddir}/cryptomator-%{version}

mvn -B clean package -DskipTests -Plinux

cp LICENSE.txt target/
cp target/cryptomator-*.jar target/mods/

cd target

"$JAVA_HOME/bin/jlink" \
  --output runtime \
  --module-path "$JMODS_PATH" \
  --add-modules java.base,java.desktop,java.instrument,java.logging,java.naming,java.net.http,java.scripting,java.sql,java.xml,javafx.base,javafx.graphics,javafx.controls,javafx.fxml,jdk.crypto.ec,jdk.crypto.cryptoki,jdk.unsupported,jdk.security.auth,jdk.accessibility,jdk.management.jfr,jdk.net,java.compiler \
  --strip-native-commands \
  --no-header-files \
  --no-man-pages \
  --strip-debug \
  --compress=zip-0

"$JAVA_HOME/bin/jpackage" \
  --type app-image \
  --runtime-image runtime \
  --input libs \
  --module-path mods \
  --module org.cryptomator.desktop/org.cryptomator.launcher.Cryptomator \
  --dest . \
  --name cryptomator \
  --vendor "Skymatic GmbH" \
  --copyright "(C) 2016 - 2026 Skymatic GmbH" \
  --java-options "--enable-preview" \
  --java-options "--enable-native-access=javafx.graphics,org.cryptomator.jfuse.linux.amd64,org.cryptomator.jfuse.linux.aarch64,org.purejava.appindicator" \
  --java-options "-Xss5m" \
  --java-options "-Xmx256m" \
  --java-options "-Dfile.encoding=utf-8" \
  --java-options "-Djava.net.useSystemProxies=true" \
  --java-options "-Dcryptomator.adminConfigPath=/etc/cryptomator/config.properties" \
  --java-options "-Dcryptomator.appVersion=%{version}" \
  --java-options "-Dcryptomator.buildNumber=fedora-%{release}" \
  --java-options "-Dcryptomator.disableUpdateCheck=true" \
  --java-options "-Dcryptomator.integrationsLinux.autoStartCmd=cryptomator" \
  --java-options "-Dcryptomator.ipcSocketPath=@{userhome}/.config/Cryptomator/ipc.socket" \
  --java-options "-Dcryptomator.logDir=@{userhome}/.local/share/Cryptomator/logs" \
  --java-options "-Dcryptomator.mountPointsDir=@{userhome}/.local/share/Cryptomator/mnt" \
  --java-options "-Dcryptomator.networking.truststore.p12Path=/etc/cryptomator/certs.p12" \
  --java-options "-Dcryptomator.pluginDir=@{userhome}/.local/share/Cryptomator/plugins" \
  --java-options "-Dcryptomator.p12Path=@{userhome}/.config/Cryptomator/key.p12" \
  --java-options "-Dcryptomator.settingsPath=@{userhome}/.config/Cryptomator/settings.json:~/.Cryptomator/settings.json" \
  --java-options "-Dcryptomator.showTrayIcon=true" \
  --java-options "-Dcryptomator.hub.enableTrustOnFirstUse=true" \
  --app-version "%{version}" \
  --verbose

%install
# Desktop integration (from upstream dist/linux/common)
install -Dm644 dist/linux/common/application-vnd.cryptomator.vault.xml \
  %{buildroot}%{_datadir}/mime/packages/cryptomator-vault.xml
install -Dm644 dist/linux/common/org.cryptomator.Cryptomator.desktop \
  %{buildroot}%{_datadir}/applications/org.cryptomator.Cryptomator.desktop
install -Dm644 dist/linux/common/org.cryptomator.Cryptomator256.png \
  %{buildroot}%{_datadir}/icons/hicolor/256x256/apps/org.cryptomator.Cryptomator.png
install -Dm644 dist/linux/common/org.cryptomator.Cryptomator512.png \
  %{buildroot}%{_datadir}/icons/hicolor/512x512/apps/org.cryptomator.Cryptomator.png
install -Dm644 dist/linux/common/org.cryptomator.Cryptomator.svg \
  %{buildroot}%{_datadir}/icons/hicolor/scalable/apps/org.cryptomator.Cryptomator.svg
install -Dm644 dist/linux/common/org.cryptomator.Cryptomator.tray.svg \
  %{buildroot}%{_datadir}/icons/hicolor/scalable/apps/org.cryptomator.Cryptomator.tray.svg
install -Dm644 dist/linux/common/org.cryptomator.Cryptomator.tray-unlocked.svg \
  %{buildroot}%{_datadir}/icons/hicolor/scalable/apps/org.cryptomator.Cryptomator.tray-unlocked.svg
install -Dm644 dist/linux/common/org.cryptomator.Cryptomator.tray.svg \
  %{buildroot}%{_datadir}/icons/hicolor/symbolic/apps/org.cryptomator.Cryptomator.tray-symbolic.svg
install -Dm644 dist/linux/common/org.cryptomator.Cryptomator.tray-unlocked.svg \
  %{buildroot}%{_datadir}/icons/hicolor/symbolic/apps/org.cryptomator.Cryptomator.tray-unlocked-symbolic.svg

# App image produced by jpackage
install -dm755 %{buildroot}/opt
cp -a target/cryptomator %{buildroot}/opt/

install -Dm644 target/LICENSE.txt %{buildroot}%{_datadir}/licenses/%{name}/LICENSE.txt

install -dm755 %{buildroot}%{_bindir}
ln -s /opt/cryptomator/bin/cryptomator %{buildroot}%{_bindir}/cryptomator

%post
/bin/touch --no-create %{_datadir}/icons/hicolor &>/dev/null || :
gtk-update-icon-cache -f -t %{_datadir}/icons/hicolor &>/dev/null || :
update-desktop-database -q %{_datadir}/applications &>/dev/null || :
update-mime-database %{_datadir}/mime &>/dev/null || :

%postun
/bin/touch --no-create %{_datadir}/icons/hicolor &>/dev/null || :
gtk-update-icon-cache -f -t %{_datadir}/icons/hicolor &>/dev/null || :
update-desktop-database -q %{_datadir}/applications &>/dev/null || :
update-mime-database %{_datadir}/mime &>/dev/null || :

%files
%{_bindir}/cryptomator
/opt/cryptomator/
%{_datadir}/applications/org.cryptomator.Cryptomator.desktop
%{_datadir}/mime/packages/cryptomator-vault.xml
%{_datadir}/icons/hicolor/*/apps/org.cryptomator.Cryptomator*
%{_datadir}/licenses/%{name}/

%changelog
* Mon Aug 03 2026 vitrasti <vitrasti@protonmail.com> - 1.19.3-1
- Native build adapted from CachyOS/AUR cryptomator packaging
