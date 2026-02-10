import { useEffect, useState } from 'react'
import { Routes, Route, Link, useNavigate, useLocation } from 'react-router-dom'
import { 
  Layout, Menu, Card, Typography, Statistic, Row, Col, Button, 
  Table, Tag, Form, Input, message, Empty, Spin, Modal
} from 'antd'
import {
  UserOutlined, ShoppingOutlined, WalletOutlined,
  SettingOutlined, LogoutOutlined, ShareAltOutlined,
  CopyOutlined, KeyOutlined
} from '@ant-design/icons'
import { useAuthStore } from '../../store'
import * as userApi from '../../api/user'
import { getOrder } from '../../api/order'

const { Sider, Content } = Layout
const { Title, Text, Paragraph } = Typography

// 用户中心首页
function Dashboard() {
  const { user, fetchUser } = useAuthStore()
  
  useEffect(() => {
    fetchUser()
  }, [])
  
  if (!user) return <Spin />
  
  return (
    <div>
      <Title level={4}>欢迎回来，{user.username}</Title>
      
      <Row gutter={16} className="mb-6">
        <Col xs={24} sm={8}>
          <Card className="rounded-xl border-0 shadow-sm">
            <Statistic
              title="账户余额"
              value={user.balance}
              precision={2}
              prefix="¥"
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card className="rounded-xl border-0 shadow-sm">
            <Statistic
              title="积分"
              value={user.coin}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card className="rounded-xl border-0 shadow-sm">
            <Statistic
              title="累计充值"
              value={user.total_recharge || 0}
              precision={2}
              prefix="¥"
            />
          </Card>
        </Col>
      </Row>

      <Card title="快捷操作" className="rounded-xl border-0 shadow-sm">
        <div className="flex flex-wrap gap-4">
          <Link to="/user/orders">
            <Button type="primary" icon={<ShoppingOutlined />}>我的订单</Button>
          </Link>
          <Link to="/user/wallet">
            <Button icon={<WalletOutlined />}>账单记录</Button>
          </Link>
          <Link to="/user/promote">
            <Button icon={<ShareAltOutlined />}>推广中心</Button>
          </Link>
          <Link to="/user/settings">
            <Button icon={<SettingOutlined />}>账户设置</Button>
          </Link>
        </div>
      </Card>
    </div>
  )
}

