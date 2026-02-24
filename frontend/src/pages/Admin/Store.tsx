import { useEffect, useState, useRef, useCallback } from 'react'
import { Table, Button, Input, Tabs, Tag, Card, Typography, message, Modal, Space, Form, Select, Spin, Result } from 'antd'
import { SearchOutlined, ShoppingCartOutlined, LinkOutlined, CheckCircleOutlined, UserOutlined, LoginOutlined, LogoutOutlined, DollarOutlined, LoadingOutlined, CreditCardOutlined } from '@ant-design/icons'
import * as adminApi from '../../api/admin'

const { Title, Text, Paragraph } = Typography

export default function Store() {
  const [loading, setLoading] = useState(false)
  const [data, setData] = useState<any[]>([])
  const [keyword, setKeyword] = useState('')
  const [activeTab, setActiveTab] = useState('all')
  const [purchasing, setPurchasing] = useState(false)

  /** Store 账号状态 */
  const [storeToken, setStoreToken] = useState<string>(localStorage.getItem('store_token') || '')
  const [storeUser, setStoreUser] = useState<any>(null)
  const [showLoginModal, setShowLoginModal] = useState(false)
  const [loginMode, setLoginMode] = useState<'login' | 'register'>('login')
  const [loginLoading, setLoginLoading] = useState(false)

  /** 支付流程状态 */
  const [paymentModal, setPaymentModal] = useState<{
    visible: boolean
    pluginId?: string
    pluginName?: string
    price?: number
    gateways?: Array<{ name: string; display_name: string }>
    orderNo?: string
    paymentUrl?: string
    status?: 'choosing' | 'paying' | 'success' | 'expired'
  }>({ visible: false })
  const [selectedGateway, setSelectedGateway] = useState('epay')
  const [selectedPayType, setSelectedPayType] = useState('alipay')
  const [paymentCreating, setPaymentCreating] = useState(false)
  const pollTimerRef = useRef<any>(null)

  /** 购买成功弹窗 */
  const [purchaseResult, setPurchaseResult] = useState<{
    visible: boolean
    pluginName?: string
    price?: number
    message?: string
  }>({ visible: false })

  const loadData = async () => {
    setLoading(true)
    try {
      const categoryMap: Record<string, string | undefined> = {
        all: undefined, enterprise: 'enterprise', official: 'official',
        third_party: 'third_party', free: 'free',
      }
      const typeMap: Record<string, string | undefined> = {
        extension: 'extension', payment: 'payment', theme: 'theme',
      }
      const res = await adminApi.getStorePlugins({
        category: categoryMap[activeTab],
        type: typeMap[activeTab],
        keyword: keyword || undefined,
        store_token: storeToken || undefined,
      })
      setData(res.items || [])
    } catch {
      setData([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { loadData() }, [activeTab, storeToken])

  /** 清理轮询定时器 */
  useEffect(() => {
    return () => {
      if (pollTimerRef.current) clearInterval(pollTimerRef.current)
    }
  }, [])

  /** Store 账号登录 */
  const handleStoreLogin = async (values: any) => {
    setLoginLoading(true)
    try {
      const res = await adminApi.storeLogin(values.account, values.password)
      if (res.success && res.access_token) {
        setStoreToken(res.access_token)
        setStoreUser(res.user)
        localStorage.setItem('store_token', res.access_token)
        setShowLoginModal(false)
        message.success(`欢迎回来, ${res.user?.username || '用户'}`)
      } else {
        message.error(res.message || '登录失败')
      }
    } catch (e: any) {
      message.error(e.message || '登录失败')
    } finally {
      setLoginLoading(false)
    }
  }

  /** Store 账号注册 */
  const handleStoreRegister = async (values: any) => {
    setLoginLoading(true)
    try {
      const res = await adminApi.storeRegister(values.username, values.email, values.password)
      if (res.success && res.access_token) {
        setStoreToken(res.access_token)
        setStoreUser(res.user)
        localStorage.setItem('store_token', res.access_token)
        setShowLoginModal(false)
        message.success('注册成功，欢迎加入！')
      } else {
        message.error(res.message || '注册失败')
      }
    } catch (e: any) {
      message.error(e.message || '注册失败')
    } finally {
      setLoginLoading(false)
    }
  }

  /** 退出 Store 账号 */
  const handleStoreLogout = () => {
    setStoreToken('')
    setStoreUser(null)
    localStorage.removeItem('store_token')
    message.info('已退出 Store 账号')
    loadData()
  }

  /** 轮询支付状态 */
  const startPollingPayment = useCallback((orderNo: string) => {
    if (pollTimerRef.current) clearInterval(pollTimerRef.current)

    let attempts = 0
    const maxAttempts = 120 // 120次 × 3秒 = 最长6分钟

    pollTimerRef.current = setInterval(async () => {
      attempts++
      if (attempts > maxAttempts) {
        clearInterval(pollTimerRef.current)
        pollTimerRef.current = null
        setPaymentModal(prev => ({ ...prev, status: 'expired' }))
        return
      }

      try {
        const res = await adminApi.queryPaymentStatus(orderNo, storeToken)
        if (res.status === 'paid') {
          clearInterval(pollTimerRef.current)
          pollTimerRef.current = null
          setPaymentModal(prev => ({ ...prev, status: 'success' }))
          message.success('支付成功！')
          loadData()
        } else if (res.status === 'expired' || res.status === 'closed') {
          clearInterval(pollTimerRef.current)
          pollTimerRef.current = null
          setPaymentModal(prev => ({ ...prev, status: 'expired' }))
        }
      } catch {
        // 网络错误，继续轮询
      }
    }, 3000)
  }, [storeToken])

  /** 购买插件 */
  const handlePurchase = async (pluginId: string, pluginName: string, isFree: boolean, price: number) => {
    if (isFree) {
      try {
        const res = await adminApi.installFromStore(pluginId)
        message.success(res.message)
      } catch (e: any) {
        message.error(e.message || '安装失败')
      }
      return
    }

    if (!storeToken) {
      message.warning('请先登录 Store 账号后再购买')
      setShowLoginModal(true)
      return
    }

    setPurchasing(true)
    try {
      const res = await adminApi.purchasePlugin(pluginId, storeToken)

      if (res.require_payment) {
        // 付费插件 → 打开支付弹窗
        setPaymentModal({
          visible: true,
          pluginId,
          pluginName: res.plugin_name || pluginName,
          price: res.price || price,
          gateways: res.gateways || [],
          status: 'choosing',
        })
      } else if (res.success !== false) {
        // 免费或未配置支付 → 直接成功
        setPurchaseResult({
          visible: true,
          pluginName: res.plugin_name || pluginName,
          price: res.price,
          message: '购买成功！插件已绑定到您的 Store 账号。',
        })
        loadData()
      } else {
        message.error(res.message || '购买失败')
      }
    } catch (e: any) {
      message.error(e.message || '购买失败，请检查商店服务器是否正常')
    } finally {
      setPurchasing(false)
    }
  }

  const handleInstall = async (pluginId: string) => {
    try {
      const res = await adminApi.installFromStore(pluginId, storeToken)
      message.success(res.message)
    } catch (e: any) {
      message.error(e.message || '安装失败')
    }
  }

  /** 创建支付订单 → 打开支付页面 */
  const handleCreatePayment = async () => {
    if (!paymentModal.pluginId) return
    setPaymentCreating(true)
    try {
      const res = await adminApi.createPaymentOrder({
        plugin_id: paymentModal.pluginId,
        store_token: storeToken,
        gateway: selectedGateway,
        pay_type: selectedPayType,
      })
      if (res.success && res.payment_url) {
        // 打开支付页面
        window.open(res.payment_url, '_blank')
        setPaymentModal(prev => ({
          ...prev,
          orderNo: res.order_no,
          paymentUrl: res.payment_url,
          status: 'paying',
        }))
        // 开始轮询
        startPollingPayment(res.order_no!)
      } else {
        message.error(res.message || '创建支付订单失败')
      }
    } catch (e: any) {
      message.error(e.message || '创建支付订单失败')
    } finally {
      setPaymentCreating(false)
    }
  }

  /** 关闭支付弹窗 */
  const closePaymentModal = () => {
    if (pollTimerRef.current) {
      clearInterval(pollTimerRef.current)
      pollTimerRef.current = null
    }
    setPaymentModal({ visible: false })
  }

  const typeTagColor: Record<string, string> = {
    payment: 'green', theme: 'purple', extension: 'blue', notify: 'orange', delivery: 'cyan',
  }

  const columns = [
    {
      title: '软件名称',
      key: 'name',
      width: 200,
      render: (_: any, r: any) => (
        <div className="flex items-center gap-2">
          {r.icon && <img src={r.icon} alt="" className="w-8 h-8 rounded" />}
          <span className="font-medium">{r.name}</span>
        </div>
      ),
    },
    { title: '开发商', dataIndex: 'author', width: 100 },
    {
      title: '类型',
      dataIndex: 'type',
      width: 100,
      render: (t: string) => <Tag color={typeTagColor[t] || 'default'}>{t}</Tag>,
    },
    {
      title: '简介',
      dataIndex: 'description',
      ellipsis: true,
    },
    {
      title: '官网',
      dataIndex: 'website',
      width: 120,
      render: (url: string) => url ? <a href={url} target="_blank" rel="noreferrer"><LinkOutlined /> 访问</a> : '-',
    },
    { title: '版本', dataIndex: 'version', width: 80 },
    {
      title: '价格',
      dataIndex: 'price',
      width: 100,
      render: (p: number, r: any) => r.is_free ? <Tag color="green">免费</Tag> : <span className="text-red-500 font-medium">¥{p}</span>,
    },
    {
      title: '状态',
      key: 'status',
      width: 80,
      render: (_: any, r: any) => r.purchased ? <Tag color="green">已购</Tag> : null,
    },
    {
      title: '操作',
      key: 'action',
      width: 120,
      render: (_: any, r: any) => {
        if (r.purchased) {
          return (
            <Button
              type="primary"
              size="small"
              icon={<ShoppingCartOutlined />}
              onClick={() => handleInstall(r.id)}
            >
              安装
            </Button>
          )
        }
        return (
          <Button
            type="primary"
            size="small"
            icon={r.is_free ? <ShoppingCartOutlined /> : <CreditCardOutlined />}
            loading={purchasing}
            onClick={() => handlePurchase(r.id, r.name, r.is_free, r.price)}
          >
            {r.is_free ? '安装' : '立即购买'}
          </Button>
        )
      },
    },
  ]

  const tabItems = [
    { key: 'all', label: '全部' },
    { key: 'enterprise', label: '企业版应用' },
    { key: 'official', label: '官方应用' },
    { key: 'third_party', label: '第三方应用' },
    { key: 'extension', label: '通用插件' },
    { key: 'payment', label: '支付接口' },
    { key: 'theme', label: '主题/模版' },
    { key: 'free', label: '免费应用' },
  ]

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0 }}>应用商店</Title>
        <div>
          {storeToken ? (
            <Space>
              <Tag icon={<UserOutlined />} color="green">
                {storeUser?.username || 'Store 账号已登录'}
              </Tag>
              <Button size="small" icon={<LogoutOutlined />} onClick={handleStoreLogout}>
                退出
              </Button>
            </Space>
          ) : (
            <Button
              type="primary"
              icon={<LoginOutlined />}
              onClick={() => setShowLoginModal(true)}
            >
              登录 Store 账号
            </Button>
          )}
        </div>
      </div>

      <Card className="rounded-xl border-0 shadow-sm">
        <div className="flex gap-2 mb-4 justify-center">
          <Input placeholder="搜索应用..." value={keyword} onChange={e => setKeyword(e.target.value)} onPressEnter={loadData} allowClear style={{ width: 300 }} />
          <Button type="primary" icon={<SearchOutlined />} onClick={loadData}>查询</Button>
        </div>
        <Tabs activeKey={activeTab} onChange={setActiveTab} items={tabItems} className="!mb-2" />
        <Table rowKey="id" loading={loading} dataSource={data} columns={columns} pagination={false} size="middle"
          locale={{ emptyText: data.length === 0 && !loading ? '插件商店服务器暂未部署，请先部署 lecfaka-store' : undefined }}
        />
      </Card>

      {/* Store 账号登录/注册弹窗 */}
      <Modal
        title={loginMode === 'login' ? '登录 Store 账号' : '注册 Store 账号'}
        open={showLoginModal}
        onCancel={() => setShowLoginModal(false)}
        footer={null}
        width={400}
      >
        {loginMode === 'login' ? (
          <Form layout="vertical" onFinish={handleStoreLogin} style={{ marginTop: 16 }}>
            <Form.Item name="account" label="邮箱或用户名" rules={[{ required: true, message: '请输入邮箱或用户名' }]}>
              <Input placeholder="请输入邮箱或用户名" />
            </Form.Item>
            <Form.Item name="password" label="密码" rules={[{ required: true, message: '请输入密码' }]}>
              <Input.Password placeholder="请输入密码" />
            </Form.Item>
            <Form.Item>
              <Button type="primary" htmlType="submit" loading={loginLoading} block>登录</Button>
            </Form.Item>
            <div style={{ textAlign: 'center' }}>
              <Text type="secondary">还没有 Store 账号？</Text>
              <Button type="link" onClick={() => setLoginMode('register')}>立即注册</Button>
            </div>
          </Form>
        ) : (
          <Form layout="vertical" onFinish={handleStoreRegister} style={{ marginTop: 16 }}>
            <Form.Item name="username" label="用户名" rules={[{ required: true, message: '请输入用户名' }]}>
              <Input placeholder="请输入用户名" />
            </Form.Item>
            <Form.Item name="email" label="邮箱" rules={[{ required: true, type: 'email', message: '请输入有效邮箱' }]}>
              <Input placeholder="请输入邮箱" />
            </Form.Item>
            <Form.Item name="password" label="密码" rules={[{ required: true, min: 6, message: '密码至少6位' }]}>
              <Input.Password placeholder="设置密码（至少6位）" />
            </Form.Item>
            <Form.Item>
              <Button type="primary" htmlType="submit" loading={loginLoading} block>注册</Button>
            </Form.Item>
            <div style={{ textAlign: 'center' }}>
              <Text type="secondary">已有账号？</Text>
              <Button type="link" onClick={() => setLoginMode('login')}>去登录</Button>
            </div>
          </Form>
        )}
      </Modal>

      {/* 支付弹窗 */}
      <Modal
        title={
          <Space>
            <DollarOutlined style={{ color: '#1890ff' }} />
            <span>购买插件</span>
          </Space>
        }
        open={paymentModal.visible}
        onCancel={closePaymentModal}
        footer={null}
        width={520}
        maskClosable={false}
      >
        {paymentModal.status === 'choosing' && (
          <div style={{ padding: '16px 0' }}>
            <div style={{
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              borderRadius: 12,
              padding: '20px 24px',
              color: '#fff',
              marginBottom: 20,
            }}>
              <div style={{ fontSize: 14, opacity: 0.9, marginBottom: 4 }}>购买插件</div>
              <div style={{ fontSize: 20, fontWeight: 600 }}>{paymentModal.pluginName}</div>
              <div style={{ fontSize: 28, fontWeight: 700, marginTop: 8 }}>¥{paymentModal.price}</div>
            </div>

            <Form layout="vertical">
              <Form.Item label="支付网关">
                <Select
                  value={selectedGateway}
                  onChange={setSelectedGateway}
                  options={(paymentModal.gateways || []).map(g => ({
                    label: g.display_name,
                    value: g.name,
                  }))}
                  style={{ width: '100%' }}
                />
              </Form.Item>
              <Form.Item label="支付方式">
                <Select
                  value={selectedPayType}
                  onChange={setSelectedPayType}
                  options={[
                    { label: '💳 支付宝', value: 'alipay' },
                    { label: '💬 微信支付', value: 'wxpay' },
                    { label: '🐧 QQ 支付', value: 'qqpay' },
                  ]}
                  style={{ width: '100%' }}
                />
              </Form.Item>
            </Form>

            <Button
              type="primary"
              size="large"
              block
              loading={paymentCreating}
              icon={<CreditCardOutlined />}
              onClick={handleCreatePayment}
              style={{ height: 48, fontSize: 16, borderRadius: 8 }}
            >
              确认支付 ¥{paymentModal.price}
            </Button>
          </div>
        )}

        {paymentModal.status === 'paying' && (
          <div style={{ textAlign: 'center', padding: '40px 0' }}>
            <Spin indicator={<LoadingOutlined style={{ fontSize: 48 }} spin />} />
            <div style={{ marginTop: 24, fontSize: 16, fontWeight: 500 }}>等待支付...</div>
            <Paragraph type="secondary" style={{ marginTop: 12 }}>
              支付页面已在新窗口打开，请在支付页面完成付款。
              <br />
              支付完成后此处将自动更新。
            </Paragraph>
            <Button
              type="link"
              onClick={() => {
                if (paymentModal.paymentUrl) {
                  window.open(paymentModal.paymentUrl, '_blank')
                }
              }}
            >
              重新打开支付页面
            </Button>
            <br />
            <Button type="text" danger onClick={closePaymentModal} style={{ marginTop: 16 }}>
              取消支付
            </Button>
          </div>
        )}

        {paymentModal.status === 'success' && (
          <Result
            status="success"
            title="支付成功！"
            subTitle={`${paymentModal.pluginName} 已绑定到您的 Store 账号`}
            extra={[
              <Button type="primary" key="done" onClick={closePaymentModal}>
                完成
              </Button>,
            ]}
          />
        )}

        {paymentModal.status === 'expired' && (
          <Result
            status="warning"
            title="支付超时"
            subTitle="订单已过期，请重新发起购买"
            extra={[
              <Button type="primary" key="retry" onClick={() => {
                closePaymentModal()
                if (paymentModal.pluginId) {
                  handlePurchase(paymentModal.pluginId, paymentModal.pluginName || '', false, paymentModal.price || 0)
                }
              }}>
                重新购买
              </Button>,
              <Button key="cancel" onClick={closePaymentModal}>
                关闭
              </Button>,
            ]}
          />
        )}
      </Modal>

      {/* 免费插件 / 未配置支付时的购买成功弹窗 */}
      <Modal
        title={
          <Space>
            <CheckCircleOutlined style={{ color: '#52c41a', fontSize: 20 }} />
            <span>购买成功</span>
          </Space>
        }
        open={purchaseResult.visible}
        onCancel={() => setPurchaseResult({ visible: false })}
        footer={[
          <Button key="close" type="primary" onClick={() => setPurchaseResult({ visible: false })}>
            确定
          </Button>,
        ]}
        width={480}
      >
        <div style={{ padding: '16px 0' }}>
          <Paragraph>
            <Text strong>插件：</Text> {purchaseResult.pluginName}
          </Paragraph>
          {purchaseResult.price !== undefined && purchaseResult.price > 0 && (
            <Paragraph>
              <Text strong>价格：</Text> <Text type="danger">¥{purchaseResult.price}</Text>
            </Paragraph>
          )}

          <div style={{
            background: '#f6ffed',
            border: '1px solid #b7eb8f',
            borderRadius: 8,
            padding: '16px 20px',
            margin: '16px 0',
            textAlign: 'center',
          }}>
            <Text style={{ fontSize: 14 }}>
              🎉 {purchaseResult.message || '购买成功！'}
            </Text>
            <br />
            <Text type="secondary" style={{ fontSize: 12, marginTop: 8, display: 'block' }}>
              插件已绑定到您的 Store 账号。您可以在 Store 官网的控制台管理域名绑定。
            </Text>
          </div>

          <Paragraph type="secondary" style={{ fontSize: 13 }}>
            请前往 <Text strong>系统管理 → 插件管理</Text> 找到该插件并启用。
          </Paragraph>
        </div>
      </Modal>
    </div>
  )
}
