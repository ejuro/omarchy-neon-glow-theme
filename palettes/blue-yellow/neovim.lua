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

        fg = "#d4e7ff",
        dark_fg = "#7d92ac",
        light_fg = "#a5ceff",
        bright_fg = "#f0f6ff",
        muted = "#818fa0",

        red = "#ffeb6f",
        yellow = "#ffee89",
        orange = "#ffed7c",
        green = "#64aaff",
        cyan = "#aed3ff",
        blue = "#80b9ff",
        magenta = "#fff096",
        brown = "#899eb8",

        bright_red = "#fff2a0",
        bright_yellow = "#fff5ba",
        bright_green = "#86bdff",
        bright_cyan = "#d0e5ff",
        bright_blue = "#b2d4ff",
        bright_magenta = "#fff6c1",

        accent = "#64aaff",
        cursor = "#f0f6ff",
        foreground = "#d4e7ff",
        background = "#000000",
        selection = "#1c3047",
        selection_foreground = "#f0f6ff",
        selection_background = "#1c3047",
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
