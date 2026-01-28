# --- ステージ1: Rustビルド ---
FROM rust:1.80-alpine AS builder
WORKDIR /usr/src/app
# 必要なビルドツールをインストール
RUN apk add --no-cache musl-dev openssl-dev openssl-libs-static pkgconfig patch
COPY . .
# Rustバイナリをビルド
RUN cargo build --release

# --- ステージ2: 最終イメージ (Alpine) ---
FROM alpine:3.20
WORKDIR /app

# Python3と実行に必要な最小限のライブラリをインストール
RUN apk add --no-cache python3 py3-pip libgcc libssl3 ca-certificates
# Flaskをインストール（PEP 668対策のフラグ付き）
RUN pip3 install --break-system-packages flask flask-cors

# ビルダーからRustバイナリをコピー
COPY --from=builder /usr/src/app/target/release/inv_sig_helper_rust /app/
# Pythonサーバーコードをコピー
COPY main.py /app/

# 外部公開用(Flask)と内部通信用(Rust)のポート
EXPOSE 10000 12999

# RustとPythonを同時に立ち上げる起動スクリプト
RUN echo "#!/bin/sh\n\
./inv_sig_helper_rust --tcp 127.0.0.1:12999 &\n\
python3 main.py" > /app/entrypoint.sh && chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]
