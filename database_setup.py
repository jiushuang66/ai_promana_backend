import sys
from pathlib import Path

import pymysql

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from ai_promana_backend.config import settings

TABLE_SQL = [
    """
    CREATE TABLE IF NOT EXISTS `users` (
        `id` INT NOT NULL AUTO_INCREMENT COMMENT '自增ID',
        `username` VARCHAR(50) NOT NULL COMMENT '用户名',
        `nickname` VARCHAR(100) DEFAULT NULL COMMENT '昵称',
        `password_hash` VARCHAR(255) NOT NULL COMMENT '密码哈希',
        `real_name` VARCHAR(100) DEFAULT NULL COMMENT '真实姓名',
        `email` VARCHAR(100) NOT NULL COMMENT '邮箱',
        `phone` VARCHAR(20) DEFAULT NULL COMMENT '电话',
        `avatar_url` VARCHAR(500) DEFAULT NULL COMMENT '头像URL',
        `role` VARCHAR(20) DEFAULT 'user' COMMENT '平台角色：admin/user/member（兼容旧值 member）',
        `department` VARCHAR(100) DEFAULT NULL COMMENT '部门',
        `department_id` VARCHAR(50) DEFAULT NULL COMMENT '部门ID（兼容前端 departmentId）',
        `position` VARCHAR(100) DEFAULT NULL COMMENT '职位',
        `note` VARCHAR(500) DEFAULT NULL COMMENT '用户备注',
        `status` VARCHAR(20) DEFAULT 'pending' COMMENT '状态：pending/active/disabled（前端可映射：待激活/正常/停用）',
        `join_date` DATE DEFAULT NULL COMMENT '加入日期',
        `last_login_time` DATETIME DEFAULT NULL COMMENT '最后登录时间',
        `last_login_ip` VARCHAR(50) DEFAULT NULL COMMENT '最后登录IP',
        `password_updated_at` DATETIME DEFAULT NULL COMMENT '密码最近修改时间',
        `failed_login_count` INT DEFAULT 0 COMMENT '连续登录失败次数',
        `locked_until` DATETIME DEFAULT NULL COMMENT '账号锁定到期时间',
        `version` INT DEFAULT 1 COMMENT '乐观锁版本号',
        `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
        `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
        PRIMARY KEY (`id`),
        UNIQUE KEY `uniq_users_username` (`username`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';
    """,
    """
    CREATE TABLE IF NOT EXISTS `projects` (
        `id` INT NOT NULL AUTO_INCREMENT COMMENT '项目ID',
        `project_code` VARCHAR(50) NOT NULL COMMENT '项目编码',
        `project_name` VARCHAR(200) NOT NULL COMMENT '项目名称',
        `description` TEXT COMMENT '项目描述/摘要',
        `project_type` VARCHAR(50) DEFAULT NULL COMMENT '项目类型',
        `status` VARCHAR(20) DEFAULT 'active' COMMENT '状态：active/paused/completed/archived/pending',
        `priority` VARCHAR(20) DEFAULT 'medium' COMMENT '优先级：low/medium/high/p0/p1/p2/p3',
        `health_score` INT DEFAULT 100 COMMENT '健康度评分 0-100',
        `completion_rate` DECIMAL(5,2) DEFAULT 0 COMMENT '完成度百分比 0-100',
        `start_date` DATE DEFAULT NULL COMMENT '开始日期',
        `end_date` DATE DEFAULT NULL COMMENT '结束日期',
        `pm_id` INT DEFAULT NULL COMMENT '项目经理ID',
        `team_id` INT DEFAULT NULL COMMENT '归属团队ID',
        `estimated_members` INT DEFAULT 6 COMMENT '预计成员数',
        `template_type` VARCHAR(50) DEFAULT NULL COMMENT '模板类型：需求迭代/平台交付/验证实验',
        `project_template_id` INT DEFAULT NULL COMMENT '项目模板ID（关联 project_templates.id）',
        `current_stage` VARCHAR(50) DEFAULT NULL COMMENT '当前阶段：需求评审/开发实现/联调验证/上线验收',
        `baseline_version` VARCHAR(20) DEFAULT 'V1' COMMENT '当前基线版本',
        `risk_sync_enabled` TINYINT DEFAULT 1 COMMENT '是否开启风险同步：0否 1是',
        `report_subscription` VARCHAR(50) DEFAULT 'weekly' COMMENT '报告订阅频率：daily/weekly/monthly',
        `report_subscribers` VARCHAR(500) DEFAULT NULL COMMENT '报告订阅人列表（逗号或JSON）',
        `default_view` VARCHAR(50) DEFAULT 'overview' COMMENT '默认详情入口：overview/kanban/gantt',
        `risk_remind_freq` VARCHAR(50) DEFAULT 'daily' COMMENT '风险提醒频率：daily/weekly/exception',
        `tags` VARCHAR(500) DEFAULT NULL COMMENT '标签，JSON格式',
        `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
        `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
        PRIMARY KEY (`id`),
        UNIQUE KEY `uniq_projects_project_code` (`project_code`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='项目表';
    """,
    """
    CREATE TABLE IF NOT EXISTS `tasks` (
        `id` INT NOT NULL AUTO_INCREMENT COMMENT '任务ID',
        `task_code` VARCHAR(50) DEFAULT NULL COMMENT '任务编码',
        `task_title` VARCHAR(200) NOT NULL COMMENT '任务标题',
        `task_content` TEXT COMMENT '任务内容',
        `project_id` INT NOT NULL COMMENT '所属项目ID',
        `parent_task_id` INT DEFAULT NULL COMMENT '父任务ID',
        `milestone_id` INT DEFAULT NULL COMMENT '关联里程碑ID',
        `assignee_id` INT DEFAULT NULL COMMENT '负责人ID',
        `reviewer_id` INT DEFAULT NULL COMMENT '复核人ID',
        `status` VARCHAR(20) DEFAULT 'pending' COMMENT '状态：pending/in_progress/review/completed/blocked（兼容前端别名：todo/done）',
        `column_key` VARCHAR(50) DEFAULT NULL COMMENT '看板列Key：todo/doing/review/blocked/done',
        `priority` VARCHAR(20) DEFAULT 'medium' COMMENT '优先级：low/medium/high/urgent/p0/p1/p2/p3',
        `sort_order` DECIMAL(12,4) DEFAULT 0 COMMENT '看板/列表排序值',
        `progress` DECIMAL(5,2) DEFAULT 0 COMMENT '进度百分比 0-100',
        `estimated_hours` DECIMAL(10,2) DEFAULT NULL COMMENT '预估工时',
        `actual_hours` DECIMAL(10,2) DEFAULT NULL COMMENT '实际工时',
        `start_date` DATETIME DEFAULT NULL COMMENT '开始时间',
        `due_date` DATETIME DEFAULT NULL COMMENT '截止日期',
        `completion_date` DATETIME DEFAULT NULL COMMENT '完成时间',
        `tags` VARCHAR(500) DEFAULT NULL COMMENT '标签，JSON格式',
        `pbc_binding` VARCHAR(200) DEFAULT NULL COMMENT 'PBC绑定目标',
        `blocking_reason` TEXT COMMENT '阻塞原因',
        `dependency_task_id` INT DEFAULT NULL COMMENT '主依赖任务ID（兼容字段，复杂依赖建议使用 task_dependencies）',
        `critical_path` TINYINT DEFAULT 0 COMMENT '是否关键路径：0否 1是',
        `status_changed_at` DATETIME DEFAULT NULL COMMENT '任务状态最近变更时间',
        `version` INT DEFAULT 1 COMMENT '乐观锁版本号',
        `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
        `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
        PRIMARY KEY (`id`),
        UNIQUE KEY `uniq_tasks_task_code` (`task_code`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='任务表';
    """,
    """
    CREATE TABLE IF NOT EXISTS `teams` (
        `id` INT NOT NULL AUTO_INCREMENT COMMENT '团队ID',
        `team_name` VARCHAR(100) NOT NULL COMMENT '团队名称',
        `team_code` VARCHAR(50) DEFAULT NULL COMMENT '团队编码',
        `description` TEXT COMMENT '团队描述',
        `leader_id` INT DEFAULT NULL COMMENT '团队负责人ID',
        `parent_team_id` INT DEFAULT NULL COMMENT '上级团队ID',
        `status` TINYINT DEFAULT 1 COMMENT '状态：0禁用 1启用',
        `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
        `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
        PRIMARY KEY (`id`),
        UNIQUE KEY `uniq_teams_team_code` (`team_code`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='团队表';
    """,
    """
    CREATE TABLE IF NOT EXISTS `project_members` (
        `id` INT NOT NULL AUTO_INCREMENT COMMENT 'ID',
        `project_id` INT NOT NULL COMMENT '项目ID',
        `user_id` INT NOT NULL COMMENT '用户ID',
        `role` VARCHAR(50) DEFAULT 'member' COMMENT '项目内角色：pm/member/viewer/qa/dev',
        `role_template_id` INT DEFAULT NULL COMMENT '项目角色模板ID',
        `join_date` DATE DEFAULT NULL COMMENT '加入日期',
        `status` VARCHAR(20) DEFAULT 'pending' COMMENT '状态：pending/accepted/left',
        `workload_rate` DECIMAL(5,2) DEFAULT 100 COMMENT '负载率 0-100',
        `invited_by` INT DEFAULT NULL COMMENT '邀请人ID',
        `invited_at` DATETIME DEFAULT NULL COMMENT '邀请时间',
        `accepted_at` DATETIME DEFAULT NULL COMMENT '接受邀请时间',
        `left_at` DATETIME DEFAULT NULL COMMENT '退出项目时间',
        `note` VARCHAR(500) DEFAULT NULL COMMENT '成员备注',
        `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
        `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
        PRIMARY KEY (`id`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='项目成员关联表';
    """,
    """
    CREATE TABLE IF NOT EXISTS `daily_reports` (
        `id` INT NOT NULL AUTO_INCREMENT COMMENT '日报ID',
        `report_date` DATE NOT NULL COMMENT '日报日期',
        `user_id` INT DEFAULT NULL COMMENT '生成用户ID',
        `project_id` INT DEFAULT NULL COMMENT '关联项目ID',
        `report_type` VARCHAR(50) DEFAULT 'daily' COMMENT '报表类型：daily/weekly/project/global',
        `period_start` DATE DEFAULT NULL COMMENT '统计周期开始日期',
        `period_end` DATE DEFAULT NULL COMMENT '统计周期结束日期',
        `generated_by` VARCHAR(50) DEFAULT 'ai' COMMENT '生成来源：ai/manual/system',
        `summary` TEXT COMMENT 'AI生成的摘要',
        `key_highlights` TEXT COMMENT '关键进展',
        `risk_alerts` TEXT COMMENT '风险提示',
        `suggestions` TEXT COMMENT 'AI建议',
        `metrics_json` TEXT COMMENT '报表指标数据（JSON）',
        `source_data_json` TEXT COMMENT '报表来源数据快照（JSON）',
        `confidence_score` DECIMAL(5,2) DEFAULT NULL COMMENT '置信度评分',
        `status` VARCHAR(20) DEFAULT 'draft' COMMENT '状态：draft/published',
        `published_at` DATETIME DEFAULT NULL COMMENT '发布时间',
        `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
        `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
        PRIMARY KEY (`id`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='AI日报表';
    """,
    """
    CREATE TABLE IF NOT EXISTS `documents` (
        `id` INT NOT NULL AUTO_INCREMENT COMMENT '文档ID',
        `doc_code` VARCHAR(50) DEFAULT NULL COMMENT '文档编码',
        `doc_name` VARCHAR(200) NOT NULL COMMENT '文档名称',
        `doc_type` VARCHAR(50) DEFAULT NULL COMMENT '文档类型',
        `status` VARCHAR(20) DEFAULT 'active' COMMENT '状态：active/archived/deleted',
        `file_path` VARCHAR(500) DEFAULT NULL COMMENT '文件存储路径',
        `file_size` BIGINT DEFAULT NULL COMMENT '文件大小',
        `mime_type` VARCHAR(100) DEFAULT NULL COMMENT '文件MIME类型',
        `project_id` INT DEFAULT NULL COMMENT '关联项目ID',
        `uploader_id` INT DEFAULT NULL COMMENT '上传人ID',
        `version` VARCHAR(20) DEFAULT '1.0' COMMENT '版本号',
        `latest_version` INT DEFAULT 1 COMMENT '最新版本序号',
        `description` TEXT COMMENT '文档描述',
        `summary` TEXT COMMENT 'AI文档摘要',
        `tags_json` TEXT COMMENT '标签数据（JSON）',
        `download_count` INT DEFAULT 0 COMMENT '下载次数',
        `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
        `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
        PRIMARY KEY (`id`),
        UNIQUE KEY `uniq_documents_doc_code` (`doc_code`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='文档表';
    """,
    """
    CREATE TABLE IF NOT EXISTS `notifications` (
        `id` INT NOT NULL AUTO_INCREMENT COMMENT '通知ID',
        `user_id` INT NOT NULL COMMENT '接收用户ID',
        `title` VARCHAR(200) DEFAULT NULL COMMENT '通知标题',
        `content` TEXT COMMENT '通知内容',
        `type` VARCHAR(50) DEFAULT NULL COMMENT '类型：task_reminder/project_update/system_alert/risk_alert',
        `category` VARCHAR(50) DEFAULT NULL COMMENT '通知分类：pending/system/ai/other',
        `status` VARCHAR(50) DEFAULT 'pending' COMMENT '通知状态：pending/high_priority/completed/ai_reminder',
        `priority` VARCHAR(20) DEFAULT 'P2' COMMENT '优先级：P0/P1/P2/P3',
        `source_module` VARCHAR(50) DEFAULT NULL COMMENT '来源模块：admin/project/workbench/system',
        `related_id` INT DEFAULT NULL COMMENT '关联ID（任务/项目等）',
        `related_type` VARCHAR(50) DEFAULT NULL COMMENT '关联类型：task/project/risk',
        `action_label` VARCHAR(100) DEFAULT NULL COMMENT '操作按钮文案',
        `action_path` VARCHAR(200) DEFAULT NULL COMMENT '操作跳转路径',
        `action_type` VARCHAR(50) DEFAULT NULL COMMENT '操作类型：view/handle/apply/export',
        `tags_json` TEXT COMMENT '标签数据（JSON）',
        `metadata_json` TEXT COMMENT '扩展数据（JSON）',
        `is_read` TINYINT DEFAULT 0 COMMENT '是否已读',
        `read_at` DATETIME DEFAULT NULL COMMENT '阅读时间',
        `handled` TINYINT DEFAULT 0 COMMENT '是否已处理',
        `handled_at` DATETIME DEFAULT NULL COMMENT '处理时间',
        `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
        `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
        PRIMARY KEY (`id`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='通知表';
    """,
    """
    CREATE TABLE IF NOT EXISTS `system_settings` (
        `id` INT NOT NULL AUTO_INCREMENT COMMENT '设置ID',
        `setting_key` VARCHAR(100) NOT NULL COMMENT '设置键',
        `setting_value` TEXT COMMENT '设置值',
        `setting_type` VARCHAR(50) DEFAULT 'string' COMMENT '类型：string/json/boolean/number',
        `value_schema` TEXT COMMENT '配置值结构说明（JSON Schema或前端控件配置）',
        `description` VARCHAR(200) DEFAULT NULL COMMENT '设置描述',
        `group_name` VARCHAR(50) DEFAULT NULL COMMENT '设置分组',
        `version` INT DEFAULT 1 COMMENT '配置版本号',
        `updated_by` INT DEFAULT NULL COMMENT '最近更新人ID',
        `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
        `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
        PRIMARY KEY (`id`),
        UNIQUE KEY `uniq_system_settings_setting_key` (`setting_key`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='系统设置表';
    """,
    """
    CREATE TABLE IF NOT EXISTS `operation_logs` (
        `id` INT NOT NULL AUTO_INCREMENT COMMENT '日志ID',
        `user_id` INT DEFAULT NULL COMMENT '操作用户ID',
        `action` VARCHAR(100) DEFAULT NULL COMMENT '操作动作',
        `action_key` VARCHAR(100) DEFAULT NULL COMMENT '动作Key：delete_template/update_system_config',
        `target_type` VARCHAR(50) DEFAULT NULL COMMENT '目标类型：task/project/document/user',
        `target_id` INT DEFAULT NULL COMMENT '目标ID',
        `target_ref` VARCHAR(100) DEFAULT NULL COMMENT '目标业务ID或字符串ID',
        `target_name` VARCHAR(200) DEFAULT NULL COMMENT '目标名称',
        `detail` TEXT COMMENT '操作详情',
        `result` VARCHAR(20) DEFAULT NULL COMMENT '执行结果：success/failed',
        `risk_level` VARCHAR(20) DEFAULT 'low' COMMENT '风险等级：low/medium/high',
        `request_id` VARCHAR(100) DEFAULT NULL COMMENT '请求链路ID',
        `module` VARCHAR(50) DEFAULT NULL COMMENT '所属模块：admin/project/task/system',
        `ip_address` VARCHAR(50) DEFAULT NULL COMMENT 'IP地址',
        `user_agent` VARCHAR(500) DEFAULT NULL COMMENT '浏览器信息',
        `metadata_json` TEXT COMMENT '扩展数据（JSON）',
        `occurred_at` DATETIME DEFAULT NULL COMMENT '实际发生时间',
        `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
        PRIMARY KEY (`id`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='操作日志表';
    """,
    """
    CREATE TABLE IF NOT EXISTS `pbc_objectives` (
        `id` INT NOT NULL AUTO_INCREMENT COMMENT '目标ID',
        `objective_code` VARCHAR(50) DEFAULT NULL COMMENT '目标编码',
        `objective_name` VARCHAR(200) NOT NULL COMMENT '目标名称',
        `description` TEXT COMMENT '目标描述',
        `quarter` VARCHAR(10) DEFAULT NULL COMMENT '季度：2024-Q1',
        `weight` DECIMAL(5,2) DEFAULT NULL COMMENT '权重',
        `target_value` DECIMAL(10,2) DEFAULT NULL COMMENT '目标值',
        `actual_value` DECIMAL(10,2) DEFAULT NULL COMMENT '实际值',
        `achievement_rate` DECIMAL(5,2) DEFAULT NULL COMMENT '达成率',
        `status` VARCHAR(20) DEFAULT 'active' COMMENT '状态',
        `user_id` INT DEFAULT NULL COMMENT '关联用户ID',
        `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
        `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
        PRIMARY KEY (`id`),
        UNIQUE KEY `uniq_pbc_objectives_objective_code` (`objective_code`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='PBC目标表';
    """,
    """
    CREATE TABLE IF NOT EXISTS `milestones` (
        `id` INT NOT NULL AUTO_INCREMENT COMMENT '里程碑ID',
        `milestone_name` VARCHAR(200) NOT NULL COMMENT '里程碑名称',
        `project_id` INT NOT NULL COMMENT '所属项目ID',
        `description` TEXT COMMENT '里程碑描述',
        `owner_id` INT DEFAULT NULL COMMENT '负责人ID',
        `due_date` DATE DEFAULT NULL COMMENT '计划日期',
        `completion_date` DATE DEFAULT NULL COMMENT '实际完成日期',
        `status` VARCHAR(20) DEFAULT 'pending' COMMENT '状态：pending/in_progress/completed/delayed',
        `sort_order` INT DEFAULT 0 COMMENT '排序值',
        `baseline_date` DATE DEFAULT NULL COMMENT '基线日期',
        `delay_days` INT DEFAULT 0 COMMENT '延后天数',
        `variance_days` DECIMAL(5,2) DEFAULT 0 COMMENT '偏差天数（精确到小时）',
        `progress` DECIMAL(5,2) DEFAULT 0 COMMENT '进度百分比 0-100',
        `version` INT DEFAULT 1 COMMENT '乐观锁版本号',
        `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
        `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
        PRIMARY KEY (`id`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='里程碑表';
    """,
    """
    CREATE TABLE IF NOT EXISTS `risks` (
        `id` INT NOT NULL AUTO_INCREMENT COMMENT '风险ID',
        `risk_code` VARCHAR(50) DEFAULT NULL COMMENT '风险编码',
        `project_id` INT NOT NULL COMMENT '所属项目ID',
        `risk_title` VARCHAR(200) NOT NULL COMMENT '风险标题',
        `risk_level` VARCHAR(20) DEFAULT 'medium' COMMENT '风险等级：low/medium/high/critical',
        `risk_factor` VARCHAR(100) DEFAULT NULL COMMENT '风险因子',
        `confidence_score` DECIMAL(5,2) DEFAULT NULL COMMENT '置信度评分',
        `ai_analysis` TEXT COMMENT 'AI深度分析',
        `mitigation_plan` TEXT COMMENT '缓解方案',
        `status` VARCHAR(20) DEFAULT 'active' COMMENT '状态：active/resolved/closed',
        `assignee_id` INT DEFAULT NULL COMMENT '负责人ID',
        `due_date` DATE DEFAULT NULL COMMENT '处理截止日期',
        `resolved_at` DATETIME DEFAULT NULL COMMENT '解决时间',
        `progress_blocked` DECIMAL(5,2) DEFAULT 0 COMMENT '进度阻碍百分比',
        `task_ids` VARCHAR(500) DEFAULT NULL COMMENT '关联任务ID列表，JSON格式',
        `related_task_ids_json` TEXT COMMENT '关联任务ID数组（JSON）',
        `version` INT DEFAULT 1 COMMENT '乐观锁版本号',
        `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
        `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
        PRIMARY KEY (`id`),
        UNIQUE KEY `uniq_risks_risk_code` (`risk_code`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='风险表';
    """,
    """
    CREATE TABLE IF NOT EXISTS `roles_permissions` (
        `id` INT NOT NULL AUTO_INCREMENT COMMENT 'ID',
        `role_code` VARCHAR(50) NOT NULL COMMENT '角色编码',
        `role_name` VARCHAR(100) DEFAULT NULL COMMENT '角色名称',
        `permission_key` VARCHAR(100) NOT NULL COMMENT '权限键',
        `permission_label` VARCHAR(100) DEFAULT NULL COMMENT '权限名称',
        `permission_type` VARCHAR(50) DEFAULT NULL COMMENT '权限类型：page/action/data',
        `resource_key` VARCHAR(100) DEFAULT NULL COMMENT '资源Key：页面、模块或动作分组',
        `allowed` TINYINT DEFAULT 1 COMMENT '是否允许：0禁止 1允许',
        `scope` VARCHAR(50) DEFAULT NULL COMMENT '权限范围：self/all/project',
        `status` VARCHAR(20) DEFAULT 'active' COMMENT '状态：active/disabled',
        `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
        `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
        PRIMARY KEY (`id`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='角色权限表';
    """,
    """
    CREATE TABLE IF NOT EXISTS `system_metrics` (
        `id` INT NOT NULL AUTO_INCREMENT COMMENT '监控ID',
        `metric_type` VARCHAR(50) DEFAULT NULL COMMENT '指标类型：environment/compute/security/project',
        `metric_name` VARCHAR(100) DEFAULT NULL COMMENT '指标名称',
        `metric_value` DECIMAL(15,4) DEFAULT NULL COMMENT '指标值',
        `unit` VARCHAR(20) DEFAULT NULL COMMENT '单位',
        `status` VARCHAR(20) DEFAULT 'normal' COMMENT '状态：normal/warning/critical',
        `threshold_low` DECIMAL(15,4) DEFAULT NULL COMMENT '下限阈值',
        `threshold_high` DECIMAL(15,4) DEFAULT NULL COMMENT '上限阈值',
        `project_id` INT DEFAULT NULL COMMENT '关联项目ID（可选）',
        `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
        PRIMARY KEY (`id`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='系统监控表';
    """,
    """
    CREATE TABLE IF NOT EXISTS `task_dependencies` (
        `id` INT NOT NULL AUTO_INCREMENT COMMENT 'ID',
        `task_id` INT NOT NULL COMMENT '任务ID',
        `depends_on_task_id` INT DEFAULT NULL COMMENT '依赖任务ID',
        `dependency_type` VARCHAR(20) DEFAULT 'finish_to_start' COMMENT '依赖类型：finish_to_start/start_to_start',
        `lag_days` INT DEFAULT 0 COMMENT '延迟天数',
        `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
        PRIMARY KEY (`id`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='任务依赖表';
    """,
    """
    CREATE TABLE IF NOT EXISTS `baseline_versions` (
        `id` INT NOT NULL AUTO_INCREMENT COMMENT '基线ID',
        `project_id` INT NOT NULL COMMENT '所属项目ID',
        `version_name` VARCHAR(20) DEFAULT NULL COMMENT '版本名称：V1/V2',
        `baseline_data` TEXT COMMENT '基线数据（JSON格式）',
        `created_by` INT DEFAULT NULL COMMENT '创建人ID',
        `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
        PRIMARY KEY (`id`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='基线版本表';
    """,
    """
    CREATE TABLE IF NOT EXISTS `compute_requests` (
        `id` INT NOT NULL AUTO_INCREMENT COMMENT '申请ID',
        `request_code` VARCHAR(50) DEFAULT NULL COMMENT '申请编码',
        `project_id` INT DEFAULT NULL COMMENT '关联项目ID',
        `applicant_id` INT NOT NULL COMMENT '申请人ID',
        `resource_type` VARCHAR(50) DEFAULT NULL COMMENT '资源类型：GPU/CPU/Memory',
        `resource_spec` VARCHAR(100) DEFAULT NULL COMMENT '资源规格',
        `request_hours` INT DEFAULT NULL COMMENT '申请时长（小时）',
        `scheduled_date` DATE DEFAULT NULL COMMENT '计划使用日期',
        `status` VARCHAR(20) DEFAULT 'pending' COMMENT '状态：pending/approved/rejected',
        `approver_id` INT DEFAULT NULL COMMENT '审批人ID',
        `approved_at` DATETIME DEFAULT NULL COMMENT '审批时间',
        `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
        `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
        PRIMARY KEY (`id`),
        UNIQUE KEY `uniq_compute_requests_request_code` (`request_code`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='算力申请表';
    """,
    """
    CREATE TABLE IF NOT EXISTS `user_workload` (
        `id` INT NOT NULL AUTO_INCREMENT COMMENT '记录ID',
        `user_id` INT NOT NULL COMMENT '用户ID',
        `project_id` INT DEFAULT NULL COMMENT '项目ID',
        `date` DATE NOT NULL COMMENT '日期',
        `workload_percent` DECIMAL(5,2) DEFAULT NULL COMMENT '负载百分比',
        `task_count` INT DEFAULT 0 COMMENT '任务数量',
        `estimated_hours` DECIMAL(10,2) DEFAULT NULL COMMENT '预估工时',
        `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
        `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
        PRIMARY KEY (`id`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户负载记录表';
    """,
    """
    CREATE TABLE IF NOT EXISTS `task_comments` (
        `id` INT NOT NULL AUTO_INCREMENT COMMENT '评论ID',
        `task_id` INT NOT NULL COMMENT '任务ID',
        `user_id` INT NOT NULL COMMENT '评论用户ID',
        `parent_comment_id` INT DEFAULT NULL COMMENT '父评论ID（支持回复）',
        `content` TEXT NOT NULL COMMENT '评论内容',
        `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
        `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
        PRIMARY KEY (`id`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='任务评论表';
    """,
    """
    CREATE TABLE IF NOT EXISTS `project_templates` (
        `id` INT NOT NULL AUTO_INCREMENT COMMENT '模板ID',
        `template_code` VARCHAR(50) DEFAULT NULL COMMENT '模板编码',
        `template_name` VARCHAR(100) NOT NULL COMMENT '模板名称',
        `description` TEXT COMMENT '模板描述',
        `milestone_count` INT DEFAULT 0 COMMENT '默认里程碑数',
        `default_stage_flow` TEXT COMMENT '默认阶段流转（JSON）',
        `enabled_pages_json` TEXT COMMENT '启用页面列表（JSON数组）',
        `milestones_json` TEXT COMMENT '里程碑明细（JSON数组）',
        `default_role_template_ids_json` TEXT COMMENT '默认角色模板ID列表（JSON数组）',
        `used_project_count` INT DEFAULT 0 COMMENT '已使用项目数量',
        `is_builtin` TINYINT DEFAULT 0 COMMENT '是否内置模板',
        `version` INT DEFAULT 1 COMMENT '乐观锁版本号',
        `status` VARCHAR(20) DEFAULT 'active' COMMENT '状态：active/disabled',
        `created_by` INT DEFAULT NULL COMMENT '创建人ID',
        `updated_by` INT DEFAULT NULL COMMENT '最近更新人ID',
        `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
        `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
        PRIMARY KEY (`id`),
        UNIQUE KEY `uniq_project_templates_template_code` (`template_code`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='项目模板表';
    """,
    """
    CREATE TABLE IF NOT EXISTS `role_templates` (
        `id` INT NOT NULL AUTO_INCREMENT COMMENT '模板ID',
        `template_key` VARCHAR(50) NOT NULL COMMENT '模板键：pm/dev/qa/collab',
        `template_name` VARCHAR(100) NOT NULL COMMENT '模板名称',
        `scope` VARCHAR(50) DEFAULT 'project' COMMENT '适用范围：project/platform',
        `description` TEXT COMMENT '模板说明',
        `visible_pages_json` TEXT COMMENT '页面可见性（JSON数组）',
        `action_permissions_json` TEXT COMMENT '操作权限（JSON数组）',
        `default_role_code` VARCHAR(50) DEFAULT NULL COMMENT '关联角色编码',
        `is_builtin` TINYINT DEFAULT 0 COMMENT '是否内置模板',
        `version` INT DEFAULT 1 COMMENT '乐观锁版本号',
        `reference_count` INT DEFAULT 0 COMMENT '引用项目/用户数量',
        `status` VARCHAR(20) DEFAULT 'active' COMMENT '状态：active/disabled',
        `created_by` INT DEFAULT NULL COMMENT '创建人ID',
        `updated_by` INT DEFAULT NULL COMMENT '最近更新人ID',
        `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
        `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
        PRIMARY KEY (`id`),
        UNIQUE KEY `uniq_role_templates_template_key` (`template_key`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='角色模板表';
    """,
    """
    CREATE TABLE IF NOT EXISTS `user_sessions` (
        `id` INT NOT NULL AUTO_INCREMENT COMMENT '会话ID',
        `session_id` VARCHAR(100) NOT NULL COMMENT '业务会话ID',
        `user_id` INT NOT NULL COMMENT '用户ID',
        `access_token` TEXT COMMENT '访问令牌',
        `refresh_token` TEXT COMMENT '刷新令牌',
        `access_expires_at` DATETIME DEFAULT NULL COMMENT '访问令牌过期时间',
        `refresh_expires_at` DATETIME DEFAULT NULL COMMENT '刷新令牌过期时间',
        `device_name` VARCHAR(200) DEFAULT NULL COMMENT '设备名称',
        `ip_address` VARCHAR(50) DEFAULT NULL COMMENT 'IP地址',
        `location` VARCHAR(100) DEFAULT NULL COMMENT '地理位置',
        `user_agent` VARCHAR(500) DEFAULT NULL COMMENT '浏览器信息',
        `is_current` TINYINT DEFAULT 0 COMMENT '是否当前会话',
        `status` VARCHAR(20) DEFAULT 'active' COMMENT '状态：active/revoked/expired',
        `last_active_at` DATETIME DEFAULT NULL COMMENT '最近活跃时间',
        `revoked_at` DATETIME DEFAULT NULL COMMENT '下线时间',
        `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
        `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
        PRIMARY KEY (`id`),
        UNIQUE KEY `uniq_user_sessions_session_id` (`session_id`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户设备会话表';
    """,
    """
    CREATE TABLE IF NOT EXISTS `user_settings` (
        `id` INT NOT NULL AUTO_INCREMENT COMMENT '用户设置ID',
        `user_id` INT NOT NULL COMMENT '用户ID',
        `section_key` VARCHAR(50) NOT NULL COMMENT '设置分组：profile/notification/security/ai',
        `setting_key` VARCHAR(100) NOT NULL COMMENT '设置键',
        `setting_value` TEXT COMMENT '设置值',
        `setting_type` VARCHAR(50) DEFAULT 'json' COMMENT '类型：string/json/boolean/number',
        `version` INT DEFAULT 1 COMMENT '乐观锁版本号',
        `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
        `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
        PRIMARY KEY (`id`),
        UNIQUE KEY `uniq_user_settings_user_key` (`user_id`, `section_key`, `setting_key`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户个性化设置表';
    """,
    """
    CREATE TABLE IF NOT EXISTS `notification_preferences` (
        `id` INT NOT NULL AUTO_INCREMENT COMMENT '通知偏好ID',
        `user_id` INT NOT NULL COMMENT '用户ID',
        `channel` VARCHAR(50) NOT NULL COMMENT '通道：in_app/email/wecom',
        `category` VARCHAR(50) NOT NULL COMMENT '分类：task/report/system/ai',
        `enabled` TINYINT DEFAULT 1 COMMENT '是否启用',
        `quiet_hours_json` TEXT COMMENT '免打扰时间配置（JSON）',
        `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
        `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
        PRIMARY KEY (`id`),
        UNIQUE KEY `uniq_notification_preferences_user_channel_category` (`user_id`, `channel`, `category`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户通知偏好表';
    """,
    """
    CREATE TABLE IF NOT EXISTS `async_jobs` (
        `id` INT NOT NULL AUTO_INCREMENT COMMENT '异步任务ID',
        `job_id` VARCHAR(100) NOT NULL COMMENT '业务任务ID',
        `job_type` VARCHAR(50) NOT NULL COMMENT '任务类型：export/import/report/ai_apply',
        `source_module` VARCHAR(50) DEFAULT NULL COMMENT '来源模块',
        `status` VARCHAR(20) DEFAULT 'pending' COMMENT '状态：pending/running/success/failed',
        `file_name` VARCHAR(200) DEFAULT NULL COMMENT '文件名',
        `download_url` VARCHAR(500) DEFAULT NULL COMMENT '下载地址',
        `request_payload_json` TEXT COMMENT '请求参数快照（JSON）',
        `result_json` TEXT COMMENT '执行结果（JSON）',
        `error_message` TEXT COMMENT '错误信息',
        `created_by` INT DEFAULT NULL COMMENT '创建人ID',
        `started_at` DATETIME DEFAULT NULL COMMENT '开始时间',
        `finished_at` DATETIME DEFAULT NULL COMMENT '结束时间',
        `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
        `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
        PRIMARY KEY (`id`),
        UNIQUE KEY `uniq_async_jobs_job_id` (`job_id`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='异步导入导出和生成任务表';
    """,
    """
    CREATE TABLE IF NOT EXISTS `ai_suggestion_logs` (
        `id` INT NOT NULL AUTO_INCREMENT COMMENT 'AI建议记录ID',
        `suggestion_id` VARCHAR(100) NOT NULL COMMENT '建议ID',
        `scope` VARCHAR(50) DEFAULT NULL COMMENT '建议范围：admin/project/task/report/settings',
        `target_type` VARCHAR(50) DEFAULT NULL COMMENT '目标类型',
        `target_id` VARCHAR(100) DEFAULT NULL COMMENT '目标业务ID',
        `title` VARCHAR(200) DEFAULT NULL COMMENT '建议标题',
        `summary` TEXT COMMENT '建议摘要',
        `confidence` DECIMAL(5,2) DEFAULT NULL COMMENT '置信度',
        `action_key` VARCHAR(100) DEFAULT NULL COMMENT '建议动作',
        `status` VARCHAR(20) DEFAULT 'generated' COMMENT '状态：generated/applied/deferred/dismissed',
        `payload_json` TEXT COMMENT '建议原始数据（JSON）',
        `applied_by` INT DEFAULT NULL COMMENT '采纳人ID',
        `applied_at` DATETIME DEFAULT NULL COMMENT '采纳时间',
        `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
        `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
        PRIMARY KEY (`id`),
        UNIQUE KEY `uniq_ai_suggestion_logs_suggestion_id` (`suggestion_id`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='AI建议生成和采纳记录表';
    """,
    """
    CREATE TABLE IF NOT EXISTS `system_setting_history` (
        `id` INT NOT NULL AUTO_INCREMENT COMMENT '配置历史ID',
        `history_id` VARCHAR(100) DEFAULT NULL COMMENT '业务历史ID',
        `setting_key` VARCHAR(100) DEFAULT NULL COMMENT '配置键',
        `group_name` VARCHAR(50) DEFAULT NULL COMMENT '配置分组',
        `before_value` TEXT COMMENT '修改前值',
        `after_value` TEXT COMMENT '修改后值',
        `changed_keys_json` TEXT COMMENT '变更配置键列表（JSON数组）',
        `version` INT DEFAULT NULL COMMENT '配置版本号',
        `operator_id` INT DEFAULT NULL COMMENT '操作人ID',
        `operation_type` VARCHAR(50) DEFAULT NULL COMMENT '操作类型：save/reset/import',
        `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
        PRIMARY KEY (`id`),
        UNIQUE KEY `uniq_system_setting_history_history_id` (`history_id`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='系统配置变更历史表';
    """,
    """
    CREATE TABLE IF NOT EXISTS `document_versions` (
        `id` INT NOT NULL AUTO_INCREMENT COMMENT '文档版本ID',
        `document_id` INT NOT NULL COMMENT '文档ID',
        `version_no` INT NOT NULL COMMENT '版本序号',
        `version_name` VARCHAR(50) DEFAULT NULL COMMENT '版本名称：v1/v2',
        `file_path` VARCHAR(500) DEFAULT NULL COMMENT '版本文件路径',
        `file_size` BIGINT DEFAULT NULL COMMENT '版本文件大小',
        `summary` TEXT COMMENT '版本说明或AI摘要',
        `created_by` INT DEFAULT NULL COMMENT '创建人ID',
        `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
        PRIMARY KEY (`id`),
        UNIQUE KEY `uniq_document_versions_doc_version` (`document_id`, `version_no`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='文档版本表';
    """,
    """
    CREATE TABLE IF NOT EXISTS `document_attachments` (
        `id` INT NOT NULL AUTO_INCREMENT COMMENT '附件ID',
        `document_id` INT NOT NULL COMMENT '文档ID',
        `file_name` VARCHAR(200) NOT NULL COMMENT '附件名称',
        `file_path` VARCHAR(500) DEFAULT NULL COMMENT '附件路径',
        `file_size` BIGINT DEFAULT NULL COMMENT '附件大小',
        `mime_type` VARCHAR(100) DEFAULT NULL COMMENT 'MIME类型',
        `uploaded_by` INT DEFAULT NULL COMMENT '上传人ID',
        `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
        PRIMARY KEY (`id`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='文档附件表';
    """,
    """
    CREATE TABLE IF NOT EXISTS `report_subscriptions` (
        `id` INT NOT NULL AUTO_INCREMENT COMMENT '报表订阅ID',
        `user_id` INT NOT NULL COMMENT '订阅用户ID',
        `project_id` INT DEFAULT NULL COMMENT '项目ID，空表示全局报表',
        `report_type` VARCHAR(50) DEFAULT 'weekly' COMMENT '报表类型：daily/weekly/monthly/global',
        `channel` VARCHAR(50) DEFAULT 'in_app' COMMENT '通知通道：in_app/email/wecom',
        `enabled` TINYINT DEFAULT 1 COMMENT '是否启用',
        `filters_json` TEXT COMMENT '订阅筛选条件（JSON）',
        `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
        `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
        PRIMARY KEY (`id`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='报表订阅表';
    """,
]

