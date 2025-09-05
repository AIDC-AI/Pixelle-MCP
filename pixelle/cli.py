# Copyright (C) 2025 AIDC-AI
# This project is licensed under the MIT License (SPDX-License-identifier: MIT).

"""
Pixelle CLI - Simplified main entry point.

This module serves as the main entry point for the Pixelle CLI.
All functionality has been refactored into the pixelle.cli subpackage.
"""

from pixelle.cli.main import app, main


if __name__ == "__main__":
    main()
