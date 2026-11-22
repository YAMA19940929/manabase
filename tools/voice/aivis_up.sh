#!/usr/bin/env bash
# AivisSpeech エンジンをこのマシンの中だけ(127.0.0.1:10101)で起動し、基本の声「阿井田 茂」を入れる。
#
#   bash tools/voice/aivis_up.sh
#
# 前提:Docker が動いていること(クラウドのセッションでは、先に dockerd をバックグラウンドで起動しておく)。
# エンジンは起動時に Hugging Face から言語モデルを取ってくるので、セッションのプロキシと証明書を
# そのまま中に渡す(HTTPS_PROXY / CA バンドルが無い環境では、その部分は空のまま動く)。
set -euo pipefail
IMAGE=ghcr.io/aivis-project/aivisspeech-engine:cpu-latest
NAME=aivis
CA=${CA_BUNDLE:-/root/.ccr/ca-bundle.crt}

docker info >/dev/null 2>&1 || { echo "Docker が動いていません。先に dockerd を起動してください。" >&2; exit 1; }

if curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:10101/version 2>/dev/null | grep -q 200; then
  echo "AivisSpeech はもう動いています。"
else
  docker rm -f "$NAME" >/dev/null 2>&1 || true
  args=(-d --name "$NAME" --network host -e NO_PROXY=127.0.0.1,localhost)
  if [ -n "${HTTPS_PROXY:-}" ]; then args+=(-e HTTPS_PROXY="$HTTPS_PROXY" -e HTTP_PROXY="$HTTPS_PROXY"); fi
  if [ -f "$CA" ]; then
    args+=(-v "$CA:/ccr/ca-bundle.crt:ro" -e SSL_CERT_FILE=/ccr/ca-bundle.crt
           -e REQUESTS_CA_BUNDLE=/ccr/ca-bundle.crt -e CURL_CA_BUNDLE=/ccr/ca-bundle.crt)
  fi
  docker run "${args[@]}" "$IMAGE" gosu user /opt/python/bin/poetry run python ./run.py --host 127.0.0.1 >/dev/null
  echo -n "起動を待っています"
  for _ in $(seq 1 200); do
    curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:10101/version 2>/dev/null | grep -q 200 && break
    docker ps --filter name="$NAME" --format "{{.Status}}" | grep -q Up || { echo; docker logs "$NAME" 2>&1 | tail -5; exit 1; }
    echo -n "."; sleep 2
  done
  echo " OK"
fi

# 基本の声を確認(無ければ AivisHub から入れる)
python3 "$(dirname "$0")/tts.py" "テストです。" /tmp/aivis_check.wav >/dev/null
echo "基本の声:阿井田 茂(ノーマル)で読み上げできます。"