INDEX_DEFINITIONS = [
    ("users", "idx_users_username", "`username`"),
    ("users", "idx_users_email", "`email`"),
    ("users", "idx_users_status", "`status`"),
    ("users", "idx_users_role", "`role`"),
    ("users", "idx_users_join_date", "`join_date`"),
    ("users", "idx_users_department_id", "`department_id`"),
    ("projects", "idx_projects_pm", "`pm_id`"),
    ("projects", "idx_projects_status", "`status`"),
    ("projects", "idx_projects_team", "`team_id`"),
    ("projects", "idx_projects_end_date", "`end_date`"),
    ("projects", "idx_projects_template_id", "`project_template_id`"),
    ("tasks", "idx_tasks_project", "`project_id`"),
    ("tasks", "idx_tasks_assignee", "`assignee_id`"),
    ("tasks", "idx_tasks_status", "`status`"),
    ("tasks", "idx_tasks_column_order", "`project_id`, `column_key`, `sort_order`"),
    ("tasks", "idx_tasks_due_date", "`due_date`"),
    ("tasks", "idx_tasks_milestone", "`milestone_id`"),
    ("tasks", "idx_tasks_dependency", "`dependency_task_id`"),
    ("project_members", "idx_project_members_project", "`project_id`"),
    ("project_members", "idx_project_members_user", "`user_id`"),
    ("project_members", "idx_project_members_status", "`status`"),
    ("project_members", "idx_project_members_project_user", "`project_id`, `user_id`"),
    ("daily_reports", "idx_daily_reports_user_date", "`user_id`, `report_date`"),
    ("daily_reports", "idx_daily_reports_project_type", "`project_id`, `report_type`"),
    ("documents", "idx_documents_project", "`project_id`"),
    ("documents", "idx_documents_status", "`status`"),
    ("notifications", "idx_notifications_user_read", "`user_id`, `is_read`"),
    ("notifications", "idx_notifications_type", "`type`"),
    ("notifications", "idx_notifications_category", "`category`"),
    ("notifications", "idx_notifications_priority", "`priority`"),
    ("notifications", "idx_notifications_status", "`status`"),
    ("operation_logs", "idx_operation_logs_user", "`user_id`"),
    ("operation_logs", "idx_operation_logs_created", "`created_at`"),
    ("operation_logs", "idx_operation_logs_result", "`result`"),
    ("operation_logs", "idx_operation_logs_action_key", "`action_key`"),
    ("operation_logs", "idx_operation_logs_risk_level", "`risk_level`"),
    ("operation_logs", "idx_operation_logs_request", "`request_id`"),
    ("pbc_objectives", "idx_pbc_objectives_quarter", "`quarter`"),
    ("pbc_objectives", "idx_pbc_objectives_user", "`user_id`"),
    ("milestones", "idx_milestones_project", "`project_id`"),
    ("compute_requests", "idx_compute_requests_applicant", "`applicant_id`"),
    ("compute_requests", "idx_compute_requests_date", "`scheduled_date`"),
    ("risks", "idx_risks_project", "`project_id`"),
    ("risks", "idx_risks_level", "`risk_level`"),
    ("risks", "idx_risks_status", "`status`"),
    ("roles_permissions", "idx_roles_permissions_role", "`role_code`"),
    ("roles_permissions", "idx_roles_permissions_permission", "`permission_key`"),
    ("roles_permissions", "idx_roles_permissions_role_perm", "`role_code`, `permission_key`"),
    ("system_metrics", "idx_system_metrics_type", "`metric_type`"),
    ("system_metrics", "idx_system_metrics_created", "`created_at`"),
    ("task_dependencies", "idx_task_dependencies_task", "`task_id`"),
    ("task_dependencies", "idx_task_dependencies_depends", "`depends_on_task_id`"),
    ("baseline_versions", "idx_baseline_versions_project", "`project_id`"),
    ("user_workload", "idx_user_workload_user_date", "`user_id`, `date`"),
    ("task_comments", "idx_task_comments_task_created", "`task_id`, `created_at`"),
    ("task_comments", "idx_task_comments_user", "`user_id`"),
    ("project_templates", "idx_project_templates_code", "`template_code`"),
    ("project_templates", "idx_project_templates_status", "`status`"),
    ("role_templates", "idx_role_templates_key", "`template_key`"),
    ("role_templates", "idx_role_templates_status", "`status`"),
    ("user_sessions", "idx_user_sessions_user_status", "`user_id`, `status`"),
    ("user_sessions", "idx_user_sessions_last_active", "`last_active_at`"),
    ("user_settings", "idx_user_settings_user_section", "`user_id`, `section_key`"),
    ("notification_preferences", "idx_notification_preferences_user", "`user_id`"),
    ("async_jobs", "idx_async_jobs_type_status", "`job_type`, `status`"),
    ("async_jobs", "idx_async_jobs_created_by", "`created_by`"),
    ("ai_suggestion_logs", "idx_ai_suggestion_logs_scope_status", "`scope`, `status`"),
    ("ai_suggestion_logs", "idx_ai_suggestion_logs_target", "`target_type`, `target_id`"),
    ("system_setting_history", "idx_system_setting_history_key_created", "`setting_key`, `created_at`"),
    ("system_setting_history", "idx_system_setting_history_operator", "`operator_id`"),
    ("document_versions", "idx_document_versions_document", "`document_id`"),
    ("document_attachments", "idx_document_attachments_document", "`document_id`"),
    ("report_subscriptions", "idx_report_subscriptions_user", "`user_id`"),
    ("report_subscriptions", "idx_report_subscriptions_project", "`project_id`"),
]


