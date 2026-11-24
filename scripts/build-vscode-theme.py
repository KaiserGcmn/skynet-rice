#!/usr/bin/env python3
"""Pack sources/vscode-amoled-theme into a .vsix for `code --install-extension`.

The package is built with the standard library only and is reproducible: fixed
timestamps, sorted entries. Output: .build/vscode-amoled/<name>-<version>.vsix
"""
import argparse
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'sources/vscode-amoled-theme'
FIXED_TIME = (2026, 11, 23, 0, 0, 0)

CONTENT_TYPES = (
    '<?xml version="1.0" encoding="utf-8"?>\n'
    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    '<Default Extension=".json" ContentType="application/json"/>'
    '<Default Extension=".md" ContentType="text/markdown"/>'
    '<Default Extension=".vsixmanifest" ContentType="text/xml"/>'
    '</Types>\n')

MANIFEST = '''<?xml version="1.0" encoding="utf-8"?>
<PackageManifest Version="2.0.0" xmlns="http://schemas.microsoft.com/developer/vsx-schema/2011" xmlns:d="http://schemas.microsoft.com/developer/vsx-schema-design/2011">
  <Metadata>
    <Identity Language="en-US" Id="{name}" Version="{version}" Publisher="{publisher}"/>
    <DisplayName>{display}</DisplayName>
    <Description xml:space="preserve">{description}</Description>
    <Tags>theme,amoled,black,dark</Tags>
    <Categories>Themes</Categories>
    <GalleryFlags>Public</GalleryFlags>
    <Properties>
      <Property Id="Microsoft.VisualStudio.Code.Engine" Value="{engine}"/>
      <Property Id="Microsoft.VisualStudio.Code.ExtensionDependencies" Value=""/>
      <Property Id="Microsoft.VisualStudio.Code.ExtensionPack" Value=""/>
      <Property Id="Microsoft.VisualStudio.Code.ExtensionKind" Value="ui,workspace"/>
      <Property Id="Microsoft.VisualStudio.Code.LocalizedLanguages" Value=""/>
    </Properties>
  </Metadata>
  <Installation>
    <InstallationTarget Id="Microsoft.VisualStudio.Code"/>
  </Installation>
  <Dependencies/>
  <Assets>
    <Asset Type="Microsoft.VisualStudio.Code.Manifest" Path="extension/package.json" Addressable="true"/>
    <Asset Type="Microsoft.VisualStudio.Services.Content.Details" Path="extension/NOTICE.md" Addressable="true"/>
  </Assets>
</PackageManifest>
'''


def escape(text):
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def build(output_dir):
    package = json.loads((SOURCE / 'package.json').read_text(encoding='utf-8'))
    files = ['package.json', 'NOTICE.md'] + sorted(
        str(path.relative_to(SOURCE)) for path in (SOURCE / 'themes').glob('*.json'))
    manifest = MANIFEST.format(
        name=package['name'], version=package['version'], publisher=package['publisher'],
        display=escape(package['displayName']), description=escape(package['description']),
        engine=escape(package['engines']['vscode']))
    output_dir.mkdir(parents=True, exist_ok=True)
    target = output_dir / f"{package['name']}-{package['version']}.vsix"
    entries = [('[Content_Types].xml', CONTENT_TYPES.encode()),
               ('extension.vsixmanifest', manifest.encode())]
    entries += [(f'extension/{name}', (SOURCE / name).read_bytes()) for name in files]
    with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as archive:
        for name, data in entries:
            info = zipfile.ZipInfo(name, FIXED_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, data)
    return target


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--output-dir', type=Path, default=ROOT / '.build/vscode-amoled')
    print(build(parser.parse_args().output_dir))


if __name__ == '__main__':
    main()
