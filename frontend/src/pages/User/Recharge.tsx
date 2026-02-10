import { useEffect, useMemo, useRef, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Card, Typography, Button, InputNumber, Alert, Table, message, Space, Modal } from 'antd'
import { WalletOutlined, WechatOutlined, AlipayCircleOutlined, GiftOutlined } from '@ant-design/icons'
import {
  createRecharge,
  getRechargeOptions,
  getRechargeOrderStatus,
  RechargeBonus,
  RechargeConfig,
  RechargePayment,
  RechargeUserGroup,
} from '../../api/user'
import { useAuthStore } from '../../store/auth'

const { Title, Text } = Typography

function submitPaymentForm(action: string, formData: Record<string, any>) {
  const formEl = document.createElement('form')
  formEl.method = 'POST'
  formEl.action = action
  formEl.style.display = 'none'

  Object.entries(formData || {}).forEach(([key, val]) => {
    const input = document.createElement('input')
    input.type = 'hidden'
    input.name = key
    input.value = String(val)
    formEl.appendChild(input)
  })

  document.body.appendChild(formEl)
  formEl.submit()
}

const PaymentIcon = ({ handler }: { handler: string }) => {
  if (handler?.includes('wechat') || handler?.includes('wxpay')) {
    return <WechatOutlined className="text-xl text-green-500" />
  }
  if (handler?.includes('alipay')) {
    return <AlipayCircleOutlined className="text-xl text-blue-500" />
  }
  return <WalletOutlined className="text-xl" />
}

