import { useEffect, useState } from 'react'
import { Card, Typography, Button, InputNumber, Alert, Table, message, Space } from 'antd'
import { WalletOutlined, WechatOutlined, AlipayCircleOutlined, GiftOutlined } from '@ant-design/icons'
import api from '../../api'
import { useAuthStore } from '../../store/auth'

const { Title, Text } = Typography

interface UserGroup {
  id: number
  name: string
  discount: number
  min_recharge: number
  icon?: string
}

interface PaymentMethod {
  id: number
  name: string
  icon?: string
  handler: string
}

interface RechargeBonus {
  amount: number
  bonus: number
}

export default function UserRecharge() {
  const [loading, setLoading] = useState(false)
  const [amount, setAmount] = useState<number>(1)
  const [selectedPayment, setSelectedPayment] = useState<number | null>(null)
  const [payments, setPayments] = useState<PaymentMethod[]>([])
  const [userGroups, setUserGroups] = useState<UserGroup[]>([])
  const [bonusConfig, setBonusConfig] = useState<RechargeBonus[]>([])
  const { user, fetchUser } = useAuthStore()

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      const [paymentsRes, groupsRes, settingsRes] = await Promise.all([
        api.get('/shop/payments'),
        api.get('/admin/user-groups'),
        api.get('/admin/settings/flat'),
      ])
      
      // 只显示支持充值的支付方式
      const rechargePayments = (paymentsRes || []).filter((p: any) => p.handler !== '#balance')
      setPayments(rechargePayments)
      if (rechargePayments.length > 0) {
        setSelectedPayment(rechargePayments[0].id)
      }
      
      setUserGroups(groupsRes.items || [])
      
      // 解析充值赠送配置
      const bonusStr = settingsRes.recharge_bonus_config || ''
      const bonuses: RechargeBonus[] = []
      bonusStr.split('\n').forEach((line: string) => {
        const [amt, bonus] = line.split('-').map(Number)
        if (amt && bonus) {
          bonuses.push({ amount: amt, bonus })
        }
      })
      setBonusConfig(bonuses)
    } catch (e) {
      console.error(e)
    }
  }

  const handleRecharge = async () => {
    if (!amount || amount < 1) {
      message.warning('请输入充值金额')
      return
    }
    if (!selectedPayment) {
      message.warning('请选择支付方式')
      return
    }
    
    setLoading(true)
    try {
      const res = await api.post('/users/me/recharge', {
        amount,
        payment_id: selectedPayment,
      })
      
      if (res.payment_url) {
        window.location.href = res.payment_url
      } else {
        message.success('充值订单已创建')
        fetchUser()
      }
    } catch (e: any) {
      message.error(e.message || '充值失败')
    } finally {
      setLoading(false)
    }
  }

  // 计算当前赠送金额
  const currentBonus = bonusConfig.reduce((bonus, item) => {
    if (amount >= item.amount) return item.bonus
    return bonus
  }, 0)

  // 用户等级表格列
  const groupColumns = [
    {
      title: '等级',
      key: 'level',
      render: (_: any, _record: UserGroup, index: number) => (
        <span className="px-2 py-1 rounded text-white text-xs" style={{
          background: `linear-gradient(135deg, ${['#9ca3af', '#60a5fa', '#f472b6', '#fbbf24'][index % 4]} 0%, ${['#6b7280', '#3b82f6', '#ec4899', '#f59e0b'][index % 4]} 100%)`
        }}>
          LV{index + 1}
        </span>
      ),
    },
    {
      title: '等级名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '所需元气',
      dataIndex: 'min_recharge',
      key: 'min_recharge',
      render: (v: number) => <Text type="danger">{v}</Text>,
    },
  ]

  // 支付方式图标
  const PaymentIcon = ({ handler }: { handler: string }) => {
    if (handler?.includes('wechat') || handler?.includes('wxpay')) 
      return <WechatOutlined className="text-xl text-green-500" />
    if (handler?.includes('alipay')) 
      return <AlipayCircleOutlined className="text-xl text-blue-500" />
    return <WalletOutlined className="text-xl" />
  }

  return (
    <div>
      <Title level={4} className="flex items-center gap-2">
        <WalletOutlined /> 充值余额
      </Title>

      {/* 用户状态 */}
      <Alert
        message={
          <span>
            当前元气：<Text type="danger">{user?.coin || 0}</Text>，
            您当前用户等级：<Text type="warning">一贫如洗</Text>，
            升级到 <Text type="success">小康之家</Text> 还需要充值 
            <Text type="danger">¥{Math.max(0, 50 - (user?.total_recharge || 0)).toFixed(2)}</Text>
          </span>
        }
        type="info"
        className="mb-6 rounded-xl"
      />

      {/* 充值赠送活动 */}
      {bonusConfig.length > 0 && (
        <Card className="border-0 shadow-sm rounded-xl mb-6 bg-gradient-to-r from-pink-50 to-purple-50">
          <div className="flex items-center gap-2 mb-3">
            <GiftOutlined className="text-pink-500" />
            <Text strong>充值赠送活动</Text>
          </div>
          <div className="space-y-1 text-sm">
            {bonusConfig.map((item, idx) => (
              <div key={idx}>
                一次性充值 <Text type="danger">¥{item.amount}</Text>，
                赠送 <Text type="success">¥{item.bonus}</Text>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* 充值表单 */}
      <Card className="border-0 shadow-sm rounded-xl mb-6">
        <div className="mb-4">
          <Text className="text-gray-500">金额</Text>
          <Text type="secondary" className="ml-2">当前余额: ¥{user?.balance || 0}</Text>
        </div>
        
        <InputNumber
          value={amount}
          onChange={(v) => setAmount(v || 1)}
          min={1}
          max={10000}
          className="w-full mb-4"
          size="large"
          addonBefore="¥"
        />

        {currentBonus > 0 && (
          <Alert
            message={`充值 ¥${amount} 将赠送 ¥${currentBonus}`}
            type="success"
            showIcon
            className="mb-4 rounded-lg"
          />
        )}

        <div className="mb-4">
          <Text className="text-gray-500 block mb-2">支付方式</Text>
          <Space wrap>
            {payments.map((p) => (
              <Button
                key={p.id}
                type={selectedPayment === p.id ? 'primary' : 'default'}
                onClick={() => setSelectedPayment(p.id)}
                className={`rounded-lg ${selectedPayment === p.id ? 'bg-pink-500 border-pink-500' : ''}`}
                icon={<PaymentIcon handler={p.handler} />}
              >
                {p.name}
              </Button>
            ))}
          </Space>
        </div>

        <Button
          type="primary"
          size="large"
          loading={loading}
          onClick={handleRecharge}
          className="w-full h-12 rounded-xl bg-gradient-to-r from-pink-400 to-pink-500 border-0"
        >
          立即充值
        </Button>
      </Card>

      {/* 会员等级说明 */}
      <Card className="border-0 shadow-sm rounded-xl">
        <div className="mb-4">
          <Text strong>会员等级划分</Text>
          <Text type="secondary" className="ml-2">（说明：充值/消费可获得元气，比例1:1）</Text>
        </div>
        
        <Table
          columns={groupColumns}
          dataSource={userGroups}
          rowKey="id"
          pagination={false}
          size="small"
        />
      </Card>
    </div>
  )
}