def _index_exists(cursor, database_name: str, table_name: str, index_name: str) -> bool:
    cursor.execute(
        """
        SELECT 1
        FROM information_schema.statistics
        WHERE table_schema = %s AND table_name = %s AND index_name = %s
        LIMIT 1
        """,
        (database_name, table_name, index_name),
    )
    return cursor.fetchone() is not None


def _column_exists(cursor, database_name: str, table_name: str, column_name: str) -> bool:
    cursor.execute(
        """
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = %s AND table_name = %s AND column_name = %s
        LIMIT 1
        """,
        (database_name, table_name, column_name),
    )
    return cursor.fetchone() is not None


def _create_index_if_not_exists(cursor, database_name: str, table_name: str, index_name: str, columns: str) -> bool:
    if _index_exists(cursor, database_name, table_name, index_name):
        return False
    cursor.execute(f"CREATE INDEX `{index_name}` ON `{table_name}` ({columns})")
    return True


def setup_database() -> None:
    """按 database_schema.txt 初始化数据库表结构和索引。"""
    conn = None
    database_name = settings.MYSQL_DATABASE or "rd_system"

    try:
        conn = pymysql.connect(
            host=settings.MYSQL_HOST,
            port=settings.MYSQL_PORT,
            user=settings.MYSQL_USER,
            password=settings.MYSQL_PASSWORD,
            charset="utf8mb4",
        )

        cursor = conn.cursor()
        cursor.execute(
            f"CREATE DATABASE IF NOT EXISTS `{database_name}` "
            "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        )
        cursor.execute(f"USE `{database_name}`")

        for table_sql in TABLE_SQL:
            cursor.execute(table_sql)

        columns_to_add = [
            ("users", "department_id", "VARCHAR(50) DEFAULT NULL COMMENT '部门ID（兼容前端 departmentId）'"),
            ("users", "join_date", "DATE DEFAULT NULL COMMENT '加入日期'"),
            ("users", "last_login_ip", "VARCHAR(50) DEFAULT NULL COMMENT '最后登录IP'"),
            ("users", "password_updated_at", "DATETIME DEFAULT NULL COMMENT '密码最近修改时间'"),
            ("users", "failed_login_count", "INT DEFAULT 0 COMMENT '连续登录失败次数'"),
            ("users", "locked_until", "DATETIME DEFAULT NULL COMMENT '账号锁定到期时间'"),
            ("users", "version", "INT DEFAULT 1 COMMENT '乐观锁版本号'"),
            ("projects", "pm_id", "INT DEFAULT NULL COMMENT '项目经理ID'"),
            ("projects", "team_id", "INT DEFAULT NULL COMMENT '归属团队ID'"),
            ("projects", "project_template_id", "INT DEFAULT NULL COMMENT '项目模板ID'"),
            ("tasks", "assignee_id", "INT DEFAULT NULL COMMENT '负责人ID'"),
            ("tasks", "milestone_id", "INT DEFAULT NULL COMMENT '关联里程碑ID'"),
            ("tasks", "dependency_task_id", "INT DEFAULT NULL COMMENT '主依赖任务ID'"),
            ("tasks", "column_key", "VARCHAR(50) DEFAULT NULL COMMENT '看板列Key'"),
            ("tasks", "sort_order", "DECIMAL(12,4) DEFAULT 0 COMMENT '看板/列表排序值'"),
            ("tasks", "status_changed_at", "DATETIME DEFAULT NULL COMMENT '任务状态最近变更时间'"),
            ("tasks", "version", "INT DEFAULT 1 COMMENT '乐观锁版本号'"),
            ("project_members", "user_id", "INT NOT NULL COMMENT '用户ID'"),
            ("project_members", "role_template_id", "INT DEFAULT NULL COMMENT '项目角色模板ID'"),
            ("project_members", "invited_by", "INT DEFAULT NULL COMMENT '邀请人ID'"),
            ("project_members", "invited_at", "DATETIME DEFAULT NULL COMMENT '邀请时间'"),
            ("project_members", "accepted_at", "DATETIME DEFAULT NULL COMMENT '接受邀请时间'"),
            ("project_members", "left_at", "DATETIME DEFAULT NULL COMMENT '退出项目时间'"),
            ("project_members", "note", "VARCHAR(500) DEFAULT NULL COMMENT '成员备注'"),
            ("daily_reports", "report_date", "DATE NOT NULL COMMENT '日报日期'"),
            ("daily_reports", "report_type", "VARCHAR(50) DEFAULT 'daily' COMMENT '报表类型'"),
            ("daily_reports", "period_start", "DATE DEFAULT NULL COMMENT '统计周期开始日期'"),
            ("daily_reports", "period_end", "DATE DEFAULT NULL COMMENT '统计周期结束日期'"),
            ("daily_reports", "generated_by", "VARCHAR(50) DEFAULT 'ai' COMMENT '生成来源'"),
            ("daily_reports", "metrics_json", "TEXT COMMENT '报表指标数据（JSON）'"),
            ("daily_reports", "source_data_json", "TEXT COMMENT '报表来源数据快照（JSON）'"),
            ("documents", "status", "VARCHAR(20) DEFAULT 'active' COMMENT '状态'"),
            ("documents", "mime_type", "VARCHAR(100) DEFAULT NULL COMMENT '文件MIME类型'"),
            ("documents", "latest_version", "INT DEFAULT 1 COMMENT '最新版本序号'"),
            ("documents", "summary", "TEXT COMMENT 'AI文档摘要'"),
            ("documents", "tags_json", "TEXT COMMENT '标签数据（JSON）'"),
            ("documents", "download_count", "INT DEFAULT 0 COMMENT '下载次数'"),
            ("notifications", "is_read", "TINYINT DEFAULT 0 COMMENT '是否已读'"),
            ("notifications", "type", "VARCHAR(50) DEFAULT NULL COMMENT '类型'"),
            ("notifications", "category", "VARCHAR(50) DEFAULT NULL COMMENT '通知分类'"),
            ("notifications", "status", "VARCHAR(50) DEFAULT 'pending' COMMENT '通知状态'"),
            ("notifications", "priority", "VARCHAR(20) DEFAULT 'P2' COMMENT '优先级'"),
            ("notifications", "source_module", "VARCHAR(50) DEFAULT NULL COMMENT '来源模块'"),
            ("notifications", "action_type", "VARCHAR(50) DEFAULT NULL COMMENT '操作类型'"),
            ("notifications", "metadata_json", "TEXT COMMENT '扩展数据（JSON）'"),
            ("notifications", "handled", "TINYINT DEFAULT 0 COMMENT '是否已处理'"),
            ("notifications", "handled_at", "DATETIME DEFAULT NULL COMMENT '处理时间'"),
            ("system_settings", "value_schema", "TEXT COMMENT '配置值结构说明'"),
            ("system_settings", "version", "INT DEFAULT 1 COMMENT '配置版本号'"),
            ("system_settings", "updated_by", "INT DEFAULT NULL COMMENT '最近更新人ID'"),
            ("operation_logs", "result", "VARCHAR(20) DEFAULT NULL COMMENT '执行结果'"),
            ("operation_logs", "action_key", "VARCHAR(100) DEFAULT NULL COMMENT '动作Key'"),
            ("operation_logs", "target_ref", "VARCHAR(100) DEFAULT NULL COMMENT '目标业务ID或字符串ID'"),
            ("operation_logs", "target_name", "VARCHAR(200) DEFAULT NULL COMMENT '目标名称'"),
            ("operation_logs", "risk_level", "VARCHAR(20) DEFAULT 'low' COMMENT '风险等级'"),
            ("operation_logs", "request_id", "VARCHAR(100) DEFAULT NULL COMMENT '请求链路ID'"),
            ("operation_logs", "module", "VARCHAR(50) DEFAULT NULL COMMENT '所属模块'"),
            ("operation_logs", "metadata_json", "TEXT COMMENT '扩展数据（JSON）'"),
            ("operation_logs", "occurred_at", "DATETIME DEFAULT NULL COMMENT '实际发生时间'"),
            ("pbc_objectives", "quarter", "VARCHAR(10) DEFAULT NULL COMMENT '季度'"),
            ("pbc_objectives", "user_id", "INT DEFAULT NULL COMMENT '关联用户ID'"),
            ("milestones", "owner_id", "INT DEFAULT NULL COMMENT '负责人ID'"),
            ("milestones", "sort_order", "INT DEFAULT 0 COMMENT '排序值'"),
            ("milestones", "version", "INT DEFAULT 1 COMMENT '乐观锁版本号'"),
            ("compute_requests", "applicant_id", "INT NOT NULL COMMENT '申请人ID'"),
            ("compute_requests", "scheduled_date", "DATE DEFAULT NULL COMMENT '计划使用日期'"),
            ("risks", "risk_level", "VARCHAR(20) DEFAULT 'medium' COMMENT '风险等级'"),
            ("risks", "due_date", "DATE DEFAULT NULL COMMENT '处理截止日期'"),
            ("risks", "resolved_at", "DATETIME DEFAULT NULL COMMENT '解决时间'"),
            ("risks", "related_task_ids_json", "TEXT COMMENT '关联任务ID数组（JSON）'"),
            ("risks", "version", "INT DEFAULT 1 COMMENT '乐观锁版本号'"),
            ("roles_permissions", "role_code", "VARCHAR(50) NOT NULL COMMENT '角色编码'"),
            ("roles_permissions", "role_name", "VARCHAR(100) DEFAULT NULL COMMENT '角色名称'"),
            ("roles_permissions", "permission_key", "VARCHAR(100) NOT NULL COMMENT '权限键'"),
            ("roles_permissions", "permission_label", "VARCHAR(100) DEFAULT NULL COMMENT '权限名称'"),
            ("roles_permissions", "resource_key", "VARCHAR(100) DEFAULT NULL COMMENT '资源Key'"),
            ("system_metrics", "metric_type", "VARCHAR(50) DEFAULT NULL COMMENT '指标类型'"),
            ("task_dependencies", "depends_on_task_id", "INT DEFAULT NULL COMMENT '依赖任务ID'"),
            ("user_workload", "date", "DATE NOT NULL COMMENT '日期'"),
            ("user_workload", "updated_at", "DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'"),
            ("project_templates", "template_code", "VARCHAR(50) DEFAULT NULL COMMENT '模板编码'"),
            ("project_templates", "enabled_pages_json", "TEXT COMMENT '启用页面列表（JSON数组）'"),
            ("project_templates", "milestones_json", "TEXT COMMENT '里程碑明细（JSON数组）'"),
            ("project_templates", "default_role_template_ids_json", "TEXT COMMENT '默认角色模板ID列表（JSON数组）'"),
            ("project_templates", "used_project_count", "INT DEFAULT 0 COMMENT '已使用项目数量'"),
            ("project_templates", "is_builtin", "TINYINT DEFAULT 0 COMMENT '是否内置模板'"),
            ("project_templates", "version", "INT DEFAULT 1 COMMENT '乐观锁版本号'"),
            ("project_templates", "updated_by", "INT DEFAULT NULL COMMENT '最近更新人ID'"),
            ("role_templates", "template_key", "VARCHAR(50) NOT NULL COMMENT '模板键'"),
            ("role_templates", "is_builtin", "TINYINT DEFAULT 0 COMMENT '是否内置模板'"),
            ("role_templates", "version", "INT DEFAULT 1 COMMENT '乐观锁版本号'"),
            ("role_templates", "reference_count", "INT DEFAULT 0 COMMENT '引用项目/用户数量'"),
            ("role_templates", "updated_by", "INT DEFAULT NULL COMMENT '最近更新人ID'"),
            ("user_sessions", "access_token", "TEXT COMMENT '访问令牌'"),
            ("user_sessions", "refresh_token", "TEXT COMMENT '刷新令牌'"),
            ("user_sessions", "access_expires_at", "DATETIME DEFAULT NULL COMMENT '访问令牌过期时间'"),
            ("user_sessions", "refresh_expires_at", "DATETIME DEFAULT NULL COMMENT '刷新令牌过期时间'"),
        ]
        
        for table_name, column_name, column_def in columns_to_add:
            if not _column_exists(cursor, database_name, table_name, column_name):
                cursor.execute(f"ALTER TABLE `{table_name}` ADD COLUMN `{column_name}` {column_def}")

        created_indexes = 0
        for table_name, index_name, columns in INDEX_DEFINITIONS:
            if _create_index_if_not_exists(cursor, database_name, table_name, index_name, columns):
                created_indexes += 1

        conn.commit()
        print(
            f"数据库 `{database_name}` 初始化成功："
            f"{len(TABLE_SQL)} 张表已检查/创建，{created_indexes} 个索引新建。"
        )

    except pymysql.MySQLError as e:
        if conn is not None:
            conn.rollback()
        error_code = e.args[0] if e.args else None
        print(f"数据库初始化失败：{str(e)}")
        if error_code == 1045:
            print("提示：MySQL 用户名或密码错误，请检查项目根目录 .env 里的 MYSQL_USER / MYSQL_PASSWORD。")
        elif error_code == 1049:
            print("提示：目标数据库不存在但创建失败，请确认当前账号具有建库权限。")
        elif error_code == 2003:
            print("提示：无法连接到 MySQL，请确认 MySQL 服务已启动，并检查 MYSQL_HOST / MYSQL_PORT。")
        raise
    finally:
        if conn is not None:
            conn.close()


if __name__ == "__main__":
    setup_database()
