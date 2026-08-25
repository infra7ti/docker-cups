# -*- coding: utf-8 -*-
##
# @file minicli.py
# @brief High-performance semantic CLI rendering engine optimized for SigERP3 tools.
#
# SPDX-FileCopyrightText: 2026 INFRA7 Serviços em TI
# SPDX-License-Identifier: GPL-2.0-or-later
##

import os
import sys
import shutil

class _Style:
    """Internal ANSI escape codes with 8-bit Xterm high-fidelity colors."""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    CLEAR_SCREEN = '\033[2J\033[H'  # Fully clears screen and positions cursor at 0:0

    # Semantic color definitions matching structural requirements
    BLUE = '\033[38;5;12m'
    GREEN = '\033[38;5;2m'
    ORANGE = '\033[38;5;208m'
    GOLD = '\033[38;5;220m'
    PURPLE = '\033[38;5;5m'
    RED = '\033[38;5;9m'
    CYAN = '\033[38;5;14m'
    WHITE = '\033[38;5;15m'
    GRAY = '\033[38;5;244m'


class Symbol:
    """Isolated structural symbols and glifos ported from high-identity legacy shell scripts."""
    FLAG = "⚑"        # Unique status identifier from dbtool (\u2691)
    ITEM = "🢂"        # Clean bullet for timeline items
    SUBITEM = "↳"     # Subitem nested pointer indicator
    DONE = "✔"        # Final operational check mark validation
    LINE_CHAR = "─"   # Horizontal thin separator line


class Cli:
    """Semantic abstraction engine for dynamic console interface rendering."""

    DEBUG_MODE = os.getenv("SIGERP_DEBUG", "false").lower() == "true"

    @staticmethod
    def highlight(text, color="gold"):
        """Applies high-visibility semantic formatting to emphasize variables or names."""
        style_code = getattr(_Style, color.upper(), _Style.GOLD)
        return f"{style_code}{text}{_Style.RESET}"

    @staticmethod
    def path(text):
        """Applies specific purple styling for file system locations or URLs."""
        return f"{_Style.PURPLE}{text}{_Style.RESET}"

    @staticmethod
    def param(text):
        """Applies specific cyan styling for keywords, types, or command-line parameters."""
        return f"{_Style.CYAN}{text}{_Style.RESET}"

    @staticmethod
    def line():
        """Draws a horizontal separator line synchronized with the current window geometry."""
        try:
            columns, _ = shutil.get_terminal_size(fallback=(80, 24))
            print(f"  {_Style.GRAY}{Symbol.LINE_CHAR * (columns - 4)}{_Style.RESET}")
        except Exception:
            print(f"  {_Style.GRAY}──────────────────────────────────────────────────────────────────────────────{_Style.RESET}")

    @staticmethod
    def title(message):
        """Renders a mandatory gold uppercase header line with a 2-character indentation."""
        print(f"\n  {_Style.BOLD}{_Style.GOLD}{message.upper()}{_Style.RESET}")

    @staticmethod
    def subtitle(message):
        """Renders an elegant secondary description line in clean white with a 2-character indentation."""
        print(f"  {_Style.WHITE}{message}{_Style.RESET}")

    @staticmethod
    def item(message, nested=False):
        """Renders progression indicators, shifting layout spacing automatically if marked as nested."""
        if nested:
            print(f"    {_Style.BLUE}{Symbol.SUBITEM}{_Style.RESET} {message}")
        else:
            print(f"  {_Style.BLUE}{Symbol.ITEM}{_Style.RESET} {message}")

    @staticmethod
    def status(level, message, indent_level=1):
        """Dynamic router mapping string keys into high-fidelity flag status states.

        Optimizes conditional routing using a clean switch/match block.
        """

        """ Use spaces to indent the message according to its indentation level """
        indent = f"  " * indent_level

        match level.lower().strip():
            case "completed" | "done":
                print(f"{indent}{_Style.GREEN}{Symbol.DONE}{_Style.RESET} Done. {message} {_Style.RESET}")
            case "success" | "succ":
                print(f"{indent}{_Style.GREEN}{Symbol.FLAG}{_Style.RESET} Success: {message} {_Style.RESET}")
            case "warning" | "warn":
                print(f"{indent}{_Style.ORANGE}{Symbol.FLAG}{_Style.RESET} Warning: {message}")
            case "error":
                print(f"{indent}{_Style.RED}{Symbol.FLAG}{_Style.RESET} Error: {message}", file=sys.stderr)
            case "critical" | "crit":
                print(f"{indent}{_Style.BOLD}{_Style.RED}{Symbol.FLAG} Critical: {message}{_Style.RESET}", file=sys.stderr)
            case "debug" | "dbg":
                if Cli.DEBUG_MODE:
                    print(f"{indent}{_Style.PURPLE}{Symbol.FLAG}{_Style.RESET} Debug: {message}")
            case "notice" | "noti":
                print(f"{indent}{_Style.CYAN}{Symbol.FLAG}{_Style.RESET} Notice: {message}")
            case "info":
                print(f"{indent}{_Style.BLUE}{Symbol.FLAG}{_Style.RESET} Info: {message}")
            case _:  # Fallback: Default standard information layout
                print(f"{indent}{_Style.BLUE}{Symbol.FLAG}{_Style.RESET} {message}")

    @staticmethod
    def section(title_text, subtitle_text):
        """Orchestrates an atomic full-screen context layout swipe for isolated executions."""
        print(_Style.CLEAR_SCREEN, end="")
        Cli.title(title_text)
        Cli.subtitle(subtitle_text)
        Cli.line()

