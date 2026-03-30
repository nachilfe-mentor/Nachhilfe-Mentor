#!/usr/bin/env bash
# Wait for batch to finish, then start the regular autoblog loop
while tmux has-session -t autoblog-batch 2>/dev/null; do
    sleep 30
done
echo "Batch finished. Starting regular autoblog..."
/home/opc/Nachhilfe-Mentor/auto-blog.sh
