import { useEffect, useState } from 'react'
import {
  Table, Select, Tag, Card, Typography, Row, Col, Statistic, Avatar
} from 'antd'
import { UserOutlined } from '@ant-design/icons'
import * as adminApi from '../../api/admin'

const { Title, Text } = Typography

export default function Bills() {
  const [loading, setLoading] = useState(false)
  const [bills, setBills] = useState<adminApi.Bill[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [filters, setFilters] = useState<{ type?: number; currency?: number }>({})
  const [stats, setStats] = useState({
    today_income: 0,
    today_expense: 0,
    total_income: 0,
    total_expense: 0,
  })

  useEffect(() => {
    loadData()
    loadStats()
  }, [page, filters])

  const loadData = async () => {
    setLoading(true)
    try {
      const res = await adminApi.getBills({ ...filters, page, limit: 20 })
      setBills(res.items)
      setTotal(res.total)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  const loadStats = async () => {
    try {
      const res = await adminApi.getBillStats()
      setStats(res)
    } catch (e) {
      console.error(e)
    }
  }

  const columns = [
    {
      title: '会员',
      key: 'user',
      width: 150,
      render: (_: any, record: adminApi.Bill) => (
        <div className="flex items-center gap-2">
          <Avatar src={record.avatar} icon={<UserOutlined />} size="small" />
          <Text>{record.username}</Text>
        </div>
      ),
    },
    {
      title: '金额',
      dataIndex: 'amount',
      width: 100,
      render: (v: number, record: adminApi.Bill) => (
        <span className={record.type === 1 ? 'text-green-500' : 'text-red-500'}>
          {record.type === 1 ? '+' : '-'}¥{v}
        </span>
      ),
    },
    {
      title: '余额',
      dataIndex: 'balance',
      width: 100,
      render: (v: number) => `¥${v}`,
    },
    {
      title: '收支类型',
      dataIndex: 'type',
      width: 100,
      render: (v: number) => (
        <Tag color={v === 1 ? 'green' : 'red'}>{v === 1 ? '收入' : '支出'}</Tag>
      ),
    },
    {
      title: '货币类型',
      dataIndex: 'currency',
      width: 100,
      render: (v: number) => (
        <Tag color={v === 0 ? 'blue' : 'purple'}>{v === 0 ? '余额' : '硬币'}</Tag>
      ),
    },
    {
      title: '交易信息',
      dataIndex: 'description',
      ellipsis: true,
    },
    {
      title: '交易时间',
      dataIndex: 'created_at',
      width: 170,
    },
  ]

  return (
    <div>
      <Title level={4}>账单管理</Title>

      {/* 统计卡片 */}
      <Row gutter={16} className="mb-6">
        <Col span={6}>
          <Card className="rounded-xl border-0 shadow-sm">
            <Statistic 
              title="今日收入" 
              value={stats.today_income} 
              precision={2}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card className="rounded-xl border-0 shadow-sm">
            <Statistic 
              title="今日支出" 
              value={stats.today_expense} 
              precision={2}
              valueStyle={{ color: '#ff4d4f' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card className="rounded-xl border-0 shadow-sm">
            <Statistic 
              title="总收入" 
              value={stats.total_income} 
              precision={2}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card className="rounded-xl border-0 shadow-sm">
            <Statistic 
              title="总支出" 
              value={stats.total_expense} 
              precision={2}
            />
          </Card>
        </Col>
      </Row>

      <Card className="rounded-xl border-0 shadow-sm">
        {/* 筛选栏 */}
        <div className="flex gap-4 mb-4">
          <Select
            placeholder="支出/收入"
            allowClear
            style={{ width: 120 }}
            onChange={(v) => {
              setFilters({ ...filters, type: v })
              setPage(1)
            }}
          >
            <Select.Option value={0}>支出</Select.Option>
            <Select.Option value={1}>收入</Select.Option>
          </Select>
          <Select
            placeholder="钱包类型"
            allowClear
            style={{ width: 120 }}
            onChange={(v) => {
              setFilters({ ...filters, currency: v })
              setPage(1)
            }}
          >
            <Select.Option value={0}>余额</Select.Option>
            <Select.Option value={1}>硬币</Select.Option>
          </Select>
        </div>

        {/* 状态Tab */}
        <div className="flex gap-2 mb-4">
          <button 
            className={`px-4 py-1 rounded ${filters.type === undefined ? 'bg-blue-500 text-white' : 'bg-gray-100'}`}
            onClick={() => { setFilters({}); setPage(1) }}
          >
            全部
          </button>
          <button 
            className={`px-4 py-1 rounded ${filters.type === 1 ? 'bg-blue-500 text-white' : 'bg-gray-100'}`}
            onClick={() => { setFilters({ ...filters, type: 1 }); setPage(1) }}
          >
            收入
          </button>
          <button 
            className={`px-4 py-1 rounded ${filters.type === 0 ? 'bg-blue-500 text-white' : 'bg-gray-100'}`}
            onClick={() => { setFilters({ ...filters, type: 0 }); setPage(1) }}
          >
            支出
          </button>
        </div>

        <Table
          columns={columns}
          dataSource={bills}
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
