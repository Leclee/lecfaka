import { useEffect, useState } from 'react'
import { Card, Typography, Button, InputNumber, Alert, Table, Tabs, message, Space, Tag } from 'antd'
import { GiftOutlined, AlipayCircleOutlined, WechatOutlined } from '@ant-design/icons'
import dayjs from 'dayjs'
import api from '../../api'
import { useAuthStore } from '../../store/auth'

const { Title, Text } = Typography

interface WithdrawalRecord {
  id: number
  amount: number
  fee: number
  actual_amount: number
  method: string
  account: string
  status: number
  created_at: string
  processed_at?: string
}

export default function UserCoins() {
  const [loading, setLoading] = useState(false)
  const [amount, setAmount] = useState<number>(100)
  const [selectedMethod, setSelectedMethod] = useState<'alipay' | 'wechat'>('alipay')
  const [records, setRecords] = useState<WithdrawalRecord[]>([])
  const [recordsTotal, setRecordsTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [settings, setSettings] = useState<{ withdraw_min: number; withdraw_fee: number }>({
    withdraw_min: 100,
    withdraw_fee: 5,
  })
  const { user, fetchUser } = useAuthStore()

  useEffect(() => {
    loadSettings()
    loadRecords()
  }, [page])

  const loadSettings = async () => {
    try {
      const res = await api.get('/admin/settings/flat')
      setSettings({
        withdraw_min: Number(res.withdraw_min) || 100,
        withdraw_fee: Number(res.withdraw_fee) || 5,
      })
    } catch (e) {
      console.error(e)
    }
  }

  const loadRecords = async () => {
    try {
      const res = await api.get('/users/me/withdrawals', {
        params: { page, limit: 10 }
      })
      setRecords(res.items || [])
      setRecordsTotal(res.total || 0)
    } catch (e) {
      console.error(e)
    }
  }

  const handleWithdraw = async () => {
    if (!amount || amount < settings.withdraw_min) {
      message.warning(`最低兑现金额为 ${settings.withdraw_min} 元`)
      return
    }
    if (amount > (user?.coin || 0)) {
      message.warning('硬币余额不足')
      return
    }
    
    setLoading(true)
    try {
      await api.post('/users/me/withdraw', {
        amount,
        method: selectedMethod,
      })
      message.success('兑现申请已提交，请等待审核')
      fetchUser()
      loadRecords()
    } catch (e: any) {
      message.error(e.message || '兑现失败')
    } finally {
      setLoading(false)
    }
  }

  const actualAmount = Math.max(0, amount - settings.withdraw_fee)

  const recordColumns = [
    {
      title: '金额',
      dataIndex: 'amount',
      key: 'amount',
      render: (v: number) => <Text type="danger">¥{v}</Text>,
    },
    {
      title: '手续费',
      dataIndex: 'fee',
      key: 'fee',
      render: (v: number) => `¥${v}`,
    },
    {
      title: '实际到账',
      dataIndex: 'actual_amount',
      key: 'actual_amount',
      render: (v: number) => <Text type="success">¥{v}</Text>,
    },
    {
      title: '兑现方式',
      dataIndex: 'method',
      key: 'method',
      render: (v: string) => (
        v === 'alipay' ? (
          <Tag icon={<AlipayCircleOutlined />} color="blue">支付宝</Tag>
        ) : (
          <Tag icon={<WechatOutlined />} color="green">微信</Tag>
        )
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (v: number) => {
        if (v === 0) return <Tag color="processing">待审核</Tag>
        if (v === 1) return <Tag color="success">已完成</Tag>
        if (v === 2) return <Tag color="error">已拒绝</Tag>
        return <Tag>未知</Tag>
      },
    },
    {
      title: '申请时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (v: string) => v ? dayjs(v).format('YYYY-MM-DD HH:mm') : '-',
    },
  ]

  const tabItems = [
    {
      key: 'withdraw',
      label: (
        <span className="flex items-center gap-1">
          <span className="text-green-500">💰</span> 硬币兑现
        </span>
      ),
      children: (
        <div>
          {/* 提示信息 */}
          <Alert
            message={`最低兑现金额：${settings.withdraw_min}元，手动提现费用：${settings.withdraw_fee}元`}
            type="warning"
            className="mb-6 rounded-xl"
          />

          {/* 当前硬币 */}
          <div className="mb-4">
            <Text className="text-gray-500">兑现硬币</Text>
            <Text type="success" className="ml-2">当前拥有硬币:{user?.coin || 0}</Text>
          </div>

          <InputNumber
            value={amount}
            onChange={(v) => setAmount(v || 0)}
            min={settings.withdraw_min}
            max={user?.coin || 0}
            className="w-full mb-4"
            size="large"
          />

          {amount >= settings.withdraw_min && (
            <Alert
              message={`扣除手续费 ¥${settings.withdraw_fee}，实际到账 ¥${actualAmount}`}
              type="info"
              className="mb-4 rounded-lg"
            />
          )}

          {/* 兑现方式 */}
          <div className="mb-6">
            <Text className="text-gray-500 block mb-2">兑现方式</Text>
            <Space>
              <Button
                type={selectedMethod === 'alipay' ? 'primary' : 'default'}
                onClick={() => setSelectedMethod('alipay')}
                className={`rounded-lg ${selectedMethod === 'alipay' ? 'bg-blue-500 border-blue-500' : ''}`}
                icon={<AlipayCircleOutlined className="text-lg" />}
              >
                支付宝
              </Button>
              <Button
                type={selectedMethod === 'wechat' ? 'primary' : 'default'}
                onClick={() => setSelectedMethod('wechat')}
                className={`rounded-lg ${selectedMethod === 'wechat' ? 'bg-green-500 border-green-500' : ''}`}
                icon={<WechatOutlined className="text-lg" />}
              >
                微信
              </Button>
            </Space>
          </div>

          <Button
            type="primary"
            size="large"
            loading={loading}
            onClick={handleWithdraw}
            className="w-full h-12 rounded-xl bg-gradient-to-r from-pink-400 to-pink-500 border-0"
          >
            立即兑现
          </Button>
        </div>
      ),
    },
    {
      key: 'records',
      label: (
        <span className="flex items-center gap-1">
          📋 兑现记录 <Tag color="pink">{recordsTotal}</Tag>
        </span>
      ),
      children: (
        <Table
          columns={recordColumns}
          dataSource={records}
          rowKey="id"
          pagination={{
            current: page,
            total: recordsTotal,
            pageSize: 10,
            onChange: setPage,
          }}
          size="small"
        />
      ),
    },
  ]

  return (
    <div>
      <Title level={4} className="flex items-center gap-2">
        <GiftOutlined /> 硬币兑现
      </Title>

      <Card className="border-0 shadow-sm rounded-xl">
        <Tabs items={tabItems} />
      </Card>
    </div>
  )
}
