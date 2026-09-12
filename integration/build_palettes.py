#!/usr/bin/python
"""Build complete palettes using installed Omarchy templates, without changing the desktop."""
from pathlib import Path
import colorsys, hashlib, json, os, re, shutil, subprocess, tempfile, tomllib
ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'source/emerald-base'
# Readable UI accents derived from the wallpaper colors, rather than emissive white cores.
VARIANTS = {
 'emerald': ('#91ff70','#2d9b58'), 'orchid': ('#e49aff','#ac55d5'),
 'gold': ('#ffd166','#e6a02f'), 'blue': ('#60ccff','#477dff'),
 'blue-yellow': ('#64aaff','#ffe85b'), 'ice-white': ('#e4f1ff','#a5c8ef'),
 'hot-coral': ('#ff967e','#f35b59'), 'ultraviolet': ('#bc86ff','#7752ff'),
 'cyberpunk': ('#61e6ff','#ff66cf'), 'ruby-red': ('#ff4d5b','#c62e3b'),
 'vaporwave': ('#b084ff','#ffc061'), 'us': ('#71b7ff','#ff7184'),
}
def rgb(hex): return tuple(int(hex[i:i+2],16)/255 for i in (1,3,5))
def hexrgb(values): return '#'+''.join(f'{round(max(0,min(1,x))*255):02x}' for x in values)
def mix(a,b,t): return hexrgb([x*(1-t)+y*t for x,y in zip(rgb(a),rgb(b))])
base_colors=tomllib.loads((BASE/'colors.toml').read_text())
files=[p for p in BASE.iterdir() if p.is_file() and (p.suffix in ('.toml','.css','.json','.theme'))]
manifest={}
for index,(slug,(accent,secondary)) in enumerate(VARIANTS.items(),1):
    multicolor = slug in ('blue-yellow', 'cyberpunk', 'vaporwave', 'us')
    support = secondary if multicolor else accent
    # ANSI names identify slots, not fixed hues: every slot belongs to this variant.
    palette = {
        'accent': accent, 'selection': mix('#000000', accent, .28),
        'background': '#000000', 'dark_background': '#000000',
        'darker_background': '#000000', 'lighter_background': '#141414',
        'foreground': mix(accent, '#ffffff', .72),
        'bright_foreground': mix(accent, '#ffffff', .90),
        'light_foreground': mix(accent, '#ffffff', .42),
        'dark_foreground': mix('#888888', accent, .30),
        'muted': mix('#888888', accent, .20),
        'red': mix(support, '#ffffff', .12),
        'green': accent,
        'yellow': mix(support, '#ffffff', .28),
        'blue': mix(accent, '#ffffff', .18),
        'magenta': mix(support, '#ffffff', .36),
        'cyan': mix(accent, '#ffffff', .48),
        'orange': mix(support, '#ffffff', .20),
        'brown': mix('#999999', accent, .30),
        'bright_red': mix(support, '#ffffff', .42),
        'bright_green': mix(accent, '#ffffff', .22),
        'bright_yellow': mix(support, '#ffffff', .58),
        'bright_blue': mix(accent, '#ffffff', .50),
        'bright_magenta': mix(support, '#ffffff', .62),
        'bright_cyan': mix(accent, '#ffffff', .70),
    }
    if slug == 'us':
        palette['yellow'] = '#e8ecf5'
        palette['bright_yellow'] = '#ffffff'
    replacements = {}
    for p in files:
        for color in re.findall(r'#[0-9a-fA-F]{6}', p.read_text()):
            h, saturation, value = colorsys.rgb_to_hsv(*rgb(color))
            if saturation > .015:
                tone = support if multicolor and (h < .18 or h > .75) else accent
                # Theme any extra app-specific colors, not just colors.toml roles.
                replacements[color.lower()] = mix(tone, '#ffffff', (1-saturation)*.65)
    replacements.update({base_colors[key]: value for key, value in palette.items()})
    replacements.update({
        '#b9eda8': mix(accent, '#ffffff', .18),
        '#0b120d': '#0a0a0a', '#2d9b58': secondary,
    })
    target=ROOT/'palettes'/slug
    target.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='neon-glow-build-') as temp:
        home=Path(temp); stage=home/'.local/state/omarchy/current/next-theme'
        stage.mkdir(parents=True)
        user_templates=Path.home()/'.config/omarchy/themed'
        if user_templates.exists():
            shutil.copytree(user_templates,home/'.config/omarchy/themed')
        for p in files:
            text=re.sub(r'#[0-9a-fA-F]{6}',lambda m: replacements.get(m[0].lower(),m[0]),p.read_text())
            text=text.replace('Emerald Glow',f'Neon Glow — {slug.replace("-"," ").title()}')
            if p.name=='colors.toml' and slug=='us':
                text=re.sub(r'hyprland_active_border = .*',f'hyprland_active_border = "{accent} #f5f7ff {secondary} 45deg"',text)
            if p.name.startswith('shell.'):
                text=re.sub(r'(selected-background\s*=\s*)"#[0-9a-fA-F]{6}"', lambda m: m[1] + '"' + accent + '"', text)
            if p.name == 'gtk.css':
                text=re.sub(r'@define-color accent_light #[0-9a-fA-F]{6};', '@define-color accent_light ' + mix(accent, '#ffffff', .30) + ';', text)
            (stage/p.name).write_text(text)
        env=os.environ|{'HOME':str(home),'OMARCHY_PATH':'/usr/share/omarchy','PATH':'/usr/share/omarchy/bin:/usr/bin:/bin'}
        subprocess.run(['/usr/share/omarchy/bin/omarchy-theme-set-templates'],env=env,check=True,capture_output=True)
        for p in stage.iterdir():
            if p.is_file(): shutil.copy2(p,target/p.name)
    digest=hashlib.sha256(b''.join(p.name.encode()+p.read_bytes() for p in sorted(target.iterdir()) if p.is_file() and p.name!='neon-glow-variant')).hexdigest()
    (target/'neon-glow-variant').write_text(slug+' '+digest+'\n')
    manifest[slug]={'accent':accent,'secondary':secondary,'backgrounds':[p.name for p in sorted((ROOT/'backgrounds').glob(f'{index:02d}-*.png'))]}
    assert len(manifest[slug]['backgrounds'])==2
    print('Built',slug,flush=True)
(ROOT/'palettes.json').write_text(json.dumps(manifest,indent=2)+'\n')

# The initial Neon Glow appearance also uses the coordinated Emerald palette.
for source in files:
    shutil.copy2(ROOT/'palettes/emerald'/source.name, ROOT/source.name)