// 我的订单
function Orders() {
  const [loading, setLoading] = useState(false)
  const [orders, setOrders] = useState<userApi.UserOrder[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  
  useEffect(() => {
    loadOrders()
  }, [page])
  
  const loadOrders = async () => {
    setLoading(true)
    try {
      const res = await userApi.getMyOrders({ page, limit: 10 })
      setOrders(res.items)
      setTotal(res.total)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  const handleViewSecret = async (tradeNo: string) => {
    try {
      const order = await getOrder(tradeNo)
      if (order.secret) {
        Modal.success({
          title: '卡密信息',
          content: (
            <Paragraph copyable className="whitespace-pre-wrap bg-gray-50 p-4 rounded font-mono">
              {order.secret}
            </Paragraph>
          ),
          width: 600,
        })
      } else {
        message.info('暂无卡密信息')
      }
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
    { title: '订单号', dataIndex: 'trade_no', key: 'trade_no' },
    { title: '商品', dataIndex: 'commodity_name', key: 'commodity_name' },
    { 
      title: '金额', 
      dataIndex: 'amount', 
      key: 'amount',
      render: (v: number) => <span className="text-red-500">¥{v.toFixed(2)}</span>
    },
    { title: '数量', dataIndex: 'quantity', key: 'quantity' },
    { 
      title: '状态', 
      key: 'status',
      render: (_: any, record: userApi.UserOrder) => getStatusTag(record.status, record.delivery_status)
    },
    { title: '时间', dataIndex: 'created_at', key: 'created_at' },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: userApi.UserOrder) => (
        record.status === 1 && record.delivery_status === 1 && (
          <Button type="link" onClick={() => handleViewSecret(record.trade_no)}>
            查看卡密
          </Button>
        )
      )
    }
  ]
  
  return (
    <Card title="我的订单" className="rounded-xl border-0 shadow-sm">
      <Table
        columns={columns}
        dataSource={orders}
        rowKey="trade_no"
        loading={loading}
        pagination={{
          current: page,
          total,
          pageSize: 10,
          onChange: setPage,
        }}
        locale={{ emptyText: <Empty description="暂无订单" /> }}
      />
    </Card>
  )
}

// 钱包/账单
function Wallet() {
  const [loading, setLoading] = useState(false)
  const [bills, setBills] = useState<userApi.Bill[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const { user } = useAuthStore()
  
  useEffect(() => {
    loadBills()
  }, [page])
  
  const loadBills = async () => {
    setLoading(true)
    try {
      const res = await userApi.getMyBills({ page, limit: 20 })
      setBills(res.items)
      setTotal(res.total)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }
  
  const columns = [
    { 
      title: '类型', 
      dataIndex: 'type', 
      key: 'type',
      render: (v: number) => (
        <Tag color={v === 1 ? 'green' : 'red'}>
          {v === 1 ? '收入' : '支出'}
        </Tag>
      )
    },
    { 
      title: '金额', 
      dataIndex: 'amount', 
      key: 'amount',
      render: (v: number, record: userApi.Bill) => (
        <span className={record.type === 1 ? 'text-green-500' : 'text-red-500'}>
          {record.type === 1 ? '+' : '-'}¥{v.toFixed(2)}
        </span>
      )
    },
    { 
      title: '余额', 
      dataIndex: 'balance', 
      key: 'balance',
      render: (v: number) => `¥${v.toFixed(2)}`
    },
    { title: '说明', dataIndex: 'description', key: 'description' },
    { title: '时间', dataIndex: 'created_at', key: 'created_at' },
  ]
  
  return (
    <div>
      <Card className="rounded-xl border-0 shadow-sm mb-4">
        <Row gutter={16}>
          <Col span={12}>
            <Statistic 
              title="当前余额" 
              value={user?.balance || 0} 
              precision={2}
              prefix="¥"
              valueStyle={{ color: '#1890ff', fontSize: 32 }}
            />
          </Col>
          <Col span={12} className="flex items-center">
            <Button type="primary" size="large" disabled>
              充值（功能开发中）
            </Button>
          </Col>
        </Row>
      </Card>
      
      <Card title="账单记录" className="rounded-xl border-0 shadow-sm">
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
          }}
          locale={{ emptyText: <Empty description="暂无账单记录" /> }}
        />
      </Card>
    </div>
  )
}

// 推广中心
function Promote() {
  const [inviteLink, setInviteLink] = useState('')
  const [inviteCode, setInviteCode] = useState('')
  
  useEffect(() => {
    loadInviteLink()
  }, [])
  
  const loadInviteLink = async () => {
    try {
      const res = await userApi.getInviteLink()
      setInviteLink(res.invite_link)
      setInviteCode(res.invite_code)
    } catch (e) {
      console.error(e)
    }
  }
  
  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text)
    message.success('已复制到剪贴板')
  }
  
  return (
    <Card title="推广中心" className="rounded-xl border-0 shadow-sm">
      <div className="space-y-6">
        <div>
          <Text type="secondary">您的邀请码</Text>
          <div className="flex items-center gap-2 mt-2">
            <Input value={inviteCode} readOnly className="max-w-xs" />
            <Button icon={<CopyOutlined />} onClick={() => handleCopy(inviteCode)}>
              复制
            </Button>
          </div>
        </div>
        
        <div>
          <Text type="secondary">推广链接</Text>
          <div className="flex items-center gap-2 mt-2">
            <Input value={inviteLink} readOnly className="flex-1" />
            <Button icon={<CopyOutlined />} onClick={() => handleCopy(inviteLink)}>
              复制
            </Button>
          </div>
        </div>
        
        <div className="bg-blue-50 p-4 rounded-lg">
          <Text>邀请好友注册，好友消费您将获得佣金奖励！</Text>
        </div>
      </div>
    </Card>
  )
}

