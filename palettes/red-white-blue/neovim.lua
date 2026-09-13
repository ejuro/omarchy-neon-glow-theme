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

        fg = "#d7ebff",
        dark_fg = "#8196ac",
        light_fg = "#add5ff",
        bright_fg = "#f1f8ff",
        muted = "#8391a0",

        red = "#ff8293",
        yellow = "#e8ecf5",
        orange = "#ff8d9d",
        green = "#71b7ff",
        cyan = "#b5daff",
        blue = "#8bc4ff",
        magenta = "#ffa4b0",
        brown = "#8da2b8",

        bright_red = "#ffadb8",
        bright_yellow = "#ffffff",
        bright_green = "#90c7ff",
        bright_cyan = "#d4e9ff",
        bright_blue = "#b8dbff",
        bright_magenta = "#ffc9d0",

        accent = "#71b7ff",
        cursor = "#f1f8ff",
        foreground = "#d7ebff",
        background = "#000000",
        selection = "#203347",
        selection_foreground = "#f1f8ff",
        selection_background = "#203347",
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
