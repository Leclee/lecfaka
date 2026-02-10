import { useState, useEffect } from 'react'
import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import { Layout, Menu, Avatar, Dropdown, Button, Drawer } from 'antd'
import {
  HomeOutlined, ShopOutlined, WalletOutlined, ShoppingCartOutlined,
  GiftOutlined, TeamOutlined, FileTextOutlined, SafetyOutlined,
  UserOutlined, LogoutOutlined, OrderedListOutlined, MenuOutlined,
  SettingOutlined,
  CloseOutlined
} from '@ant-design/icons'
import { useAuthStore } from '../../store/auth'

const { Header, Sider, Content } = Layout

export default function UserLayout() {
  const navigate = useNavigate()
  const location = useLocation()
  const { user, logout } = useAuthStore()
  const [isMobile, setIsMobile] = useState(false)
  const [drawerVisible, setDrawerVisible] = useState(false)

  // 检测屏幕尺寸
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768)
      if (window.innerWidth >= 768) {
        setDrawerVisible(false)
      }
    }
    checkMobile()
    window.addEventListener('resize', checkMobile)
    return () => window.removeEventListener('resize', checkMobile)
  }, [])

  const menuItems = [
    { key: '/user', icon: <HomeOutlined />, label: '我的主页' },
    { key: '/user/shop', icon: <ShopOutlined />, label: '我的店铺' },
    { key: '/user/recharge', icon: <WalletOutlined />, label: '充值中心' },
    { key: '/user/orders', icon: <ShoppingCartOutlined />, label: '购买记录' },
    { key: '/user/coins', icon: <GiftOutlined />, label: '硬币兑现' },
    { key: '/user/referrals', icon: <TeamOutlined />, label: '我的下级' },
    { key: '/user/bills', icon: <FileTextOutlined />, label: '我的账单' },
    { key: '/user/security', icon: <SafetyOutlined />, label: '安全中心' },
  ]

  const handleMenuClick = (key: string) => {
    navigate(key)
  }

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const userMenuItems: any[] = [
    { key: 'center', label: '个人中心', icon: <UserOutlined />, onClick: () => navigate('/user') },
    { key: 'orders', label: '我的订单', icon: <ShoppingCartOutlined />, onClick: () => navigate('/user/orders') },
    user?.is_admin ? { key: 'admin', label: '管理后台', icon: <SettingOutlined />, onClick: () => navigate('/admin') } : null,
    { type: 'divider' as const },
    { key: 'logout', label: '退出登录', icon: <LogoutOutlined />, onClick: handleLogout, danger: true },
  ].filter(Boolean)

  // 侧边菜单组件
  const SideMenu = () => (
    <Menu
      mode="inline"
      selectedKeys={[location.pathname]}
      items={menuItems}
      onClick={({ key }) => {
        handleMenuClick(key)
        if (isMobile) setDrawerVisible(false)
      }}
      className="border-r-0 py-4"
      style={{ 
        background: 'linear-gradient(180deg, #fff5f5 0%, #fff 100%)',
      }}
    />
  )

  return (
    <Layout className="min-h-screen">
      {/* 顶部导航 */}
      <Header className="bg-white shadow-sm px-4 md:px-6 flex items-center justify-between h-16">
        <div className="flex items-center gap-4 md:gap-8">
          {/* 移动端菜单按钮 */}
          {isMobile && (
            <Button
              type="text"
              icon={<MenuOutlined />}
              onClick={() => setDrawerVisible(true)}
              className="text-gray-600"
            />
          )}
          
          <div 
            className="flex items-center gap-3 cursor-pointer"
            onClick={() => navigate('/')}
          >
            <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center flex-shrink-0">
              <ShoppingCartOutlined className="text-white text-xl" />
            </div>
            <span className="hidden sm:inline text-lg font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-purple-600">LecFaka</span>
          </div>
          
          <nav className="hidden md:flex items-center gap-4">
            <Button 
              type="link" 
              onClick={() => navigate('/user/orders')}
              className="text-gray-600 hover:text-blue-500"
              icon={<OrderedListOutlined />}
            >
              我的订单
            </Button>
            <Button 
              type="link" 
              onClick={() => navigate('/')}
              className="text-gray-600 hover:text-blue-500"
              icon={<ShoppingCartOutlined />}
            >
              购买商品
            </Button>
          </nav>
        </div>

        <div className="flex items-center gap-4">
          <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
            <div className="flex items-center gap-2 cursor-pointer hover:bg-gray-50 rounded-lg px-3 py-1.5 transition-colors">
              <Avatar 
                src={user?.avatar} 
                icon={<UserOutlined />}
                className="bg-gradient-to-br from-blue-500 to-purple-600"
              />
              <div className="hidden md:block">
                <div className="text-sm font-medium text-gray-700">{user?.username}</div>
                <div className="text-xs text-orange-500">余额: ¥{user?.balance?.toFixed(2) || '0.00'}</div>
              </div>
            </div>
          </Dropdown>
        </div>
      </Header>

      <Layout>
        {/* 移动端抽屉菜单 */}
        <Drawer
          title={
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                <ShoppingCartOutlined className="text-white" />
              </div>
              <span className="font-bold text-gray-800">菜单</span>
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
          {/* 移动端底部操作 */}
          <div className="p-4 border-t">
            <Button 
              block 
              icon={<ShoppingCartOutlined />}
              onClick={() => { navigate('/'); setDrawerVisible(false) }}
              className="mb-2"
            >
              购买商品
            </Button>
            <Button 
              block 
              type="primary"
              danger
              icon={<LogoutOutlined />}
              onClick={() => { handleLogout(); setDrawerVisible(false) }}
            >
              退出登录
            </Button>
          </div>
        </Drawer>

        {/* 桌面端侧边菜单 */}
        {!isMobile && (
          <Sider 
            width={200} 
            className="bg-white hidden md:block"
            style={{ 
              overflow: 'auto',
              height: 'calc(100vh - 64px)',
              position: 'sticky',
              top: 64,
              left: 0,
            }}
          >
            <SideMenu />
          </Sider>
        )}

        {/* 主内容区 */}
        <Content 
          className="p-4 md:p-6 bg-gray-50"
          style={{ 
            minHeight: 'calc(100vh - 64px)',
            overflow: 'auto',
          }}
        >
          <div 
            className="bg-cover bg-center rounded-xl p-4 md:p-6"
            style={{
              backgroundImage: 'url(/bg-pattern.png)',
              backgroundSize: 'cover',
            }}
          >
            <Outlet />
          </div>
        </Content>
      </Layout>
    </Layout>
  )
}
