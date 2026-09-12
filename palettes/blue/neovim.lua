return {
  {
    "bjarneo/aether.nvim",
    branch = "v3",
    name = "aether",
    priority = 1000,
    opts = {
      colors = {
        bg = "#000000",
        dark_bg = "#000000",
        darker_bg = "#000000",
        lighter_bg = "#141414",

        fg = "#d2f1ff",
        dark_fg = "#7c9cac",
        light_fg = "#a3e1ff",
        bright_fg = "#effaff",
        muted = "#8096a0",

        red = "#73d2ff",
        yellow = "#8ddaff",
        orange = "#80d6ff",
        green = "#60ccff",
        cyan = "#ace4ff",
        blue = "#7dd5ff",
        magenta = "#99deff",
        brown = "#88a8b8",

        bright_red = "#a3e1ff",
        bright_yellow = "#bceaff",
        bright_green = "#83d7ff",
        bright_cyan = "#cff0ff",
        bright_blue = "#b0e6ff",
        bright_magenta = "#c3ecff",

        accent = "#60ccff",
        cursor = "#effaff",
        foreground = "#d2f1ff",
        background = "#000000",
        selection = "#1b3947",
        selection_foreground = "#effaff",
        selection_background = "#1b3947",
      },
    },
  },
  {
    "LazyVim/LazyVim",
    opts = {
      colorscheme = "aether",
    },
  },
}
