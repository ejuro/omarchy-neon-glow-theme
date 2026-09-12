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

        fg = "#e0ffd7",
        dark_fg = "#8bac81",
        light_fg = "#bfffac",
        bright_fg = "#f4fff1",
        muted = "#8aa083",

        red = "#9eff81",
        yellow = "#b0ff98",
        orange = "#a7ff8d",
        green = "#91ff70",
        cyan = "#c6ffb5",
        blue = "#a5ff8a",
        magenta = "#b9ffa3",
        brown = "#97b88d",

        bright_red = "#bfffac",
        bright_yellow = "#d1ffc3",
        bright_green = "#a9ff8f",
        bright_cyan = "#deffd4",
        bright_blue = "#c8ffb8",
        bright_magenta = "#d5ffc9",

        accent = "#91ff70",
        cursor = "#f4fff1",
        foreground = "#e0ffd7",
        background = "#000000",
        selection = "#29471f",
        selection_foreground = "#f4fff1",
        selection_background = "#29471f",
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
