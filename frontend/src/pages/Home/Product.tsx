import { useEffect, useState, useMemo } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import DOMPurify from 'dompurify'
import {
  Card, Button, Input, Form, Spin, message, Modal,
  Typography, Tag, Divider, InputNumber, Avatar, Dropdown
} from 'antd'
import {
  ShoppingCartOutlined, SearchOutlined,
  MinusOutlined, PlusOutlined,
  WechatOutlined, AlipayCircleOutlined, WalletOutlined,
  UserOutlined, LogoutOutlined, SettingOutlined
} from '@ant-design/icons'
import { getCommodityDetail, getPayments, CommodityDetail, PaymentMethod, SkuConfig } from '../../api/shop'
import { createOrder, getOrder } from '../../api/order'
import { useAuthStore } from '../../store'
import ParticleNetwork from '../../components/ParticleNetwork'

const { Title, Paragraph, Text } = Typography

// 支付方式图标映射
const PaymentIcon = ({ handler, code }: { handler: string; code?: string }) => {
  if (handler === '#balance') return <WalletOutlined className="text-lg" />
  const key = (code || handler || '').toLowerCase()
  if (key.includes('wxpay') || key.includes('wechat')) return <WechatOutlined className="text-lg text-green-500" />
  if (key.includes('alipay')) return <AlipayCircleOutlined className="text-lg text-blue-500" />
  if (key.includes('qqpay')) return <WalletOutlined className="text-lg text-blue-400" />
  if (key.includes('usdt')) return <WalletOutlined className="text-lg text-orange-500" />
  return <WalletOutlined className="text-lg" />
}

