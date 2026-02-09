import { useEffect, useState } from 'react'
import {
  Table, Tag, Card, Typography, Row, Col, Statistic, Input, Tooltip
} from 'antd'
import { WarningOutlined } from '@ant-design/icons'
import * as adminApi from '../../api/admin'

const { Title, Text } = Typography

export default function Logs() {
  const [loading, setLoading] = useState(false)
  const [logs, setLogs] = useState<adminApi.OperationLog[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [filters, setFilters] = useState<{ risk_level?: number; email?: string }>({})
  const [stats, setStats] = useState({ total: 0, today: 0, high_risk: 0 })

  useEffect(() => {
    loadData()
    loadStats()
  }, [page, filters])

  const loadData = async () => {
    setLoading(true)
    try {
      const res = await adminApi.getLogs({ ...filters, page, limit: 20 })
      setLogs(res.items)
      setTotal(res.total)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  const loadStats = async () => {
    try {
      const res = await adminApi.getLogStats()
      setStats(res)
    } catch (e) {
      console.error(e)
    }
  }

  const getRiskTag = (level: number) => {
    if (level === 1) {
      return <Tag color="red" icon={<WarningOutlined />}>风险较高</Tag>
    }
    return <Tag color="green">无风险</Tag>
  }

  const columns = [
    {
      title: '管理员',
      dataIndex: 'email',
      width: 200,
      render: (v: string) => <Text className="text-blue-500">{v || '-'}</Text>,
    },
    {
      title: '日志',
      dataIndex: 'action',
      ellipsis: true,
    },
    {
      title: '时间',
      dataIndex: 'created_at',
      width: 170,
    },
    {
      title: 'IP',
      dataIndex: 'ip',
      width: 140,
    },
    {
      title: '浏览器信息',
      dataIndex: 'user_agent',
      width: 300,
      ellipsis: true,
      render: (v: string) => (
        <Tooltip title={v}>
          <span>{v || '-'}</span>
        </Tooltip>
      ),
    },
    {
      title: '评估',
      dataIndex: 'risk_level',
      width: 120,
      render: (level: number) => getRiskTag(level),
    },
  ]

  return (
    <div>
      <Title level={4}>操作日志</Title>

      {/* 统计卡片 */}
      <Row gutter={16} className="mb-6">
        <Col span={8}>
          <Card className="rounded-xl border-0 shadow-sm">
            <Statistic title="总日志数" value={stats.total} />
          </Card>
        </Col>
        <Col span={8}>
          <Card className="rounded-xl border-0 shadow-sm">
            <Statistic title="今日日志" value={stats.today} valueStyle={{ color: '#1890ff' }} />
          </Card>
        </Col>
        <Col span={8}>
          <Card className="rounded-xl border-0 shadow-sm">
            <Statistic 
              title="风险较高" 
              value={stats.high_risk} 
              valueStyle={{ color: stats.high_risk > 0 ? '#ff4d4f' : '#52c41a' }}
            />
          </Card>
        </Col>
      </Row>

      <Card className="rounded-xl border-0 shadow-sm">
        {/* 筛选栏 */}
        <div className="flex gap-4 mb-4">
          <Input.Search
            placeholder="Email"
            allowClear
            onSearch={(v) => {
              setFilters({ ...filters, email: v })
              setPage(1)
            }}
            style={{ width: 200 }}
          />
          <Input.Search
            placeholder="IP地址"
            allowClear
            style={{ width: 150 }}
          />
        </div>

        {/* 状态Tab */}
        <div className="flex gap-2 mb-4">
          <button 
            className={`px-4 py-1 rounded ${filters.risk_level === undefined ? 'bg-blue-500 text-white' : 'bg-gray-100'}`}
            onClick={() => { setFilters({}); setPage(1) }}
          >
            全部
          </button>
          <button 
            className={`px-4 py-1 rounded ${filters.risk_level === 0 ? 'bg-blue-500 text-white' : 'bg-gray-100'}`}
            onClick={() => { setFilters({ ...filters, risk_level: 0 }); setPage(1) }}
          >
            无风险
          </button>
          <button 
            className={`px-4 py-1 rounded ${filters.risk_level === 1 ? 'bg-blue-500 text-white' : 'bg-gray-100'}`}
            onClick={() => { setFilters({ ...filters, risk_level: 1 }); setPage(1) }}
          >
            风险较高
          </button>
        </div>

        <Table
          columns={columns}
          dataSource={logs}
          rowKey="id"
          loading={loading}
          pagination={{
            current: page,
            total,
            pageSize: 20,
            onChange: setPage,
            showTotal: (t) => `共 ${t} 条`,
          }}
        />
      </Card>
    </div>
  )
}