export default function UserRecharge() {
  const [searchParams] = useSearchParams()
  const tradeNoFromUrl = searchParams.get('trade_no')

  const [loading, setLoading] = useState(false)
  const [amount, setAmount] = useState<number>(1)
  const [selectedPayment, setSelectedPayment] = useState<number | null>(null)
  const [payments, setPayments] = useState<RechargePayment[]>([])
  const [userGroups, setUserGroups] = useState<RechargeUserGroup[]>([])
  const [bonusConfig, setBonusConfig] = useState<RechargeBonus[]>([])
  const [rechargeConfig, setRechargeConfig] = useState<RechargeConfig>({
    min: 1,
    max: 1000,
    bonus_enabled: false,
    bonus: [],
  })

  const [qrcodeModalOpen, setQrcodeModalOpen] = useState(false)
  const [qrcodeUrl, setQrcodeUrl] = useState('')
  const [qrcodeTradeNo, setQrcodeTradeNo] = useState('')

  const pollingTimerRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const { user, fetchUser } = useAuthStore()

  const stopPolling = () => {
    if (pollingTimerRef.current) {
      clearInterval(pollingTimerRef.current)
      pollingTimerRef.current = null
    }
  }

  const checkRechargeStatus = async (tradeNo: string, silent = true) => {
    try {
      const statusRes = await getRechargeOrderStatus(tradeNo)
      if (statusRes.status === 1) {
        stopPolling()
        setQrcodeModalOpen(false)
        if (!silent) {
          message.success('充值成功')
        }
        await fetchUser()
        return true
      }
      return false
    } catch (e) {
      if (!silent) {
        // 全局拦截器会处理错误提示
        console.error(e)
      }
      return false
    }
  }

  const startPolling = (tradeNo: string) => {
    stopPolling()
    pollingTimerRef.current = setInterval(async () => {
      await checkRechargeStatus(tradeNo, false)
    }, 3000)
  }

  const loadData = async () => {
    try {
      const options = await getRechargeOptions()
      const rechargePayments = (options.payments || []).filter((p) => p.handler !== '#balance')
      setPayments(rechargePayments)
      setUserGroups(options.user_groups || [])

      const config = options.recharge_config || {
        min: 1,
        max: 1000,
        bonus_enabled: false,
        bonus: [],
      }
      setRechargeConfig(config)
      setBonusConfig(config.bonus_enabled ? (config.bonus || []) : [])

      if (rechargePayments.length > 0) {
        setSelectedPayment(rechargePayments[0].id)
      }

      const min = config.min > 0 ? config.min : 1
      setAmount((prev) => (prev < min ? min : prev))
    } catch (e) {
      console.error(e)
    }
  }

  useEffect(() => {
    loadData()
    return () => stopPolling()
  }, [])

  useEffect(() => {
    if (!tradeNoFromUrl) {
      return
    }
    checkRechargeStatus(tradeNoFromUrl, false)
  }, [tradeNoFromUrl])

  const currentBonus = useMemo(() => {
    return bonusConfig.reduce((bonus, item) => {
      if (amount >= item.amount) return item.bonus
      return bonus
    }, 0)
  }, [amount, bonusConfig])

  const handleRecharge = async () => {
    if (!amount || amount <= 0) {
      message.warning('请输入充值金额')
      return
    }
    if (amount < rechargeConfig.min) {
      message.warning(`最低充值金额为 ${rechargeConfig.min}`)
      return
    }
    if (rechargeConfig.max > 0 && amount > rechargeConfig.max) {
      message.warning(`最高充值金额为 ${rechargeConfig.max}`)
      return
    }
    if (!selectedPayment) {
      message.warning('请选择支付方式')
      return
    }

    setLoading(true)
    try {
      const res = await createRecharge({
        amount,
        payment_id: selectedPayment,
      })

      if (res.payment_type === 'redirect' && res.payment_url) {
        window.location.href = res.payment_url
        return
      }

      if (res.payment_type === 'form' && res.payment_url) {
        submitPaymentForm(res.payment_url, (res.extra?.form_data as Record<string, any>) || {})
        return
      }

      if (res.payment_type === 'qrcode') {
        const qrUrl = (res.extra?.qrcode_url as string) || res.payment_url || ''
        if (!qrUrl) {
          message.warning('未获取到二维码地址，请切换支付方式重试')
          return
        }
        setQrcodeUrl(qrUrl)
        setQrcodeTradeNo(res.trade_no)
        setQrcodeModalOpen(true)
        startPolling(res.trade_no)
        return
      }

      if (res.payment_url) {
        window.location.href = res.payment_url
        return
      }

      message.success('充值订单创建成功')
      await fetchUser()
    } catch (e) {
      // 全局拦截器已提示错误，避免重复弹窗
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  const groupColumns = [
    {
      title: '等级',
      key: 'level',
      render: (_: any, _record: RechargeUserGroup, index: number) => (
        <span
          className="px-2 py-1 rounded text-white text-xs"
          style={{
            background: `linear-gradient(135deg, ${['#9ca3af', '#60a5fa', '#f472b6', '#fbbf24'][index % 4]} 0%, ${['#6b7280', '#3b82f6', '#ec4899', '#f59e0b'][index % 4]} 100%)`,
          }}
        >
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

  return (
    <div>
      <Title level={4} className="flex items-center gap-2">
        <WalletOutlined /> 充值余额
      </Title>

      <Alert
        message={
          <span>
            当前元气: <Text type="danger">{user?.coin || 0}</Text>，
            您当前用户等级: <Text type="warning">一贫如洗</Text>，
            升级到 <Text type="success">小康之家</Text> 还需要充值
            <Text type="danger">¥{Math.max(0, 50 - (user?.total_recharge || 0)).toFixed(2)}</Text>
          </span>
        }
        type="info"
        className="mb-6 rounded-xl"
      />

      {bonusConfig.length > 0 && (
        <Card className="border-0 shadow-sm rounded-xl mb-6 bg-gradient-to-r from-pink-50 to-purple-50">
          <div className="flex items-center gap-2 mb-3">
            <GiftOutlined className="text-pink-500" />
            <Text strong>充值赠送活动</Text>
          </div>
          <div className="space-y-1 text-sm">
            {bonusConfig.map((item, idx) => (
              <div key={idx}>
                一次性充值 <Text type="danger">¥{item.amount}</Text>，赠送 <Text type="success">¥{item.bonus}</Text>
              </div>
            ))}
          </div>
        </Card>
      )}

      <Card className="border-0 shadow-sm rounded-xl mb-6">
        <div className="mb-4">
          <Text className="text-gray-500">金额</Text>
          <Text type="secondary" className="ml-2">
            当前余额: ¥{user?.balance || 0}
          </Text>
          <Text type="secondary" className="ml-2">
            (单次范围: ¥{rechargeConfig.min} - ¥{rechargeConfig.max})
          </Text>
        </div>

        <InputNumber
          value={amount}
          onChange={(v) => setAmount(v || rechargeConfig.min || 1)}
          min={rechargeConfig.min || 1}
          max={rechargeConfig.max > 0 ? rechargeConfig.max : 1000000}
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

      <Card className="border-0 shadow-sm rounded-xl">
        <div className="mb-4">
          <Text strong>会员等级划分</Text>
          <Text type="secondary" className="ml-2">
            （说明：充值+消费可获得元气，比例1:1）
          </Text>
        </div>

        <Table columns={groupColumns} dataSource={userGroups} rowKey="id" pagination={false} size="small" />
      </Card>

      <Modal
        open={qrcodeModalOpen}
        centered
        onCancel={() => {
          setQrcodeModalOpen(false)
          stopPolling()
        }}
        footer={null}
        title="扫码支付"
      >
        <div className="text-center py-2">
          <div className="text-lg font-semibold mb-2">订单号：{qrcodeTradeNo}</div>
          <div className="flex justify-center mb-4">
            <div className="p-3 bg-white border border-gray-200 rounded-xl shadow-sm">
              <img
                src={qrcodeUrl}
                alt="充值二维码"
                className="w-56 h-56 object-contain"
                onError={(e) => {
                  ;(e.target as HTMLImageElement).src =
                    'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200"><text x="50%" y="50%" text-anchor="middle" dy=".3em" font-size="14">二维码加载失败</text></svg>'
                }}
              />
            </div>
          </div>
          <div className="text-gray-500 text-sm mb-3">支付完成后会自动到账</div>
          <Button
            type="primary"
            block
            className="bg-gradient-to-r from-pink-400 to-pink-500 border-0"
            onClick={async () => {
              const paid = await checkRechargeStatus(qrcodeTradeNo, false)
              if (!paid) {
                message.info('暂未检测到支付，请稍后重试')
              }
            }}
          >
            我已完成支付
          </Button>
        </div>
      </Modal>
    </div>
  )
}
