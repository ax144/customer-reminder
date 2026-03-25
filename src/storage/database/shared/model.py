from coze_coding_dev_sdk.database import Base

from typing import Optional
import datetime

from sqlalchemy import BigInteger, Boolean, Column, DateTime, Double, Integer, Numeric, PrimaryKeyConstraint, Table, Text, text, String, JSON, Date, func
from sqlalchemy.dialects.postgresql import OID
from sqlalchemy.orm import Mapped, mapped_column


class HealthCheck(Base):
    __tablename__ = 'health_check'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='health_check_pkey'),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), server_default=text('now()'))


t_pg_stat_statements = Table(
    'pg_stat_statements', Base.metadata,
    Column('userid', OID),
    Column('dbid', OID),
    Column('toplevel', Boolean),
    Column('queryid', BigInteger),
    Column('query', Text),
    Column('plans', BigInteger),
    Column('total_plan_time', Double(53)),
    Column('min_plan_time', Double(53)),
    Column('max_plan_time', Double(53)),
    Column('mean_plan_time', Double(53)),
    Column('stddev_plan_time', Double(53)),
    Column('calls', BigInteger),
    Column('total_exec_time', Double(53)),
    Column('min_exec_time', Double(53)),
    Column('max_exec_time', Double(53)),
    Column('mean_exec_time', Double(53)),
    Column('stddev_exec_time', Double(53)),
    Column('rows', BigInteger),
    Column('shared_blks_hit', BigInteger),
    Column('shared_blks_read', BigInteger),
    Column('shared_blks_dirtied', BigInteger),
    Column('shared_blks_written', BigInteger),
    Column('local_blks_hit', BigInteger),
    Column('local_blks_read', BigInteger),
    Column('local_blks_dirtied', BigInteger),
    Column('local_blks_written', BigInteger),
    Column('temp_blks_read', BigInteger),
    Column('temp_blks_written', BigInteger),
    Column('shared_blk_read_time', Double(53)),
    Column('shared_blk_write_time', Double(53)),
    Column('local_blk_read_time', Double(53)),
    Column('local_blk_write_time', Double(53)),
    Column('temp_blk_read_time', Double(53)),
    Column('temp_blk_write_time', Double(53)),
    Column('wal_records', BigInteger),
    Column('wal_fpi', BigInteger),
    Column('wal_bytes', Numeric),
    Column('jit_functions', BigInteger),
    Column('jit_generation_time', Double(53)),
    Column('jit_inlining_count', BigInteger),
    Column('jit_inlining_time', Double(53)),
    Column('jit_optimization_count', BigInteger),
    Column('jit_optimization_time', Double(53)),
    Column('jit_emission_count', BigInteger),
    Column('jit_emission_time', Double(53)),
    Column('jit_deform_count', BigInteger),
    Column('jit_deform_time', Double(53)),
    Column('stats_since', DateTime(True)),
    Column('minmax_stats_since', DateTime(True))
)


t_pg_stat_statements_info = Table(
    'pg_stat_statements_info', Base.metadata,
    Column('dealloc', BigInteger),
    Column('stats_reset', DateTime(True))
)


class Customer(Base):
    """客户信息表"""
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False, comment="客户姓名")
    company: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, comment="公司名称")
    position: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, comment="职位")
    referrer: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, comment="推荐人")
    direct_project: Mapped[Optional[str]] = mapped_column(String(500), nullable=True, comment="直接项目")
    project_progress_1: Mapped[Optional[str]] = mapped_column(String(500), nullable=True, comment="直接项目进度")
    extended_project: Mapped[Optional[str]] = mapped_column(String(500), nullable=True, comment="延伸项目")
    project_progress_2: Mapped[Optional[str]] = mapped_column(String(500), nullable=True, comment="延伸项目进度")
    others: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="其他信息")
    last_contact_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True, comment="最后联系时间")
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=True, comment="创建时间")
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=True, comment="更新时间")
    meeting_date: Mapped[Optional[datetime.date]] = mapped_column(Date, nullable=True, comment="约见日期")
    visit_date: Mapped[Optional[datetime.date]] = mapped_column(Date, nullable=True, comment="外访日期")


class PushLog(Base):
    """推送日志表"""
    __tablename__ = "push_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    push_date: Mapped[datetime.date] = mapped_column(Date, nullable=False, comment="推送日期")
    push_type: Mapped[str] = mapped_column(String(50), nullable=False, comment="推送类型")
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, comment="创建时间")


class Document(Base):
    """文档库表"""
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False, comment="文档标题")
    category: Mapped[str] = mapped_column(String(100), nullable=False, comment="文档分类")
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="文档内容摘要")
    keywords: Mapped[Optional[list]] = mapped_column(JSON, nullable=True, comment="关键词数组")
    file_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True, comment="原始文件路径")
    file_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="文件URL")
    project: Mapped[Optional[str]] = mapped_column(String(200), nullable=True, comment="关联项目")
    status: Mapped[Optional[str]] = mapped_column(String(50), default='active', nullable=True, comment="状态")
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=True, comment="创建时间")
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=True, comment="更新时间")


class WorkSchedule(Base):
    """工作安排表"""
    __tablename__ = "work_schedules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False, comment="安排标题")
    assignee: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, comment="负责人")
    project: Mapped[Optional[str]] = mapped_column(String(200), nullable=True, comment="关联项目")
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="安排内容")
    priority: Mapped[Optional[str]] = mapped_column(String(20), default='medium', nullable=True, comment="优先级")
    status: Mapped[Optional[str]] = mapped_column(String(50), default='pending', nullable=True, comment="状态")
    due_date: Mapped[Optional[datetime.date]] = mapped_column(Date, nullable=True, comment="截止日期")
    related_customers: Mapped[Optional[list]] = mapped_column(JSON, nullable=True, comment="关联客户")
    related_documents: Mapped[Optional[list]] = mapped_column(JSON, nullable=True, comment="关联文档ID")
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=True, comment="创建时间")
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=True, comment="更新时间")
