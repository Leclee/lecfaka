import { useEffect, useState } from 'react'
import {
  Table, Button, Space, Select, Input, Tag, Card, Typography,
  Row, Col, Statistic, message, Popconfirm
} from 'antd'
import { ReloadOutlined, CheckOutlined } from '@ant-design/icons'
import * as adminApi from '../../api/admin'

const { Title, Text } = Typography

export default function RechargeOrders() {
  const [loading, setLoading] = useState(false)
  const [orders, setOrders] = useState<adminApi.RechargeOrder[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [filters, setFilters] = useState<{
    status?: number
    trade_no?: string
  }>({})
  const [stats, setStats] = useState({
    total_count: 0,
    total_amount: 0,
    today_count: 0,
    today_amount: 0,
  })

  useEffect(() => {
    loadData()
    loadStats()
  }, [page, filters])

  const loadData = async () => {
    setLoading(true)
    try {
      const res = await adminApi.getRechargeOrders({
        ...filters,
        page,
        limit: 20,
      })
      setOrders(res.items)
      setTotal(res.total)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  const loadStats = async () => {
    try {
      const res = await adminApi.getRechargeStats()
      setStats(res)
    } catch (e) {
      console.error(e)
    }
  }

  const handleComplete = async (id: number) => {
    try {
      await adminApi.completeRecharge(id)
      message.success('操作成功')
      loadData()
      loadStats()
    } catch (e: any) {
      message.error(e.message || '操作失败')
    }
  }

  const getStatusTag = (status: number) => {
    const map: Record<number, { color: string; text: string }> = {
      0: { color: 'orange', text: '待支付' },
      1: { color: 'green', text: '已支付' },
      2: { color: 'default', text: '已取消' },
      3: { color: 'red', text: '支付失败' },
    }
    const item = map[status] || { color: 'default', text: '未知' }
    return <Tag color={item.color}>{item.text}</Tag>
  }

  const columns = [
    {
      title: '订单号',
      dataIndex: 'trade_no',
      width: 200,
      render: (v: string) => <Text copyable={{ text: v }}>{v}</Text>,
    },
    {
      title: '会员',
      dataIndex: 'username',
      width: 120,
    },
    {
      title: '充值金额',
      dataIndex: 'amount',
      width: 100,
      render: (v: number) => <span className="text-red-500 font-medium">¥{v}</span>,
    },
    {
      title: '支付方式',
      dataIndex: 'payment_name',
      width: 100,
      render: (v: string) => v ? <Tag color="blue">{v}</Tag> : '-',
    },
    {
      title: '下单时间',
      dataIndex: 'created_at',
      width: 170,
    },
    {
      title: '客户IP',
      dataIndex: 'create_ip',
      width: 130,
    },
    {
      title: '支付状态',
      dataIndex: 'status',
      width: 100,
      render: (status: number) => getStatusTag(status),
    },
    {
      title: '支付时间',
      dataIndex: 'paid_at',
      width: 170,
      render: (v: string) => v || '-',
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      render: (_: any, record: adminApi.RechargeOrder) => (
        record.status === 0 && (
          <Popconfirm
            title="确定手动完成此充值订单？"
            onConfirm={() => handleComplete(record.id)}
          >
            <Button type="link" icon={<CheckOutlined />}>
              补单
            </Button>
          </Popconfirm>
        )
      ),
    },
  ]

  return (
    <div>
      <Title level={4}>充值订单</Title>

      {/* 统计卡片 */}
      <Row gutter={16} className="mb-6">
        <Col span={6}>
          <Card className="rounded-xl border-0 shadow-sm">
            <Statistic title="订单数量" value={stats.total_count} />
          </Card>
        </Col>
        <Col span={6}>
          <Card className="rounded-xl border-0 shadow-sm">
            <Statistic 
              title="订单金额" 
              value={stats.total_amount} 
              precision={2}
              valueStyle={{ color: '#cf1322' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card className="rounded-xl border-0 shadow-sm">
            <Statistic title="今日订单" value={stats.today_count} />
          </Card>
        </Col>
        <Col span={6}>
          <Card className="rounded-xl border-0 shadow-sm">
            <Statistic 
              title="今日金额" 
              value={stats.today_amount} 
              precision={2}
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
      </Row>

      <Card className="rounded-xl border-0 shadow-sm">
        <div className="flex justify-between mb-4">
          <Space>
            <Input.Search
              placeholder="订单号"
              allowClear
              onSearch={(v) => {
                setFilters({ ...filters, trade_no: v })
                setPage(1)
              }}
              style={{ width: 200 }}
            />
            <Select
              placeholder="状态"
              allowClear
              style={{ width: 120 }}
              onChange={(v) => {
                setFilters({ ...filters, status: v })
                setPage(1)
              }}
            >
              <Select.Option value={0}>待支付</Select.Option>
              <Select.Option value={1}>已支付</Select.Option>
              <Select.Option value={2}>已取消</Select.Option>
            </Select>
          </Space>
          <Button icon={<ReloadOutlined />} onClick={loadData}>
            刷新
          </Button>
        </div>

        <Table
          columns={columns}
          dataSource={orders}
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
