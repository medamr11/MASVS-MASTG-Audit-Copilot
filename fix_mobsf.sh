#!/bin/bash
echo "Starting MobSF in the background..."
docker run -d --name mobsf_daemon -p 8000:8000 opensecurity/mobile-security-framework-mobsf:latest > /dev/null 2>&1 || docker start mobsf_daemon

echo "Waiting for MobSF to generate REST API Key (this may take 15-30 seconds)..."
API_KEY=""
while [ -z "$API_KEY" ]; do
    sleep 2
    API_KEY=$(docker logs mobsf_daemon 2>&1 | grep "REST API Key:" | head -n 1 | awk '{print $NF}')
done

echo "Found MobSF API Key: $API_KEY"

echo "Updating backend/.env with the new API key..."
sed -i "s/^MOBSF_API_KEY=.*/MOBSF_API_KEY=$API_KEY/" backend/.env

echo "Triggering backend reload..."
touch backend/app/main.py
sleep 3

echo "✅ Everything is set up! You can now go to http://localhost:5173/upload and upload your APK."
