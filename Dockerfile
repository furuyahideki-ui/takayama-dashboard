FROM python:3.11-slim

# 作業ディレクトリの設定
WORKDIR /app

# 依存関係ファイルのコピー
COPY requirements.txt .

# パッケージのインストール
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションのコードをコピー
COPY . .

# Cloud Runがリッスンするポートを指定
EXPOSE 8080

# アプリケーションの起動
CMD ["streamlit", "run", "app.py", "--server.port=8080", "--server.address=0.0.0.0"]
