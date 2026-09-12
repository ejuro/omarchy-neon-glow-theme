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

        fg = "#d3f8ff",
        dark_fg = "#7ca4ac",
        light_fg = "#a3f0ff",
        bright_fg = "#effcff",
        muted = "#809ba0",

        red = "#ff78d5",
        yellow = "#ff91dc",
        orange = "#ff85d9",
        green = "#61e6ff",
        cyan = "#adf2ff",
        blue = "#7debff",
        magenta = "#ff9de0",
        brown = "#88b0b8",

        bright_red = "#ffa6e3",
        bright_yellow = "#ffbfeb",
        bright_green = "#84ecff",
        bright_cyan = "#d0f8ff",
        bright_blue = "#b0f2ff",
        bright_magenta = "#ffc5ed",

        accent = "#61e6ff",
        cursor = "#effcff",
        foreground = "#d3f8ff",
        background = "#000000",
        selection = "#1b4047",
        selection_foreground = "#effcff",
        selection_background = "#1b4047",
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
