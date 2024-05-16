
<div align="center">
<img width="20%" src="./public/logo.png">

# SPACE FIT 健身空間 - 全端網站
</div>

> ⚠ 測試操作請同時下載前、後台資料包 : <br>
前台 --> https://github.com/Jam-Peng/space_fit_frontend <br>
後台 --> https://github.com/Jam-Peng/space_fit_backend

>⚠ 由於將資料庫部署 Aws 選擇較低的 CPU 配置，影響應用程序與數據庫查詢的時間增加，降低網頁加載速度。

###  Preview :

<table width="100%"> 
<tr>
<td width="50%">      
&nbsp; 
<br>
<p align="center">
  Frontend - Home
</p>
<img src="./public/frontend_home.jpg">
</td> 
<td width="50%">
<br>
<p align="center">
  Backend - Course manage
</p>
<center>
<img src="./public/backend_course_manage.jpg">
</td>
</tr>
</table>

#

## 專案說明
- 模擬健身中心售課網站與後台管理系統。
- 透過 Flask API 將將前、後端做資料的整合與應用。
- 部署資料庫於 aws-RDS，
- <a href="https://drive.google.com/file/d/13Z1jdBGDP95JCOCd2z3zKP7JwtV1Wgn5/view?usp=sharing" target="_blank">開啟線上完整專案指南</a>

#
### 使用環境
- `Python-3`。

---
### 使用技術
- 以 `Flask` 框架開發。
- 使用 `SQLAlchemy` ORM (物件關聯映射) 庫，管理資料庫連接的建立、維護和釋放，無需手動管理資料庫連接。避免資源洩漏並提高應用程序的性能。
- 使用 `Marshmallow` 和 `SQLAlchemy` 一起使用，用於資料模型的序列化和反序列化，以便在 Web 應用程序中進行數據的轉換。允許將 Python 資料轉換為 JSON 或其他數據格式，並將接收到的客户端資料反序列化為資料庫模型。

### 使用套件
- `flask` -- `Flask`、`request`、`jsonify`、`current_app`、`Blueprint`
- `flask_sqlalchemy` -- `SQLAlchemy`
- `flask_marshmallow` -- `Marshmallow`
- `functools` -- `wraps`
- `werkzeug.security` -- `generate_password_hash`、`check_password_hash`
- `werkzeug.utils` -- `secure_filename`
- `jwt`
- `os`
- `base64`
- `uuid`
- `datetime` -- `datetime`、`timedelta`
- `flask_cors` -- `CORS`


## 如何執行 - `前、後台`
--> 使用 Zip 下載專案或使用下面的指令下載
```bash
git clone https://github.com/Jam-Peng/space_fit_backend.git
```

--> 進入前台資料包
```bash
cd frontend
```

--> 或進入後台資料包
```bash
cd backendend
```

--> 安裝專案需求 dependencies
```bash
npm install
```

--> 執行專案
```bash
npm run server
```

## 如何執行 - `伺服器`
--> 使用 Zip 下載專案或使用下面的指令下載
```bash
git clone https://github.com/Jam-Peng/space_fit_server.git
```

--> 進入server資料包
```bash
cd server
```

--> 建立虛擬環境
```bash
conda create --name venv python=3.9
```

--> 執行虛擬環境
```bash
conda activate venv
```

--> 安裝套件
```bash
pip install -r requirements.txt
```

--> 運行伺服器
```bash
flask run
```
