# Copyright (C) 2025 AIDC-AI
# This project is licensed under the MIT License (SPDX-License-identifier: MIT).

import random
import uuid

def generate_uuid():
    return str(uuid.uuid4()).replace("-", "")

if __name__ == "__main__":
    print(generate_uuid())