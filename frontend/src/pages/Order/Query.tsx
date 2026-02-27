import { useState, useEffect } from 'react'
import { useSearchParams, Link, useNavigate } from 'react-router-dom'
import {
  Card, Input, Button, Table, Tag, Modal, Layout,
  Typography, Space, Empty, message, Avatar, Dropdown
} from 'antd'
import {
  SearchOutlined, ShoppingCartOutlined, UserOutlined,
  LogoutOutlined, SettingOutlined
} from '@ant-design/icons'
import { queryOrders, getOrder, getOrderSecret, OrderDetail } from '../../api/order'
import { useAuthStore } from '../../store'

const { Title, Text, Paragraph } = Typography
const { Header, Content, Footer } = Layout

export default function Query() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const initialTradeNo = searchParams.get('trade_no') || ''
  const { user, token, logout } = useAuthStore()

  const [keyword, setKeyword] = useState(initialTradeNo)
  const [loading, setLoading] = useState(false)
  const [orders, setOrders] = useState<OrderDetail[]>([])
  const [selectedOrder, setSelectedOrder] = useState<OrderDetail | null>(null)
  const [secretModalVisible, setSecretModalVisible] = useState(false)
  const [password, setPassword] = useState('')

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

  const handleSearch = async (val?: string | React.MouseEvent | React.KeyboardEvent<HTMLInputElement>) => {
    const searchKeyword = typeof val === 'string' ? val : keyword
    const targetKeyword = searchKeyword.trim()
    if (!targetKeyword) {
      message.warning('请输入订单号或联系方式')
      return
    }

    setLoading(true)
    try {
      const res = await queryOrders(targetKeyword)
      setOrders(res.items)
      if (res.items.length === 0) {
        message.info('未找到相关订单')
      }
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (initialTradeNo) {
      handleSearch()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const handleViewSecret = async (order: OrderDetail) => {
    setSelectedOrder(order)

    // 如果有密码保护
    if (order.has_password) {
      setSecretModalVisible(true)
      return
    }

    // 直接获取卡密
    try {
      const fullOrder = await getOrder(order.trade_no)
      if (fullOrder.secret) {
        Modal.success({
          title: '卡密信息',
          content: (
            <div>
              <Paragraph copyable className="whitespace-pre-wrap bg-gray-50 p-4 rounded">
                {fullOrder.secret}
              </Paragraph>
            </div>
          ),
          width: 600,
        })
      }
    } catch (e) {
      console.error(e)
    }
  }

  const handleGetSecret = async () => {
    if (!selectedOrder) return

    try {
      const res = await getOrderSecret(selectedOrder.trade_no, password)
      setSecretModalVisible(false)
      setPassword('')

      Modal.success({
        title: '卡密信息',
        content: (
          <div>
            <Paragraph copyable className="whitespace-pre-wrap bg-gray-50 p-4 rounded">
              {res.secret}
            </Paragraph>
          </div>
        ),
        width: 600,
      })
    } catch (e) {
      console.error(e)
    }
  }

  const getStatusTag = (status: number, deliveryStatus: number) => {
    if (status === 0) return <Tag color="orange">待支付</Tag>
    if (status === 2) return <Tag color="default">已取消</Tag>
    if (status === 3) return <Tag color="red">已退款</Tag>
    if (deliveryStatus === 0) return <Tag color="blue">待发货</Tag>
    return <Tag color="green">已完成</Tag>
  }

  const columns = [
    {
      title: '订单号',
      dataIndex: 'trade_no',
      key: 'trade_no',
      render: (text: string) => <Text copyable={{ text }}>{text}</Text>,
    },
    {
      title: '商品',
      dataIndex: 'commodity_name',
      key: 'commodity_name',
    },
    {
      title: '金额',
      dataIndex: 'amount',
      key: 'amount',
      render: (amount: number) => <Text className="text-red-500">¥{amount}</Text>,
    },
    {
      title: '数量',
      dataIndex: 'quantity',
      key: 'quantity',
    },
    {
      title: '状态',
      key: 'status',
      render: (_: any, record: OrderDetail) => getStatusTag(record.status, record.delivery_status),
    },
    {
      title: '下单时间',
      dataIndex: 'created_at',
      key: 'created_at',
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: OrderDetail) => (
        <Space>
          {record.status === 1 && record.delivery_status === 1 && (
            <Button type="link" onClick={() => handleViewSecret(record)}>
              查看卡密
            </Button>
          )}
          {record.status === 0 && (
            <Button type="link" className="text-orange-500">
              去支付
            </Button>
          )}
        </Space>
      ),
    },
  ]

  return (
    <Layout className="min-h-screen bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50">
      {/* 顶部导航栏 */}
      <Header className="bg-white/80 backdrop-blur-md shadow-sm sticky top-0 z-50 px-4 md:px-8 flex items-center justify-between h-16">
        <div className="flex items-center gap-3 cursor-pointer" onClick={() => navigate('/')}>
          <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center flex-shrink-0">
            <ShoppingCartOutlined className="text-white text-xl" />
          </div>
          <span className="text-lg font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-purple-600 hidden sm:block">
            LecFaka
          </span>
        </div>

        <div className="flex items-center gap-2 md:gap-4">
          <Link to="/" className="hidden sm:flex items-center gap-1 text-gray-600 hover:text-blue-500 transition-colors">
            <ShoppingCartOutlined />
            <span>购物</span>
          </Link>

          <Link to="/query" className="flex items-center gap-1 text-blue-500 font-medium">
            <SearchOutlined />
            <span>订单查询</span>
          </Link>

          {token && user ? (
            <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
              <div className="flex items-center gap-2 cursor-pointer hover:bg-gray-100 rounded-lg px-3 py-1.5 transition-colors">
                <Avatar
                  src={user.avatar}
                  icon={<UserOutlined />}
                  className="bg-gradient-to-br from-blue-500 to-purple-600"
                />
                <div className="hidden md:block">
                  <div className="text-sm font-medium text-gray-700">{user.username}</div>
                  <div className="text-xs text-orange-500">余额: ¥{user.balance.toFixed(2)}</div>
                </div>
              </div>
            </Dropdown>
          ) : (
            <div className="flex gap-2">
              <Link
                to="/login"
                className="px-4 py-1.5 text-blue-600 hover:text-blue-700 font-medium transition-colors"
              >
                登录
              </Link>
              <Link
                to="/register"
                className="px-4 py-1.5 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-lg hover:shadow-lg transition-all"
              >
                注册
              </Link>
            </div>
          )}
        </div>
      </Header>

      <Content className="px-4 md:px-8 py-6 max-w-4xl mx-auto w-full">
        <Card className="border-0 shadow-sm rounded-xl">
          <div className="flex items-center gap-2 mb-4">
            <SearchOutlined className="text-blue-500" />
            <Title level={4} className="!mb-0">订单查询</Title>
          </div>

          <div className="flex gap-4 mb-6">
            <Input
              placeholder="订单号/联系方式"
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
              onPressEnter={handleSearch}
              className="flex-1 rounded-lg"
              size="large"
            />
            <Button
              type="primary"
              size="large"
              icon={<SearchOutlined />}
              onClick={handleSearch}
              loading={loading}
              className="rounded-lg bg-gradient-to-r from-blue-500 to-purple-600 border-0"
            >
              查询订单
            </Button>
          </div>

          {orders.length > 0 ? (
            <Table
              columns={columns}
              dataSource={orders}
              rowKey="trade_no"
              pagination={false}
              className="rounded-lg"
            />
          ) : (
            <Empty description="请输入订单号或联系方式查询订单" className="py-12" />
          )}
        </Card>
      </Content>

      {/* 页脚 */}
      <Footer className="text-center bg-transparent py-6">
        <Text type="secondary" className="text-sm">
          © 2024 LecFaka - 基于 FastAPI + React 构建的现代化发卡系统
        </Text>
      </Footer>

      {/* 密码验证弹窗 */}
      <Modal
        title="请输入查单密码"
        open={secretModalVisible}
        onOk={handleGetSecret}
        onCancel={() => {
          setSecretModalVisible(false)
          setPassword('')
        }}
      >
        <Input.Password
          placeholder="请输入您设置的查单密码"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          onPressEnter={handleGetSecret}
        />
      </Modal>
    </Layout>
  )
}
