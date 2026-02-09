import { useEffect, useState } from 'react'
import { Outlet, useNavigate, useLocation, Link } from 'react-router-dom'
import { 
  Layout, Menu, Avatar, Dropdown, Typography, Badge,
  Breadcrumb, Drawer
} from 'antd'
import {
  DashboardOutlined, ShoppingOutlined, CreditCardOutlined,
  OrderedListOutlined, UserOutlined, SettingOutlined,
  LogoutOutlined, MenuFoldOutlined, MenuUnfoldOutlined,
  TagOutlined, GiftOutlined, BellOutlined, WalletOutlined,
  BankOutlined, CrownOutlined, DollarOutlined, FileTextOutlined,
  HistoryOutlined, MenuOutlined, CloseOutlined,
  ApiOutlined, ToolOutlined
} from '@ant-design/icons'
import { useAuthStore } from '../../store'

const { Header, Sider, Content } = Layout
const { Text } = Typography

export default function AdminLayout() {
  const navigate = useNavigate()
  const location = useLocation()
  const { user, logout } = useAuthStore()
  const [collapsed, setCollapsed] = useState(false)
  const [isMobile, setIsMobile] = useState(false)
  const [drawerVisible, setDrawerVisible] = useState(false)
  // theme available if needed

  // 检测屏幕尺寸
  useEffect(() => {
    const checkMobile = () => {
      const mobile = window.innerWidth < 768
      setIsMobile(mobile)
      if (!mobile) setDrawerVisible(false)
      if (mobile) setCollapsed(true)
    }
    checkMobile()
    window.addEventListener('resize', checkMobile)
    return () => window.removeEventListener('resize', checkMobile)
  }, [])

  useEffect(() => {
    // 检查是否是管理员
    if (!user?.is_admin) {
      navigate('/login')
    }
  }, [user])

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const menuItems: any[] = [
    {
      key: '/admin',
      icon: <DashboardOutlined />,
      label: '控制台',
    },
    {
      key: 'user',
      icon: <UserOutlined />,
      label: 'USER',
      type: 'group' as const,
      children: [
        { key: '/admin/users', icon: <UserOutlined />, label: '会员管理' },
        { key: '/admin/recharge', icon: <WalletOutlined />, label: '充值订单' },
        { key: '/admin/bills', icon: <FileTextOutlined />, label: '账单管理' },
        { key: '/admin/user-groups', icon: <CrownOutlined />, label: '会员等级' },
        { key: '/admin/business-levels', icon: <DollarOutlined />, label: '商户等级' },
        { key: '/admin/withdrawals', icon: <BankOutlined />, label: '提现管理' },
      ],
    },
    {
      key: 'trade',
      icon: <ShoppingOutlined />,
      label: 'TRADE',
      type: 'group',
      children: [
        { key: '/admin/categories', icon: <TagOutlined />, label: '分类管理' },
        { key: '/admin/commodities', icon: <ShoppingOutlined />, label: '商品管理' },
        { key: '/admin/cards', icon: <CreditCardOutlined />, label: '卡密管理' },
        { key: '/admin/orders', icon: <OrderedListOutlined />, label: '商品订单' },
        { key: '/admin/coupons', icon: <GiftOutlined />, label: '优惠券' },
      ],
    },
    {
      key: 'config',
      icon: <SettingOutlined />,
      label: 'CONFIG',
      type: 'group',
      children: [
        { key: '/admin/settings', icon: <SettingOutlined />, label: '网站设置' },
        { key: '/admin/general-plugins', icon: <ToolOutlined />, label: '通用插件' },
        {
          key: 'payment-group',
          icon: <DollarOutlined />,
          label: '支付管理',
          children: [
            { key: '/admin/payment-plugins', icon: <ApiOutlined />, label: '支付插件' },
            { key: '/admin/payment-settings', icon: <CreditCardOutlined />, label: '支付接口' },
          ],
        },
        { key: '/admin/logs', icon: <HistoryOutlined />, label: '操作日志' },
      ],
    },
  ]

  const userMenuItems = [
    { key: 'profile', label: '个人资料', icon: <UserOutlined /> },
    { key: 'home', label: '返回前台', icon: <ShoppingOutlined />, onClick: () => navigate('/') },
    { type: 'divider' as const },
    { key: 'logout', label: '退出登录', icon: <LogoutOutlined />, onClick: handleLogout, danger: true },
  ]

  // 面包屑映射
  const breadcrumbMap: Record<string, string> = {
    '/admin': '控制台',
    '/admin/users': '会员管理',
    '/admin/recharge': '充值订单',
    '/admin/bills': '账单管理',
    '/admin/withdrawals': '提现管理',
    '/admin/user-groups': '会员等级',
    '/admin/business-levels': '商户等级',
    '/admin/categories': '分类管理',
    '/admin/commodities': '商品管理',
    '/admin/cards': '卡密管理',
    '/admin/orders': '商品订单',
    '/admin/coupons': '优惠券',
    '/admin/plugins': '插件管理',
    '/admin/general-plugins': '通用插件',
    '/admin/payment-plugins': '支付插件',
    '/admin/payment-settings': '支付接口',
    '/admin/store': '应用商店',
    '/admin/settings': '网站设置',
    '/admin/logs': '操作日志',
  }

  const currentPath = location.pathname
  const breadcrumbItems: any[] = [
    { title: <Link to="/admin">首页</Link> },
    currentPath !== '/admin' ? { title: breadcrumbMap[currentPath] || '' } : null,
  ].filter(Boolean)

  // 侧边菜单组件
  const SideMenu = () => (
    <Menu
      mode="inline"
      selectedKeys={[currentPath]}
      items={menuItems}
      onClick={({ key }) => {
        navigate(key)
        if (isMobile) setDrawerVisible(false)
      }}
      className="border-r-0 mt-2"
      style={{ borderRight: 0 }}
    />
  )

  // Logo 组件
  const Logo = ({ showText = true }: { showText?: boolean }) => (
    <div className="h-16 flex items-center border-b border-gray-100 px-4">
      <div className={`flex items-center gap-3 ${!showText ? 'justify-center w-full' : ''}`}>
        <div className="w-9 h-9 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center flex-shrink-0">
          <ShoppingOutlined className="text-white text-lg" />
        </div>
        {showText && (
          <span className="text-lg font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-purple-600 whitespace-nowrap">LecFaka</span>
        )}
      </div>
    </div>
  )

  return (
    <Layout className="min-h-screen">
      {/* 移动端抽屉菜单 */}
      <Drawer
        title={
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
              <ShoppingOutlined className="text-white" />
            </div>
            <span className="font-bold text-gray-800">管理后台</span>
          </div>
        }
        placement="left"
        onClose={() => setDrawerVisible(false)}
        open={drawerVisible}
        width={260}
        closeIcon={<CloseOutlined />}
        styles={{ body: { padding: 0 } }}
      >
        <SideMenu />
      </Drawer>

      {/* 桌面端侧边栏 */}
      {!isMobile && (
        <Sider 
          trigger={null} 
          collapsible 
          collapsed={collapsed}
          width={220}
          className="!bg-white border-r border-gray-100 shadow-sm hidden md:block"
          style={{ overflow: 'auto', height: '100vh', position: 'fixed', left: 0, top: 0, bottom: 0 }}
        >
          <Logo showText={!collapsed} />
          <SideMenu />
        </Sider>
      )}

      {/* 主内容区 */}
      <Layout style={{ marginLeft: isMobile ? 0 : (collapsed ? 80 : 220), transition: 'margin-left 0.2s' }}>
        {/* 顶部栏 */}
        <Header className="bg-white px-4 flex items-center justify-between h-16 shadow-sm sticky top-0 z-10">
          <div className="flex items-center gap-4">
            <div
              className="cursor-pointer hover:bg-gray-100 p-2 rounded-lg transition-colors"
              onClick={() => isMobile ? setDrawerVisible(true) : setCollapsed(!collapsed)}
            >
              {isMobile ? <MenuOutlined /> : (collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />)}
            </div>
            <Breadcrumb items={breadcrumbItems} className="hidden sm:flex" />
          </div>

          <div className="flex items-center gap-4">
            <Badge count={0} size="small">
              <BellOutlined className="text-lg text-gray-500 cursor-pointer hover:text-blue-500 transition-colors" />
            </Badge>

            <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
              <div className="flex items-center gap-2 cursor-pointer hover:bg-gray-100 rounded-lg px-3 py-1.5 transition-colors">
                <Avatar 
                  src={user?.avatar}
                  icon={<UserOutlined />}
                  className="bg-gradient-to-br from-blue-500 to-purple-600"
                />
                <Text className="hidden md:inline">{user?.username}</Text>
              </div>
            </Dropdown>
          </div>
        </Header>

        {/* 内容区 */}
        <Content className="m-2 md:m-4 p-3 md:p-6 bg-gray-50 min-h-[calc(100vh-88px)]">
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  )
}
