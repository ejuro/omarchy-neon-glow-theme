#!/usr/bin/python
"""Install or remove Neon Glow's user service. Does not edit application configs."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
SERVICE = 'neon-glow.service'
# Only color data from the repo is staged. Executable configs come from local Omarchy templates.
COLOR_FILES = {'colors.toml', 'gtk.css', 'obsidian.css', 'vscode-theme.json', 'icons.theme'}

def run(*args, **kwargs):
    return subprocess.run(args, check=True, **kwargs)

def preflight():
    if sys.version_info < (3, 11): raise RuntimeError('Python 3.11 or newer is required.')
    required = ('systemctl', 'omarchy', 'omarchy-shell', 'omarchy-theme-set-templates', 'omarchy-theme-color', 'hyprctl')
    missing = [name for name in required if not shutil.which(name)]
    if missing: raise RuntimeError('Requires Omarchy 4 / Quattro with its graphical shell. Missing: '+', '.join(missing))
    omarchy = Path(os.environ.get('OMARCHY_PATH', '/usr/share/omarchy'))
    if not (omarchy/'default/themed/shell.toml.tpl').is_file():
        raise RuntimeError('Requires Omarchy 4 / Quattro theme templates; older Waybar versions are unsupported.')
    run('systemctl', '--user', 'show-environment', stdout=subprocess.DEVNULL)
    return omarchy

def prepare(home, state, omarchy):
    import tomllib
    manifest = json.loads((ROOT/'palettes.json').read_text())
    state.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix='.palettes-', dir=state))
    try:
        for slug, item in manifest.items():
            if Path(slug).name != slug or slug.startswith('.'): raise RuntimeError('Invalid variant name')
            for wallpaper in item['backgrounds']:
                if Path(wallpaper).name != wallpaper or not (ROOT/'backgrounds'/wallpaper).is_file():
                    raise RuntimeError('Missing wallpaper: '+wallpaper)
            with tempfile.TemporaryDirectory(prefix='neon-glow-templates-') as scratch:
                temp_home = Path(scratch)
                output = temp_home/'.local/state/omarchy/current/next-theme'
                output.mkdir(parents=True)
                templates = home/'.config/omarchy/themed'
                if templates.is_dir(): shutil.copytree(templates, temp_home/'.config/omarchy/themed')
                for source in (ROOT/'palettes'/slug).iterdir():
                    if source.is_file() and (source.name in COLOR_FILES or (source.name.startswith('shell.') and source.name != 'shell.toml' and source.suffix == '.toml')):
                        shutil.copy2(source, output/source.name)
                colors = tomllib.loads((output/'colors.toml').read_text())
                if colors['accent'] != item['accent']: raise RuntimeError('Invalid palette: '+slug)
                env = os.environ | {'HOME': str(temp_home), 'OMARCHY_PATH': str(omarchy)}
                run('omarchy-theme-set-templates', env=env, stdout=subprocess.DEVNULL)
                for name in ('shell.toml','neovim.lua','foot.ini','hyprland.lua'):
                    if not (output/name).is_file(): raise RuntimeError('Omarchy did not generate '+name)
                for path in output.glob('*.toml'): tomllib.loads(path.read_text())
                digest = hashlib.sha256(b''.join(p.name.encode()+p.read_bytes() for p in sorted(output.iterdir()) if p.is_file())).hexdigest()
                (output/'neon-glow-variant').write_text(slug+' '+digest+'\n')
                shutil.copytree(output, staging/slug)
        return staging
    except Exception:
        shutil.rmtree(staging)
        raise

def install(home):
    omarchy = preflight()
    target = home/'.config/omarchy/themes/neon-glow'
    if (target.exists() or target.is_symlink()) and target.resolve() != ROOT:
        raise RuntimeError('Another Neon Glow installation exists at '+str(target)+'. Run its install.sh to update it.')
    state = home/'.local/state/neon-glow'
    unit = home/'.config/systemd/user'/SERVICE
    if unit.exists() and 'neon_glow.py' not in unit.read_text():
        raise RuntimeError('An unrelated neon-glow.service already exists; leaving it untouched.')
    previous_unit = unit.read_text() if unit.exists() else None
    staging = prepare(home, state, omarchy)
    service_text = (ROOT/'integration'/SERVICE).read_text()
    service_text = service_text.replace('Environment=OMARCHY_PATH=/usr/share/omarchy', 'Environment="OMARCHY_PATH='+str(omarchy)+'"')
    # All validation and generation finish before stopping the existing integration.
    subprocess.run(['systemctl','--user','stop',SERVICE], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    previous = state/'palettes.previous'
    try:
        if previous.exists(): shutil.rmtree(previous)
        if (state/'palettes').exists(): (state/'palettes').rename(previous)
        staging.rename(state/'palettes')
        if not target.exists():
            target.parent.mkdir(parents=True,exist_ok=True)
            target.symlink_to(ROOT, target_is_directory=True)
        unit.parent.mkdir(parents=True,exist_ok=True)
        if unit.exists() and unit.read_text()!=service_text:
            shutil.copy2(unit, state/f'service-backup-{time.time_ns()}.service')
        unit.write_text(service_text)
        run('systemctl','--user','daemon-reload')
        run('systemctl','--user','enable',SERVICE)
        run('systemctl','--user','restart',SERVICE)
        run('systemctl','--user','is-active','--quiet',SERVICE)
    except Exception:
        if previous.exists():
            shutil.rmtree(state/'palettes',ignore_errors=True)
            previous.rename(state/'palettes')
        if previous_unit is not None:
            unit.write_text(previous_unit)
            subprocess.run(['systemctl','--user','daemon-reload'],check=False)
            subprocess.run(['systemctl','--user','restart',SERVICE],check=False)
        else:
            subprocess.run(['systemctl','--user','disable','--now',SERVICE],check=False)
            unit.unlink(missing_ok=True)
            subprocess.run(['systemctl','--user','daemon-reload'],check=False)
        raise
    if previous.exists(): shutil.rmtree(previous)
    current = home/'.local/state/omarchy/current/theme.name'
    if not current.exists() or current.read_text().strip()!='neon-glow':
        run('omarchy','theme','set','Neon Glow')
    print('Neon Glow is ready. Change wallpapers with your normal background picker.')
    print('Starts automatically at login. No Neovim or other app configuration was changed.')

def uninstall(home):
    unit = home/'.config/systemd/user'/SERVICE
    if unit.exists() and 'neon_glow.py' not in unit.read_text():
        raise RuntimeError('The service has been replaced by another program; leaving it untouched.')
    subprocess.run(['systemctl','--user','disable','--now',SERVICE],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    unit.unlink(missing_ok=True)
    run('systemctl','--user','daemon-reload')
    state=home/'.local/state/neon-glow'
    for name in ('palettes','palettes.previous'):
        if (state/name).is_dir(): shutil.rmtree(state/name)
    (state/'selection.json').unlink(missing_ok=True)
    print('Automatic color switching removed. Current colors and wallpaper are unchanged.')
    print('Neon Glow remains available as a static theme. Switch to another theme before removing its folder.')

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--uninstall',action='store_true')
    args=parser.parse_args()
    try:
        (uninstall if args.uninstall else install)(Path.home())
    except (OSError,ValueError,RuntimeError,subprocess.CalledProcessError) as error:
        print('Neon Glow: '+str(error),file=sys.stderr)
        return 1
    return 0

if __name__=='__main__': sys.exit(main())
