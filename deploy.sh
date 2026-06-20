#!/bin/bash
set -e

scp bot.py extractor.py sheets.py requirements.txt opc@92.5.112.79:~/cinemabot/
ssh opc@92.5.112.79 "sudo systemctl restart cinemabot"
