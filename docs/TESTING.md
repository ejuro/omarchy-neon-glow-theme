# Compatibility and testing

## Supported environment

The release was prepared and tested on Arch Linux with Omarchy **4.0.0.alpha / Quattro**, its Quickshell-based Omarchy Shell, systemd user services, and Python 3.14. The installer requires Python 3.11 or newer and checks for the Omarchy Shell and theme-generation commands before changing anything.

This is not an Omarchy 3 / Waybar theme package. Compatibility with other Omarchy 4 builds depends on their theme and shell APIs. Application configs are regenerated from the recipient's installed templates to reduce version coupling.

No optional Python packages, Blender, extra theme repositories, or custom app plugins are needed for installation.

## Tests

Run from the repository root:

```sh
/usr/bin/python integration/test_neon_glow.py
/usr/bin/python integration/test_install.py
/usr/bin/python integration/test_stock_nvim.py
```

The first test covers all 24 wallpaper mappings, all 12 palettes, black backgrounds, hue matching, readable foreground/ANSI contrast, config parsing, theme isolation, selection races, shell-reload recovery, and follower restart behavior.

The installation test creates a temporary Git repository and home directory. It uses the real Omarchy Git installer, staging logic, and theme generator. The systemd CLI is simulated so the test cannot start or stop the user's services. It checks setup, all generated palettes, reinstall, local template overrides, failed-update handling, and repeated uninstall. User app configurations are sentinel files checked for byte-for-byte preservation.

The stock-Neovim test requires the installed `omarchy-nvim` package. It copies its stock configuration and cached plugins into a temporary home, then changes palettes while Neovim remains open. It also replaces the complete theme directory. No Neon Glow Neovim helper is installed. Unsaved text and its modified flag must remain intact.

## Live checks

The running desktop has additionally been checked with all 12 variants: active Hyprland borders, matching generated shell and app configs, no Hyprland configuration errors, and retained selection after restarting the real user service.

The packaged setup is also installed on the development machine using the real user service manager. Login startup is enabled; testing restarts the service rather than rebooting the machine.

Git transport in the fresh-install test is a local `file://` repository. This exercises the same clone/staging path as GitHub, but does not test public GitHub availability; publishing is a separate step.
