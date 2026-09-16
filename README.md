# 通信设备监控数据管理 API

基于 **Python + Flask + MySQL** 的轻量后端：设备台账、性能指标入库与查询、阈值告警落库。  
适合作为校招/实习作品，展示「数据建模 → REST 接口 → 落库 → 文档」的完整闭环。

## 功能

- 设备管理：注册 / 查询 / 更新 / 停用
- 性能指标：批量写入、按设备与时间范围查询
- 告警规则与告警记录：阈值触发后写入 `alerts`
- 演示数据脚本，便于本地一键体验

## 技术栈

| 组件 | 说明 |
|------|------|
| Python 3.10+ | 主语言 |
| Flask | Web 框架 |
| PyMySQL | MySQL 驱动 |
| MySQL 8.x | 数据存储 |
| SQL | 建表与查询 |

## 快速开始

### 1. 准备数据库

安装并启动 MySQL 后执行：

```bash
mysql -u root -p < schema.sql
```

或在客户端中执行 `schema.sql` 全文。

### 2. 安装依赖

```bash
cd comm-device-monitor-api
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. 配置连接

复制环境变量示例并修改：

```bash
copy .env.example .env
```

编辑 `.env`：

```env
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=你的密码
MYSQL_DB=comm_monitor
FLASK_ENV=development
```

### 4. 写入演示数据（可选）

```bash
python seed_demo.py
```

### 5. 启动服务

```bash
python run.py
```

默认监听 `http://127.0.0.1:5000`。

## API 一览

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/health` | 健康检查 |
| GET | `/api/devices` | 设备列表（支持 `status` 过滤） |
| POST | `/api/devices` | 注册设备 |
| GET | `/api/devices/<device_id>` | 设备详情 |
| PATCH | `/api/devices/<device_id>` | 更新设备（名称/状态等） |
| POST | `/api/metrics` | 写入单条性能指标 |
| POST | `/api/metrics/batch` | 批量写入指标 |
| GET | `/api/metrics` | 查询指标（`device_id`、`start`、`end`、`metric`） |
| GET | `/api/alert-rules` | 告警规则列表 |
| POST | `/api/alert-rules` | 新增规则 |
| GET | `/api/alerts` | 告警记录（可按设备过滤） |

### 示例

注册设备：

```bash
curl -X POST http://127.0.0.1:5000/api/devices ^
  -H "Content-Type: application/json" ^
  -d "{\"device_id\":\"BTS-001\",\"name\":\"基站A\",\"type\":\"macro\",\"location\":\"南京\"}"
```

写入指标并可能触发告警：

```bash
curl -X POST http://127.0.0.1:5000/api/metrics ^
  -H "Content-Type: application/json" ^
  -d "{\"device_id\":\"BTS-001\",\"metric\":\"rsrp_dbm\",\"value\":-110,\"unit\":\"dBm\"}"
```

查询近一天指标：

```bash
curl "http://127.0.0.1:5000/api/metrics?device_id=BTS-001&metric=rsrp_dbm"
```

## 项目结构

```text
comm-device-monitor-api/
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
├── schema.sql
├── seed_demo.py
├── run.py
└── app/
    ├── __init__.py      # 应用工厂
    ├── config.py        # 环境变量配置
    ├── db.py            # 连接与查询封装
    └── api.py           # REST 路由
```

## 数据模型（简要）

- `devices`：设备台账  
- `metrics`：时序性能点（设备 + 指标名 + 数值 + 时间）  
- `alert_rules`：指标阈值规则  
- `alerts`：触发后的告警记录  

写入指标时会按规则自动判断是否生成告警。

## 后续可扩展

- JWT 鉴权、分页统一响应  
- Prometheus 指标暴露  
- 简单前端表格 / Grafana 对接  
- 按天聚合报表接口  

## License

MIT
