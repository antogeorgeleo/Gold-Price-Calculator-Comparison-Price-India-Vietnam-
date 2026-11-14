#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LEO launcher  ·  Created by Anto George Leo
------------------------------------------
Starts the LEO desktop application (Tkinter window).

    python3 run_leo.py

(The Flask web version is optional and lives in app.py — it is NOT needed
to use LEO.)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from leo_desktop import main          # noqa: E402

if __name__ == "__main__":
    main()
