"""Exercise selection, theme isolation, restart persistence, and failed refresh recovery."""
import colorsys
import importlib.util
import json
from pathlib import Path
import tempfile
import tomllib
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('neon_glow',ROOT/'integration/neon_glow.py')
module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)

class FollowerTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.home=Path(self.temp.name)
        self.runtime=self.home/'runtime'; self.runtime.mkdir()
        self.current=self.home/'.local/state/omarchy/current'
        (self.current/'theme').mkdir(parents=True)
        (self.current/'theme.name').write_text('neon-glow\n')
        self.calls=[]
        self.follower=module.Follower(home=self.home,root=ROOT,runtime=self.runtime,runner=lambda command: self.calls.append(command) or True)
    def tearDown(self): self.temp.cleanup()
    def select(self,slug,design=0):
        link=self.current/'background'; link.unlink(missing_ok=True)
        link.symlink_to(ROOT/'backgrounds'/self.follower.manifest[slug]['backgrounds'][design])
    def test_all_palettes_and_designs(self):
        for slug in self.follower.manifest:
            self.select(slug)
            self.assertTrue(self.follower.apply())
            self.assertTrue(self.follower.matches(slug))
            count=len(self.calls)
            self.select(slug,1)
            self.assertFalse(self.follower.apply())
            self.assertEqual(count,len(self.calls))
    def test_other_theme_is_untouched(self):
        self.select('us'); (self.current/'theme.name').write_text('other')
        self.assertFalse(self.follower.apply()); self.assertEqual(self.calls,[])
        self.assertFalse((self.current/'theme/colors.toml').exists())
    def test_restart_and_reapply(self):
        self.select('cyberpunk'); self.follower.apply()
        replacement=module.Follower(home=self.home,root=ROOT,runtime=self.runtime,runner=lambda command: True)
        self.assertEqual(replacement.desired()[0],'cyberpunk')
        self.assertFalse(replacement.apply())
        (self.current/'theme/colors.toml').write_text((ROOT/'colors.toml').read_text())
        self.assertTrue(replacement.apply())
        self.assertEqual(json.loads(replacement.saved.read_text())['variant'],'cyberpunk')
    def test_missing_or_unknown_wallpaper(self):
        self.assertFalse(self.follower.apply())
        (self.home/'custom.png').touch(); (self.current/'background').symlink_to(self.home/'custom.png')
        self.assertFalse(self.follower.apply()); self.assertEqual(self.calls,[])
    def test_selection_changed_while_waiting_for_lock(self):
        self.select('blue')
        original=self.follower.desired
        count=0
        def desired():
            nonlocal count
            count+=1
            if count==2: (self.current/'theme.name').write_text('other')
            return original()
        self.follower.desired=desired
        self.assertFalse(self.follower.apply()); self.assertEqual(self.calls,[])
    def test_shell_failure_is_retried(self):
        self.select('us'); self.follower.runner=lambda command: False
        self.assertFalse(self.follower.apply()); self.assertFalse(self.follower.matches('us'))
        self.follower.runner=lambda command: True
        self.assertTrue(self.follower.apply())
    def test_valid_configs_and_contrast(self):
        def lum(color):
            channels=[int(color[i:i+2],16)/255 for i in (1,3,5)]
            channels=[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in channels]
            return sum(a*b for a,b in zip(channels,(.2126,.7152,.0722)))
        for slug in self.follower.manifest:
            palette=ROOT/'palettes'/slug
            for p in palette.glob('*.toml'): tomllib.loads(p.read_text())
            for p in palette.glob('*.json'): json.loads(p.read_text())
            colors=tomllib.loads((palette/'colors.toml').read_text())
            self.assertEqual(colors['background'], '#000000')
            slots=('red','green','yellow','blue','magenta','cyan','bright_red','bright_green','bright_yellow','bright_blue','bright_magenta','bright_cyan')
            if slug not in ('blue-yellow','cyberpunk','vaporwave','us'):
                def hue(color):
                    return colorsys.rgb_to_hsv(*(int(color[i:i+2],16)/255 for i in (1,3,5)))[0]
                for slot in slots:
                    distance=abs(hue(colors[slot])-hue(colors['accent']))
                    self.assertLess(min(distance,1-distance),.012,(slug,slot))
            for key in ('foreground','accent','muted',*slots):
                ratio=(lum(colors[key])+.05)/(lum(colors['background'])+.05)
                self.assertGreaterEqual(ratio,4.5,(slug,key,ratio))
            for p in palette.iterdir():
                self.assertNotIn('{{ ',p.read_text(),p.name)

if __name__=='__main__': unittest.main()
