#!/usr/bin/env python3
"""Generate the SKYNET AMOLED Black colour theme from VS Code's "Dark 2026".

Syntax colours (tokenColors, semanticTokenColors) are copied unchanged. Every
grey surface becomes true black (#000000, or a barely lit near-black for
floating widgets), borders become dark warm greys and the blue accents become
the SKYNET red used by the earlier colorCustomizations preset.

    python3 generate-theme.py > themes/skynet-amoled-black-color-theme.json
"""
import argparse
import json
from pathlib import Path
import re
import sys

THEMES = Path('/usr/share/code/resources/app/extensions/theme-defaults/themes')
NAME = 'SKYNET AMOLED Black'

# Dark 2026 surface greys, replaced wherever they occur (exact value match).
SURFACES = {
    '#191a1b': '#000000', '#121314': '#000000', '#181818': '#000000', '#1f1f1f': '#000000',
    '#202122': '#07070A',                                    # menus, quick input, suggest, hover
    '#242526': '#0B0B0E', '#262626': '#0B0B0E',              # raised: checkbox, peek title, quote
    '#2b2b2b': '#2A2127', '#2a2b2c': '#2A2127',              # borders
    '#313233': '#1A0B0F', '#323233': '#1A1A1E', '#2c2d2e': '#16161A', '#313131': '#0A0A0D',
    '#2a2a2a': '#2A2A2E', '#191b1d4d': '#0000004D', '#2e3031': '#50343D',
}

