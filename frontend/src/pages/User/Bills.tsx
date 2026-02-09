import { useEffect, useState } from 'react'
import { Card, Typography, Table, Tag, Tabs } from 'antd'
import { FileTextOutlined } from '@ant-design/icons'
import dayjs from 'dayjs'
import api from '../../api'

const { Title, Text } = Typography

interface BillItem {
  id: number
  amount: number
  balance: number
  type: number
  description: string
  created_at: string
}

export default function UserBills() {
  const [loading, setLoading] = useState(false)
  const [data, setData] = useState<BillItem[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize] = useState(20)
  const [activeTab, setActiveTab] = useState('all')

  useEffect(() => {
    loadData()
  }, [page, activeTab])

  const loadData = async () => {
    setLoading(true)
    try {
      const type = activeTab === 'income' ? 1 : activeTab === 'expense' ? 0 : undefined
      const res = await api.get('/users/me/bills', {
        params: { page, limit: pageSize, type }
      })
      setData(res.items || [])
      setTotal(res.total || 0)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 80,
    },
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type',
      width: 80,
      render: (type: number) => (
        type === 1 
          ? <Tag color="success">收入</Tag>
          : <Tag color="error">支出</Tag>
      ),
    },
    {
      title: '金额',
      dataIndex: 'amount',
      key: 'amount',
      width: 120,
      render: (amount: number, record: BillItem) => (
        <Text className={record.type === 1 ? 'text-green-500' : 'text-red-500'}>
          {record.type === 1 ? '+' : '-'}¥{Math.abs(amount).toFixed(2)}
        </Text>
      ),
    },
    {
      title: '余额',
      dataIndex: 'balance',
      key: 'balance',
      width: 120,
      render: (balance: number) => <Text>¥{balance.toFixed(2)}</Text>,
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
    },
    {
      title: '时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (text: string) => text ? dayjs(text).format('YYYY-MM-DD HH:mm:ss') : '-',
    },
  ]

  return (
    <div>
      <Title level={4} className="flex items-center gap-2">
        <FileTextOutlined /> 我的账单
      </Title>

      <Card className="border-0 shadow-sm rounded-xl">
        <Tabs
          activeKey={activeTab}
          onChange={(key) => {
            setActiveTab(key)
            setPage(1)
          }}
          items={[
            { key: 'all', label: '全部' },
            { key: 'income', label: '收入' },
            { key: 'expense', label: '支出' },
          ]}
        />

        <Table
          rowKey="id"
          loading={loading}
          dataSource={data}
          columns={columns}
          pagination={{
            current: page,
            pageSize,
            total,
            onChange: setPage,
            showSizeChanger: false,
          }}
          size="small"
        />
      </Card>
    </div>
  )
}