export default function Product() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [form] = Form.useForm()

  const [commodity, setCommodity] = useState<CommodityDetail | null>(null)
  const [payments, setPayments] = useState<PaymentMethod[]>([])
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [quantity, setQuantity] = useState(1)
  const [selectedPayment, setSelectedPayment] = useState<number | null>(null)
  const [captchaCode, setCaptchaCode] = useState('')
  const [captchaImg, setCaptchaImg] = useState('')

  // 二维码支付弹窗
  const [qrcodeModal, setQrcodeModal] = useState(false)
  const [qrcodeUrl, setQrcodeUrl] = useState('')
  const [qrcodeTradeNo, setQrcodeTradeNo] = useState('')
  const [qrcodeChannel, setQrcodeChannel] = useState('')
  const [pollingTimer, setPollingTimer] = useState<ReturnType<typeof setInterval> | null>(null)

  // 种类和SKU选择
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null)
  const [selectedSkus, setSelectedSkus] = useState<Record<string, string>>({})

  // 粒子特效开关
  const [particleEnabled, setParticleEnabled] = useState(true)

  const { user, logout } = useAuthStore()

  const handleLogout = () => {
    logout()
    navigate('/')
  }

  const userMenuItems: any[] = [
    { key: 'center', label: '个人中心', icon: <UserOutlined />, onClick: () => navigate('/user') },
    { key: 'orders', label: '我的订单', icon: <ShoppingCartOutlined />, onClick: () => navigate('/user/orders') },
    user?.is_admin ? { key: 'admin', label: '管理后台', icon: <SettingOutlined />, onClick: () => navigate('/admin') } : null,
    { type: 'divider' as const },
    { key: 'logout', label: '退出登录', icon: <LogoutOutlined />, onClick: handleLogout, danger: true },
  ].filter(Boolean)

  useEffect(() => {
    if (id) {
      loadData()
      refreshCaptcha()
    }
  }, [id])

  // 设置默认选中的种类
  useEffect(() => {
    if (commodity?.categories && commodity.categories.length > 0 && !selectedCategory) {
      setSelectedCategory(commodity.categories[0].name)
    }
  }, [commodity?.categories])

  // 设置默认选中的SKU
  useEffect(() => {
    if (commodity?.sku_config && commodity.sku_config.length > 0) {
      const groups = new Map<string, SkuConfig[]>()
      commodity.sku_config.forEach(sku => {
        if (!groups.has(sku.group)) {
          groups.set(sku.group, [])
        }
        groups.get(sku.group)?.push(sku)
      })

      const defaultSkus: Record<string, string> = {}
      groups.forEach((options, group) => {
        if (options.length > 0) {
          defaultSkus[group] = options[0].option
        }
      })
      setSelectedSkus(defaultSkus)
    }
  }, [commodity?.sku_config])

  const loadData = async () => {
    setLoading(true)
    try {
      const [commodityData, paymentsData] = await Promise.all([
        getCommodityDetail(Number(id)),
        getPayments(),
      ])
      setCommodity(commodityData)
      setPayments(paymentsData)
      // 默认选择第一个支付方式
      if (paymentsData.length > 0) {
        setSelectedPayment(paymentsData[0].id)
      }
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  const refreshCaptcha = () => {
    const code = Math.floor(1000 + Math.random() * 9000).toString()
    setCaptchaCode(code)
    setCaptchaImg(code)
  }

  // 获取当前种类的基础价格
  const categoryPrice = useMemo(() => {
    if (commodity?.categories && selectedCategory) {
      const cat = commodity.categories.find(c => c.name === selectedCategory)
      if (cat) return cat.price
    }
    return null
  }, [commodity?.categories, selectedCategory])

  // 获取当前批发规则（种类批发规则优先，如果选择了种类则不使用通用规则）
  const wholesalePrices = useMemo(() => {
    // 如果选择了种类，只使用该种类的批发规则
    if (selectedCategory && commodity?.category_wholesale) {
      const catWholesale = commodity.category_wholesale[selectedCategory]
      if (catWholesale && catWholesale.length > 0) return catWholesale
      // 如果选择了种类但没有该种类的批发规则，返回空数组（不使用通用规则）
      return []
    }
    // 没有选择种类时（或没有种类配置），使用通用批发规则
    if (!commodity?.categories || commodity.categories.length === 0) {
      return commodity?.wholesale || []
    }
    return []
  }, [commodity?.wholesale, commodity?.category_wholesale, commodity?.categories, selectedCategory])

  // SKU 分组
  const skuGroups = useMemo(() => {
    if (!commodity?.sku_config) return new Map<string, SkuConfig[]>()
    const groups = new Map<string, SkuConfig[]>()
    commodity.sku_config.forEach(sku => {
      if (!groups.has(sku.group)) {
        groups.set(sku.group, [])
      }
      groups.get(sku.group)?.push(sku)
    })
    return groups
  }, [commodity?.sku_config])

  // SKU 加价
  const skuExtraPrice = useMemo(() => {
    if (!commodity?.sku_config) return 0
    let extra = 0
    Object.entries(selectedSkus).forEach(([group, option]) => {
      const sku = commodity.sku_config?.find(s => s.group === group && s.option === option)
      if (sku) extra += sku.extra_price
    })
    return extra
  }, [commodity?.sku_config, selectedSkus])

  // 计算当前单价
  const currentUnitPrice = useMemo(() => {
    // 基础价格：种类价格 > 会员价 > 普通价
    const originalPrice = categoryPrice ?? (user ? commodity?.user_price : commodity?.price) ?? 0
    let finalPrice = originalPrice

    // 加上 SKU 加价
    finalPrice += skuExtraPrice

    // 应用批发规则（找到适用的最大数量档位）
    let appliedRule: typeof wholesalePrices[0] | null = null
    for (const wp of wholesalePrices) {
      if (quantity >= wp.quantity) {
        appliedRule = wp
      }
    }

    if (appliedRule) {
      if (appliedRule.type === 'percent' && appliedRule.discount_percent) {
        // 百分比折扣：discount_percent 是折扣后的百分比（如90表示9折）
        finalPrice = (originalPrice * appliedRule.discount_percent / 100) + skuExtraPrice
      } else if (appliedRule.type === 'fixed' && appliedRule.price !== undefined) {
        // 固定价格
        finalPrice = appliedRule.price + skuExtraPrice
      }
    }

    return finalPrice
  }, [quantity, wholesalePrices, commodity, user, categoryPrice, skuExtraPrice])

  // 计算总价
  const totalPrice = useMemo(() => {
    return (currentUnitPrice * quantity).toFixed(2)
  }, [currentUnitPrice, quantity])

  const handleSubmit = async (values: any) => {
    if (!commodity) return

    // 验证码校验
    if (values.captcha !== captchaCode) {
      message.error('验证码错误')
      refreshCaptcha()
      return
    }

    // 检查是否需要登录
    if (commodity.only_user === 1 && !user) {
      message.warning('该商品需要登录后购买')
      navigate('/login')
      return
    }

    if (!selectedPayment) {
      message.warning('请选择支付方式')
      return
    }

    setSubmitting(true)
    try {
      const res = await createOrder({
        commodity_id: commodity.id,
        quantity: quantity,
        payment_id: selectedPayment,
        contact: values.contact,
        password: values.password,
        coupon: values.coupon,
        race: selectedCategory || undefined,
      })

      // 余额支付成功
      if (res.status === 1) {
        Modal.success({
          title: '支付成功',
          content: (
            <div>
              <p>订单号：{res.trade_no}</p>
              <p>订单金额：¥{res.amount}</p>
              {res.secret && (
                <div className="mt-4 p-3 bg-gray-100 rounded">
                  <p className="font-bold mb-2">卡密信息：</p>
                  <pre className="whitespace-pre-wrap break-all text-sm">{res.secret}</pre>
                </div>
              )}
            </div>
          ),
          onOk: () => navigate(`/query?trade_no=${res.trade_no}`),
        })
      } else if (res.payment_type === 'qrcode' && res.extra?.qrcode_url) {
        // 二维码支付 - 显示支付弹窗
        setQrcodeUrl(res.extra.qrcode_url)
        setQrcodeTradeNo(res.trade_no)
        setQrcodeChannel(res.extra?.channel || 'wxpay')
        setQrcodeModal(true)
        // 开始轮询支付状态
        startPolling(res.trade_no)
      } else if (res.payment_type === 'form' && res.extra?.form_data) {
        // 表单提交方式
        const formEl = document.createElement('form')
        formEl.method = 'POST'
        formEl.action = res.payment_url || ''
        formEl.style.display = 'none'
        Object.entries(res.extra.form_data).forEach(([key, val]) => {
          const input = document.createElement('input')
          input.type = 'hidden'
          input.name = key
          input.value = String(val)
          formEl.appendChild(input)
        })
        document.body.appendChild(formEl)
        formEl.submit()
      } else if (res.payment_url) {
        // 跳转支付
        window.location.href = res.payment_url
      } else {
        message.success('下单成功！')
        navigate(`/query?trade_no=${res.trade_no}`)
      }
    } catch (e) {
      console.error(e)
      refreshCaptcha()
    } finally {
      setSubmitting(false)
    }
  }

  // 轮询订单支付状态
  const startPolling = (tradeNo: string) => {
    // 清除旧的定时器
    if (pollingTimer) clearInterval(pollingTimer)

    const timer = setInterval(async () => {
      try {
        const order = await getOrder(tradeNo)
        if (order.status === 1) {
          // 支付成功
          clearInterval(timer)
          setPollingTimer(null)
          setQrcodeModal(false)
          Modal.success({
            title: '支付成功',
            content: (
              <div>
                <p>订单号：{tradeNo}</p>
                {order.secret && (
                  <div className="mt-4 p-3 bg-gray-100 rounded">
                    <p className="font-bold mb-2">卡密信息：</p>
                    <pre className="whitespace-pre-wrap break-all text-sm">{order.secret}</pre>
                  </div>
                )}
              </div>
            ),
            onOk: () => navigate(`/query?trade_no=${tradeNo}`),
          })
        }
      } catch (e) {
        // 忽略轮询错误
      }
    }, 3000) // 每3秒检查一次

    setPollingTimer(timer)
  }

  // 关闭二维码弹窗时清除轮询
  const closeQrcodeModal = () => {
    if (pollingTimer) {
      clearInterval(pollingTimer)
      setPollingTimer(null)
    }
    setQrcodeModal(false)
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-screen bg-gradient-to-br from-pink-50 to-purple-50">
        <Spin size="large" />
      </div>
    )
  }

  if (!commodity) {
    return (
      <div className="flex justify-center items-center min-h-screen bg-gradient-to-br from-pink-50 to-purple-50">
        <Text>商品不存在</Text>
      </div>
    )
  }


  return (
    <div className="min-h-screen bg-gradient-to-br from-pink-50 to-purple-50">
      {/* 顶部导航 */}
      <header className="bg-white shadow-sm px-6 h-16 flex items-center">
        <div className="max-w-6xl mx-auto w-full flex items-center justify-between">
          <Link to="/" className="flex items-center gap-3 no-underline hover:no-underline">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center flex-shrink-0">
              <ShoppingCartOutlined className="text-white text-xl" />
            </div>
            <span className="text-lg font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-purple-600">LecFaka</span>
          </Link>
          <nav className="flex items-center gap-6">
            <Link
              to="/"
              className="no-underline px-4 py-1.5 rounded-full border border-gray-200 text-gray-700 hover:text-pink-500 hover:border-pink-300 hover:bg-pink-50 transition-all flex items-center gap-1 font-medium"
            >
              <ShoppingCartOutlined /> 购物
            </Link>
            <Link
              to="/query"
              className="no-underline px-4 py-1.5 rounded-full border border-gray-200 text-gray-700 hover:text-pink-500 hover:border-pink-300 hover:bg-pink-50 transition-all flex items-center gap-1 font-medium"
            >
              <SearchOutlined /> 订单查询
            </Link>
          </nav>
          <div className="flex items-center gap-4">
            {user ? (
              <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
                <div className="flex items-center gap-2 cursor-pointer hover:bg-gray-100 rounded-lg px-3 py-1.5 transition-colors">
                  <Avatar
                    src={user.avatar}
                    icon={<UserOutlined />}
                    className="bg-gradient-to-br from-blue-500 to-purple-600"
                  />
                  <div className="hidden md:block">
                    <div className="text-sm font-medium text-gray-700">{user.username}</div>
                    <div className="text-xs text-orange-500">余额: ¥{(user.balance || 0).toFixed(2)}</div>
                  </div>
                </div>
              </Dropdown>
            ) : (
              <>
                <Link to="/login">
                  <Button className="rounded-lg border-purple-300 text-purple-600 hover:border-purple-500 hover:text-purple-700">登录</Button>
                </Link>
                <Link to="/register">
                  <Button type="primary" className="bg-gradient-to-r from-blue-500 to-purple-600 border-0">创建账号</Button>
                </Link>
              </>
            )}
          </div>
        </div>
      </header>


      <div className="max-w-6xl mx-auto p-6">
        <div className="flex flex-col lg:flex-row gap-6 lg:items-stretch">
          {/* 左侧：商品图片 + 粒子网格背景 - 高度与右侧同步 */}
          <div className="lg:w-1/2 flex flex-col">
            <div className="border-0 shadow-lg rounded-2xl overflow-hidden relative flex-1 bg-white">
              {/* 粒子网格连线特效 - 绝对定位覆盖整个区域 */}
              {particleEnabled && (
                <div className="absolute inset-0">
                  <ParticleNetwork
                    particleCount={120}
                    lineColor="rgba(236, 72, 153, 0.4)"
                    particleColor="rgba(236, 72, 153, 0.7)"
                    maxDistance={100}
                    mouseRadius={180}
                  />
                </div>
              )}

              {/* 粒子特效开关 */}
              <div
                className="absolute top-3 right-3 z-20 cursor-pointer select-none"
                onClick={() => setParticleEnabled(!particleEnabled)}
                title={particleEnabled ? '关闭粒子特效' : '开启粒子特效'}
              >
                <div className={`w-10 h-5 rounded-full transition-colors duration-300 flex items-center px-0.5 ${particleEnabled ? 'bg-pink-400' : 'bg-gray-300'}`}>
                  <div className={`w-4 h-4 bg-white rounded-full shadow transition-transform duration-300 ${particleEnabled ? 'translate-x-5' : 'translate-x-0'}`} />
                </div>
              </div>

              {/* 图片容器 - 绝对定位居中，88%宽度 */}
              <div className="absolute inset-0 flex items-center justify-center p-4 z-10 pointer-events-none">
                <div
                  className="flex items-center justify-center rounded-2xl overflow-hidden bg-white shadow-xl border border-gray-100 pointer-events-auto"
                  style={{ width: '88%', aspectRatio: '1/1', maxWidth: '500px' }}
                >
                  {commodity.cover ? (
                    <img
                      src={commodity.cover}
                      alt={commodity.name}
                      className="max-w-full max-h-full object-contain p-6"
                    />
                  ) : (
                    <div className="text-8xl opacity-30">📦</div>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* 右侧：商品信息和购买表单 */}
          <div className="lg:w-1/2 lg:flex lg:flex-col">
            <Card className="border-0 shadow-lg rounded-2xl flex-1">
              {/* 商品标题 */}
              <Title level={4} className="!mb-2">{commodity.name}</Title>

              {/* 标签 */}
              <div className="flex items-center gap-2 mb-4">
                <Tag color="cyan">
                  {commodity.delivery_way === 0 ? '自动发货' : '手动发货'}
                </Tag>
                <Tag color="pink">已售 {commodity.sold_count || 0}</Tag>
                <Tag color={commodity.stock > 0 ? 'green' : 'red'}>
                  库存 {commodity.stock > 0 ? commodity.stock : '售罄'}
                </Tag>
              </div>

              {/* 价格 */}
              <div className="text-pink-500 text-3xl font-bold mb-4">
                ¥{currentUnitPrice.toFixed(2)}
                {skuExtraPrice > 0 && (
                  <span className="text-sm text-gray-400 ml-2">(含规格加价 ¥{skuExtraPrice})</span>
                )}
              </div>

              {/* 购买表单 */}
              <Form form={form} layout="vertical" onFinish={handleSubmit}>
                {/* 商品种类选择 */}
                {commodity.categories && commodity.categories.length > 0 && (
                  <Form.Item label={<span className="text-gray-500">商品种类</span>}>
                    <div className="flex flex-wrap gap-2">
                      {commodity.categories.map((cat) => (
                        <Button
                          key={cat.name}
                          type={selectedCategory === cat.name ? 'primary' : 'default'}
                          onClick={() => setSelectedCategory(cat.name)}
                          className={`rounded-lg ${selectedCategory === cat.name ? 'bg-pink-500 border-pink-500' : ''}`}
                        >
                          {cat.name}
                          <span className="ml-1 text-xs opacity-75">¥{cat.price}</span>
                        </Button>
                      ))}
                    </div>
                  </Form.Item>
                )}

                {/* SKU 规格选择 */}
                {Array.from(skuGroups.entries()).map(([group, options]) => (
                  <Form.Item key={group} label={<span className="text-gray-500">{group}</span>}>
                    <div className="flex flex-wrap gap-2">
                      {options.map((sku) => (
                        <Button
                          key={sku.option}
                          type={selectedSkus[group] === sku.option ? 'primary' : 'default'}
                          onClick={() => setSelectedSkus({ ...selectedSkus, [group]: sku.option })}
                          className={`rounded-lg ${selectedSkus[group] === sku.option ? 'bg-pink-500 border-pink-500' : ''}`}
                        >
                          {sku.option}
                          {sku.extra_price > 0 && (
                            <span className="ml-1 text-xs opacity-75">+¥{sku.extra_price}</span>
                          )}
                        </Button>
                      ))}
                    </div>
                  </Form.Item>
                ))}

                {/* 邮箱地址 */}
                <Form.Item
                  name="contact"
                  label={<span className="text-gray-500">邮箱地址</span>}
                  rules={[{ required: true, message: '请输入邮箱地址' }]}
                >
                  <Input placeholder="请输入您的邮箱地址" className="rounded-lg" />
                </Form.Item>

                {/* 优惠券 */}
                <Form.Item
                  name="coupon"
                  label={<span className="text-gray-500">优惠券</span>}
                >
                  <Input placeholder="优惠券代码，没有则不填" className="rounded-lg" />
                </Form.Item>

                {/* 查询密码 */}
                <Form.Item
                  name="password"
                  label={<span className="text-gray-500">查询密码</span>}
                  rules={commodity.password_status === 1 ? [{ required: true, message: '请设置查询密码' }] : []}
                >
                  <Input.Password
                    placeholder="设置查询订单的密码"
                    className="rounded-lg"
                  />
                </Form.Item>

                {/* 购买数量 */}
                <Form.Item label={<span className="text-gray-500">购买数量</span>}>
                  <div className="flex items-center gap-2">
                    <Button
                      icon={<MinusOutlined />}
                      onClick={() => setQuantity(Math.max(commodity.minimum || 1, quantity - 1))}
                      className="rounded-lg bg-pink-100 border-pink-200 text-pink-500"
                    />
                    <InputNumber
                      value={quantity}
                      onChange={(v) => setQuantity(v || 1)}
                      min={commodity.minimum || 1}
                      max={commodity.maximum || commodity.stock || 999}
                      className="w-20 text-center"
                    />
                    <Button
                      icon={<PlusOutlined />}
                      onClick={() => setQuantity(Math.min(commodity.maximum || commodity.stock || 999, quantity + 1))}
                      className="rounded-lg bg-pink-100 border-pink-200 text-pink-500"
                    />
                  </div>
                </Form.Item>

                {/* 批发价格表 */}
                {wholesalePrices.length > 0 && (
                  <div className="bg-pink-50 rounded-lg p-3 mb-4">
                    <div className="text-pink-400 text-sm mb-2 font-medium">
                      批发优惠{selectedCategory && ` (${selectedCategory})`}
                    </div>
                    <div className="grid grid-cols-2 gap-2">
                      {wholesalePrices.map((wp, idx) => (
                        <div
                          key={idx}
                          className={`flex justify-between px-3 py-2 rounded ${quantity >= wp.quantity ? 'bg-pink-200 text-pink-600' : 'text-pink-400'}`}
                        >
                          <span>≥{wp.quantity}件</span>
                          <span>
                            {wp.type === 'percent'
                              ? `${wp.discount_percent}%`
                              : `¥${wp.price}/件`
                            }
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* 人机验证 */}
                <Form.Item
                  name="captcha"
                  label={<span className="text-gray-500">人机验证</span>}
                  rules={[{ required: true, message: '请输入验证码' }]}
                >
                  <div className="flex items-center gap-4">
                    <Input placeholder="图形验证码" className="flex-1 rounded-lg" />
                    <div
                      className="px-4 py-2 bg-pink-100 rounded-lg cursor-pointer select-none text-pink-500 font-bold text-lg tracking-widest"
                      onClick={refreshCaptcha}
                      title="点击刷新"
                    >
                      {captchaImg}
                    </div>
                  </div>
                </Form.Item>

                {/* 支付方式 */}
                <div className="mb-4">
                  <Text className="text-gray-500 block mb-2">支付方式</Text>
                  <div className="flex flex-wrap gap-2">
                    {payments.map((p) => (
                      <Button
                        key={p.id}
                        type={selectedPayment === p.id ? 'primary' : 'default'}
                        onClick={() => setSelectedPayment(p.id)}
                        className={`rounded-lg ${selectedPayment === p.id ? 'bg-pink-500 border-pink-500' : ''}`}
                        icon={<PaymentIcon handler={p.handler} code={p.code} />}
                      >
                        {p.name}
                      </Button>
                    ))}
                  </div>
                </div>

                {/* 提交按钮 */}
                <Button
                  type="primary"
                  htmlType="submit"
                  size="large"
                  loading={submitting}
                  disabled={commodity.stock === 0}
                  className="w-full h-12 rounded-lg bg-gradient-to-r from-pink-400 to-pink-500 border-0 text-lg font-bold"
                >
                  {commodity.stock === 0 ? '已售罄' : `立即购买 ¥${totalPrice}`}
                </Button>
              </Form>
            </Card>
          </div>
        </div>

        {/* 商品详情 */}
        <Card className="mt-6 border-0 shadow-lg rounded-2xl">
          <Title level={5} className="flex items-center gap-2 !mb-4">
            📦 宝贝详情
          </Title>
          <Divider className="!my-3" />
          {commodity.description ? (
            <div
              className="prose max-w-none"
              dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(commodity.description) }}
            />
          ) : (
            <Text type="secondary">暂无商品详情</Text>
          )}

          {commodity.leave_message && (
            <>
              <Divider />
              <Title level={5}>售后说明</Title>
              <Paragraph className="text-gray-500 whitespace-pre-wrap">
                {commodity.leave_message}
              </Paragraph>
            </>
          )}
        </Card>
      </div>

      {/* 二维码支付弹窗 */}
      <Modal
        open={qrcodeModal}
        onCancel={closeQrcodeModal}
        footer={null}
        centered
        width={420}
        closable
        title={null}
      >
        <div className="text-center py-4">
          {/* 支付方式标题 */}
          <div className="flex items-center justify-center gap-2 mb-4">
            {qrcodeChannel === 'wxpay' ? (
              <WechatOutlined className="text-2xl text-green-500" />
            ) : qrcodeChannel === 'alipay' ? (
              <AlipayCircleOutlined className="text-2xl text-blue-500" />
            ) : (
              <WalletOutlined className="text-2xl" />
            )}
            <span className="text-lg font-bold">
              {qrcodeChannel === 'wxpay' ? '微信支付' : qrcodeChannel === 'alipay' ? '支付宝支付' : '扫码支付'}
            </span>
          </div>

          {/* 金额 */}
          <div className="text-3xl font-bold text-pink-500 mb-4">
            ¥{totalPrice}
          </div>

          {/* 二维码图片 */}
          <div className="flex justify-center mb-4">
            <div className="p-3 bg-white border-2 border-gray-200 rounded-xl shadow-sm">
              <img
                src={qrcodeUrl}
                alt="支付二维码"
                className="w-56 h-56 object-contain"
                onError={(e) => {
                  (e.target as HTMLImageElement).src = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200"><text x="50%" y="50%" text-anchor="middle" dy=".3em" font-size="14">二维码加载失败</text></svg>'
                }}
              />
            </div>
          </div>

          {/* 提示信息 */}
          <div className="text-gray-500 text-sm mb-2">
            {qrcodeChannel === 'wxpay' ? '请使用微信扫一扫完成支付' :
              qrcodeChannel === 'alipay' ? '请使用支付宝扫一扫完成支付' :
                '请使用对应APP扫一扫完成支付'}
          </div>
          <div className="text-gray-400 text-xs">
            订单号：{qrcodeTradeNo}
          </div>
          <div className="text-gray-400 text-xs mt-1">
            支付完成后页面将自动跳转...
          </div>

          {/* 已支付按钮 */}
          <Button
            type="primary"
            size="large"
            className="mt-4 w-full bg-gradient-to-r from-pink-400 to-pink-500 border-0"
            onClick={async () => {
              try {
                const order = await getOrder(qrcodeTradeNo)
                if (order.status === 1) {
                  closeQrcodeModal()
                  message.success('支付成功！')
                  navigate(`/query?trade_no=${qrcodeTradeNo}`)
                } else {
                  message.info('暂未检测到支付，请稍候...')
                }
              } catch {
                message.error('查询失败')
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