# Curated colours: the earlier red preset with its charcoal surfaces turned black,
# plus the remaining blue accents recoloured. Keys not listed keep Dark 2026's value.
RED = '#C6535C'
OVERRIDES = {
    'window.activeBorder': '#6E3038', 'window.inactiveBorder': '#28282D',
    'focusBorder': '#A84952',
    'titleBar.activeBackground': '#000000', 'titleBar.inactiveBackground': '#000000', 'titleBar.border': '#47262C',
    'activityBar.background': '#000000', 'activityBar.border': '#302128',
    'activityBar.activeBorder': RED, 'activityBar.activeFocusBorder': '#A84952',
    'activityBar.activeBackground': '#1A0B0F',
    'activityBarBadge.background': '#96303B', 'activityBarBadge.foreground': '#F2ECEB',
    'badge.background': '#96303B', 'badge.foreground': '#F2ECEB',
    'sideBar.background': '#000000', 'sideBar.border': '#29252B',
    'sideBarSectionHeader.background': '#0A0A0D', 'sideBarSectionHeader.border': '#30262D',
    'editor.background': '#000000', 'editorGutter.background': '#000000',
    'editorGroup.border': '#302A30',
    'editorGroupHeader.tabsBackground': '#000000', 'editorGroupHeader.tabsBorder': '#35242B',
    'editorGroupHeader.noTabsBackground': '#000000',
    'tab.activeBackground': '#000000', 'tab.inactiveBackground': '#000000', 'tab.border': '#29242A',
    'tab.activeBorderTop': RED, 'tab.selectedBorderTop': RED, 'tab.unfocusedActiveBorderTop': '#6A333C',
    'tab.hoverBackground': '#150C10', 'tab.unfocusedHoverBackground': '#100A0D',
    'tab.lastPinnedBorder': '#4C3037',
    'panel.background': '#000000', 'panel.border': '#35272E', 'panelTitle.activeBorder': RED,
    'statusBar.background': '#000000', 'statusBar.noFolderBackground': '#000000',
    'statusBar.border': '#47262C', 'statusBar.noFolderBorder': '#47262C',
    'statusBar.debuggingBackground': '#94313C', 'statusBar.focusBorder': '#A84952',
    'statusBarItem.focusBorder': '#A84952', 'statusBarItem.prominentBackground': '#94313C',
    'statusBarItem.prominentHoverBackground': '#AD3E49', 'statusBarItem.remoteBackground': '#7A1F2B',
    'button.background': '#94313C', 'button.hoverBackground': '#AD3E49', 'button.border': '#B54B55',
    'button.foreground': '#F5EEEE', 'button.secondaryBackground': '#0F0B0E',
    'button.secondaryHoverBackground': '#30242B', 'button.secondaryBorder': '#49323B',
    'extensionButton.prominentBackground': '#94313C', 'extensionButton.prominentHoverBackground': '#AD3E49',
    'input.background': '#050508', 'input.border': '#423039',
    'inputOption.activeBackground': '#35202A', 'inputOption.activeBorder': '#A84952',
    'dropdown.background': '#050508', 'dropdown.listBackground': '#050508', 'dropdown.border': '#423039',
    'checkbox.background': '#0A0A0D', 'checkbox.border': '#6D414B',
    'list.hoverBackground': '#160E13', 'list.focusBackground': '#30212A',
    'list.focusOutline': '#A84952', 'list.inactiveFocusOutline': '#49323C',
    'list.highlightForeground': '#E2707A', 'list.dropBackground': '#C6535C26',
    'quickInputList.focusBackground': '#30212A',
    'menu.background': '#07070A', 'menu.border': '#483039', 'menu.selectionBackground': '#3A222B',
    'menu.selectionBorder': '#96515C', 'menu.separatorBackground': '#3A2C34',
    'quickInput.background': '#07070A', 'quickInputTitle.background': '#0F0A0D',
    'commandCenter.background': '#07070A', 'commandCenter.activeBackground': '#2B1D25',
    'commandCenter.border': '#50343D', 'commandCenter.activeBorder': '#A84952',
    'toolbar.hoverBackground': '#302029', 'toolbar.activeBackground': '#432630',
    'sash.hoverBorder': '#A84952', 'progressBar.background': RED,
    'welcomePage.progress.foreground': RED,
    'editor.lineHighlightBackground': '#0E0B0D',
    'editor.selectionBackground': '#6A222ECC', 'editor.inactiveSelectionBackground': '#4A1A2260',
    'editor.selectionHighlightBackground': '#6A222E60',
    'editor.wordHighlightBackground': '#4A1A2250', 'editor.wordHighlightStrongBackground': '#6A222E80',
    'editor.findMatchBackground': '#8C4A1E99', 'editor.findMatchHighlightBackground': '#8C4A1E55',
    'editorBracketMatch.background': '#C6535C40', 'editorBracketMatch.border': RED,
    'editorLink.activeForeground': '#E2707A', 'textLink.foreground': '#E2707A',
    'textLink.activeForeground': '#FF8A93', 'notificationLink.foreground': '#E2707A',
    'editorSuggestWidget.focusOutline': '#A84952',
    'editorHoverWidget.statusBarBackground': '#0E0E12',
    'peekView.border': '#A84952', 'peekViewEditor.background': '#000000',
    'peekViewResult.background': '#000000', 'peekViewTitle.background': '#0B0B0E',
    'peekViewResult.selectionBackground': '#C6535C26',
    'peekViewEditor.matchHighlightBackground': '#C6535C33',
    'peekViewResult.matchHighlightBackground': '#C6535C33',
    'terminal.background': '#000000', 'terminal.selectionBackground': '#C6535C33',
    'minimap.background': '#000000',
    # Blue accents of the chat/agents views (disabled here, but never left blue).
    'chat.inputWorkingBorderColor1': '#94313C', 'agentsGradient.tintColor': '#94313C',
    'agentsBadge.background': '#96303B', 'agentsUnreadBadge.background': '#96303B',
    'agentsChatInput.focusBorder': '#A84952',
    # Dimmer sliders: a bright grey bar is the largest lit area on an AMOLED panel.
    'scrollbarSlider.background': '#3A3A4066', 'scrollbarSlider.hoverBackground': '#5A5A6299',
    'scrollbarSlider.activeBackground': '#7A7A8499',
    'minimapSlider.background': '#3A3A4033', 'minimapSlider.hoverBackground': '#5A5A6255',
    'minimapSlider.activeBackground': '#7A7A8466',
}


def load(path):
    text = path.read_text(encoding='utf-8')
    text = re.sub(r'^\s*//.*$', '', text, flags=re.M)
    return json.loads(re.sub(r',(\s*[}\]])', r'\1', text))


def flatten(themes, name):
    data = load(themes / f'{name}.json')
    colors, tokens, semantic = {}, [], {}
    if data.get('include'):
        parent = flatten(themes, Path(data['include']).stem)
        colors.update(parent[0])
        tokens += parent[1]
        semantic.update(parent[2])
    colors.update(data.get('colors', {}))
    tokens += data.get('tokenColors', [])
    semantic.update(data.get('semanticTokenColors', {}))
    return colors, tokens, semantic


def build(themes):
    colors, tokens, semantic = flatten(themes, '2026-dark')
    colors = {key: SURFACES.get(value.lower(), value) if isinstance(value, str) else value
              for key, value in colors.items()}
    colors.update(OVERRIDES)
    return {
        '$schema': 'vscode://schemas/color-theme',
        'name': NAME,
        'type': 'dark',
        'semanticHighlighting': True,
        'semanticTokenColors': semantic,
        'colors': dict(sorted(colors.items())),
        'tokenColors': tokens,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--themes', type=Path, default=THEMES,
                        help="directory holding VS Code's built-in theme-defaults/themes")
    args = parser.parse_args()
    json.dump(build(args.themes), sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write('\n')


if __name__ == '__main__':
    main()
