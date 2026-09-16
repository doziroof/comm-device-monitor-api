-- 通信设备监控数据管理 API 初始化脚本
CREATE DATABASE IF NOT EXISTS comm_monitor
  DEFAULT CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE comm_monitor;

DROP TABLE IF EXISTS alerts;
DROP TABLE IF EXISTS alert_rules;
DROP TABLE IF EXISTS metrics;
DROP TABLE IF EXISTS devices;

CREATE TABLE devices (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  device_id VARCHAR(64) NOT NULL COMMENT '业务设备编号',
  name VARCHAR(128) NOT NULL COMMENT '设备名称',
  type VARCHAR(64) DEFAULT NULL COMMENT '设备类型，如 macro/smallcell',
  location VARCHAR(128) DEFAULT NULL COMMENT '部署位置',
  status TINYINT NOT NULL DEFAULT 1 COMMENT '1=在线 0=停用',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uk_device_id (device_id),
  KEY idx_status (status)
) ENGINE=InnoDB COMMENT='设备台账';

CREATE TABLE metrics (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  device_id VARCHAR(64) NOT NULL,
  metric VARCHAR(64) NOT NULL COMMENT '指标名，如 rsrp_dbm',
  value DOUBLE NOT NULL,
  unit VARCHAR(32) DEFAULT NULL,
  collected_at DATETIME NOT NULL COMMENT '采集时间',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  KEY idx_device_metric_time (device_id, metric, collected_at)
) ENGINE=InnoDB COMMENT='性能指标时序数据';

CREATE TABLE alert_rules (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  metric VARCHAR(64) NOT NULL,
  operator VARCHAR(8) NOT NULL COMMENT '> >= < <= =',
  threshold DOUBLE NOT NULL,
  severity VARCHAR(16) NOT NULL DEFAULT 'warning' COMMENT 'info/warning/critical',
  enabled TINYINT NOT NULL DEFAULT 1,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uk_metric_op (metric, operator, threshold)
) ENGINE=InnoDB COMMENT='告警阈值规则';

CREATE TABLE alerts (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  device_id VARCHAR(64) NOT NULL,
  metric VARCHAR(64) NOT NULL,
  value DOUBLE NOT NULL,
  rule_id BIGINT DEFAULT NULL,
  severity VARCHAR(16) NOT NULL DEFAULT 'warning',
  message VARCHAR(255) NOT NULL,
  triggered_at DATETIME NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  KEY idx_device_time (device_id, triggered_at)
) ENGINE=InnoDB COMMENT='告警记录';

INSERT INTO alert_rules (metric, operator, threshold, severity, enabled) VALUES
  ('rsrp_dbm', '<', -110, 'warning', 1),
  ('rsrp_dbm', '<', -120, 'critical', 1),
  ('cpu_percent', '>', 85, 'warning', 1),
  ('cpu_percent', '>', 95, 'critical', 1);