// 账户设置
function Settings() {
  const { user, fetchUser } = useAuthStore()
  const [loading, setLoading] = useState(false)
  const [form] = Form.useForm()
  const [passwordForm] = Form.useForm()
  
  const handleUpdateProfile = async (values: any) => {
    setLoading(true)
    try {
      await userApi.updateProfile(values)
      message.success('保存成功')
      fetchUser()
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }
  
  const handleChangePassword = async (values: any) => {
    if (values.new_password !== values.confirm_password) {
      message.error('两次密码输入不一致')
      return
    }
    
    setLoading(true)
    try {
      await userApi.changePassword({
        old_password: values.old_password,
        new_password: values.new_password,
      })
      message.success('密码修改成功')
      passwordForm.resetFields()
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }
  
  return (
    <div className="space-y-4">
      <Card title="基本信息" className="rounded-xl border-0 shadow-sm">
        <Form
          form={form}
          layout="vertical"
          initialValues={{
            avatar: user?.avatar,
            alipay: user?.alipay,
            wechat: user?.wechat,
          }}
          onFinish={handleUpdateProfile}
          className="max-w-md"
        >
          <Form.Item name="avatar" label="头像URL">
            <Input placeholder="https://example.com/avatar.jpg" />
          </Form.Item>
          <Form.Item name="alipay" label="支付宝账号">
            <Input placeholder="用于提现" />
          </Form.Item>
          <Form.Item name="wechat" label="微信账号">
            <Input placeholder="用于提现" />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading}>
              保存修改
            </Button>
          </Form.Item>
        </Form>
      </Card>
      
      <Card title="修改密码" className="rounded-xl border-0 shadow-sm">
        <Form
          form={passwordForm}
          layout="vertical"
          onFinish={handleChangePassword}
          className="max-w-md"
        >
          <Form.Item
            name="old_password"
            label="当前密码"
            rules={[{ required: true, message: '请输入当前密码' }]}
          >
            <Input.Password />
          </Form.Item>
          <Form.Item
            name="new_password"
            label="新密码"
            rules={[
              { required: true, message: '请输入新密码' },
              { min: 6, message: '密码至少6位' }
            ]}
          >
            <Input.Password />
          </Form.Item>
          <Form.Item
            name="confirm_password"
            label="确认新密码"
            rules={[{ required: true, message: '请确认新密码' }]}
          >
            <Input.Password />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading} icon={<KeyOutlined />}>
              修改密码
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  )
}

export default function UserCenter() {
  const navigate = useNavigate()
  const location = useLocation()
  const { user, logout, fetchUser } = useAuthStore()

  useEffect(() => {
    if (!user) {
      const token = localStorage.getItem('token')
      if (token) {
        fetchUser()
      } else {
        navigate('/login')
      }
    }
  }, [])

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  if (!user) return <Spin className="flex justify-center items-center min-h-screen" />

  const menuItems = [
    { key: '/user', icon: <UserOutlined />, label: '个人中心' },
    { key: '/user/orders', icon: <ShoppingOutlined />, label: '我的订单' },
    { key: '/user/wallet', icon: <WalletOutlined />, label: '我的钱包' },
    { key: '/user/promote', icon: <ShareAltOutlined />, label: '推广中心' },
    { key: '/user/settings', icon: <SettingOutlined />, label: '账户设置' },
  ]

  return (
    <Layout className="min-h-screen">
      <Sider width={220} className="bg-white border-r border-gray-100">
        <div className="p-4 text-center border-b border-gray-100">
          <Link to="/" className="text-lg font-bold text-blue-500 no-underline hover:no-underline">LecFaka</Link>
        </div>
        <Menu
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
          className="border-r-0"
        />
        <div className="p-4 border-t border-gray-100">
          <Button
            type="text"
            danger
            icon={<LogoutOutlined />}
            onClick={handleLogout}
            className="w-full"
          >
            退出登录
          </Button>
        </div>
      </Sider>
      
      <Content className="p-6 bg-gray-50">
        <Routes>
          <Route index element={<Dashboard />} />
          <Route path="orders" element={<Orders />} />
          <Route path="wallet" element={<Wallet />} />
          <Route path="promote" element={<Promote />} />
          <Route path="settings" element={<Settings />} />
        </Routes>
      </Content>
    </Layout>
  )
}
