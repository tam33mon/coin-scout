# Coin-Scout 🪙

eBay に新しく出品されたアンティークコインのうち、**価格が 150 ドル以上**で
タイトルに **「NGC」または「PCGS」** を含むものを自動で見つけて、**Discord** に通知します。
無料の GitHub Actions で 24 時間自動で動きます。

---

## 必要なもの（すべて無料）

1. eBay 開発者アカウント（APIのカギを取得するため）
2. Discord アカウントと、通知を受け取るサーバー（自分で作ってもOK）
3. GitHub アカウント

下の手順を上から順に進めれば動きます。コマンド入力は不要、すべてブラウザ／アプリの画面操作だけでできます。
（Discord の Webhook 作成は **パソコン版が分かりやすい** のでおすすめです）

---

## ステップ1：Discord の Webhook を作る

Webhook（ウェブフック）は「このURLに送れば、指定チャンネルに自動投稿される」という仕組みです。

1. 通知を受け取りたい **サーバー** を用意する
   - 無い場合は、Discord 左側の **「＋」→「オリジナルの作成」** で自分用サーバーを作ればOK
2. 通知用の **チャンネル**（例：`#coin-scout`）を開く
3. チャンネル名の横の **歯車（チャンネルの編集）** をクリック
4. 左メニューの **「連携サービス（Integrations）」** を開く
5. **「ウェブフックを作成（Create Webhook）」** を押す
6. 名前を決めて（例：Coin-Scout）、**「ウェブフックURLをコピー（Copy Webhook URL）」** を押す
   - この URL が `DISCORD_WEBHOOK_URL` になります

> このURLを知っている人は誰でもこのチャンネルに投稿できてしまうので、人に教えないでください。
> （あとで GitHub の「Secrets」に暗号化して保存します）

---

## ステップ2：eBay の API キーを取得する

1. https://developer.ebay.com にアクセスして無料登録（Register）
2. ログイン後、**Application Keys**（アプリのキー）ページを開く
3. **Production**（本番用）のキーを作成する
4. 表示される **App ID (Client ID)** と **Cert ID (Client Secret)** を控える
   - App ID → `EBAY_CLIENT_ID`
   - Cert ID → `EBAY_CLIENT_SECRET`

> メモ：このアプリは「検索」しかしないので、難しい追加申請は不要です。

---

## ステップ3：GitHub にアップロードする

1. https://github.com にログインし、右上「＋」→ **New repository**
2. 名前を `coin-scout` などにして、**Public（公開）** を選ぶ
   - Public を選ぶと Actions の実行時間が無料で使えます
   - APIのカギは後述の「Secrets」に暗号化して保存するので、Public でも漏れません
3. 「Create repository」を押す
4. リポジトリ画面で **Add file → Upload files** を選び、
   この `coin-scout` フォルダの中身（`coin_scout.py` / `requirements.txt` /
   `.github` フォルダ / `.gitignore`）をドラッグ＆ドロップ
5. 「Commit changes」を押す

---

## ステップ4：API キーなどを Secrets に登録する

1. リポジトリの **Settings → Secrets and variables → Actions** を開く
2. **New repository secret** を押し、次の3つを1つずつ登録する

   | 名前（Name）           | 値（Secret）                     |
   | ---------------------- | -------------------------------- |
   | `EBAY_CLIENT_ID`       | eBay の App ID                   |
   | `EBAY_CLIENT_SECRET`   | eBay の Cert ID                  |
   | `DISCORD_WEBHOOK_URL`  | Discord でコピーした Webhook URL |

   名前は表のとおり**正確に**入力してください（大文字・アンダースコアまで一致が必要）。

---

## ステップ5：動かしてみる

1. リポジトリの **Actions** タブを開く
2. 初回は「ワークフローを有効化しますか？」と出るので有効化する
3. 左の **Coin-Scout** を選び、右の **Run workflow** を押して手動実行
4. 緑のチェックが付けば成功
   - **初回は通知が来ません**（既存の出品を記録するだけ）。これは大量通知を防ぐ正常な動作です
   - 次回以降、新しく条件に合う出品が現れたら Discord に届きます

あとは 15 分おきに自動で動き続けます。

---

## カスタマイズ（`coin_scout.py` の先頭を編集するだけ）

- `MIN_PRICE = 150.0` … 下限価格を変える
- `KEYWORDS = ["NGC", "PCGS"]` … キーワードを足す／変える
- 通知の間隔 … `.github/workflows/coin-scout.yml` の `cron: "*/15 * * * *"` の数字を変える
  （例：`*/30 * * * *` で30分おき）

---

## 困ったときのチェックリスト

- 通知が来ない → `DISCORD_WEBHOOK_URL` が正しいか／そのチャンネルがまだ存在しているか
- Actions が赤くなる → Secrets の名前のスペルが表と一致しているか
- 何も検知しない → eBay 側に「新着で150ドル以上のNGC/PCGSコイン」がまだ無いだけのこともあります
  （新着がAPIに反映されるまで10〜15分ほどの遅れがあります）
