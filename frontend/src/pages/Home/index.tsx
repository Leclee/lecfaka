import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import {
  Card, Row, Col, Spin, Empty, Input, Tag, Layout, Typography,
  Avatar, Dropdown, Tabs
} from 'antd'
import {
  ShoppingCartOutlined, SearchOutlined, UserOutlined,
  BellOutlined, LogoutOutlined, SettingOutlined,
  FireOutlined, ThunderboltOutlined
} from '@ant-design/icons'
import { getCategories, getCommodities, Category, Commodity } from '../../api/shop'
import { useAuthStore, useThemeStore } from '../../store'
import DarkModeToggle from '../../components/DarkModeToggle'

const { Header, Content, Footer } = Layout
const { Text, Paragraph } = Typography
const { Search } = Input

export default function Home() {
  const navigate = useNavigate()
  const [categories, setCategories] = useState<Category[]>([])
  const [commodities, setCommodities] = useState<Commodity[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedCategory, setSelectedCategory] = useState<string>('all')
  const [keywords, setKeywords] = useState('')
  const { user, token, logout } = useAuthStore()
  useThemeStore()  // 确保主题已加载

  useEffect(() => {
    loadData()
  }, [])

  useEffect(() => {
    loadCommodities()
  }, [selectedCategory, keywords])

  const loadData = async () => {
    try {
      const cats = await getCategories()
      setCategories(cats)
    } catch (e) {
      console.error(e)
    }
    await loadCommodities()
  }

  const loadCommodities = async () => {
    setLoading(true)
    try {
      const res = await getCommodities({
        category_id: selectedCategory !== 'all' ? Number(selectedCategory) : undefined,
        keywords: keywords || undefined,
        limit: 100,
      })
      setCommodities(res.items)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

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

  // 分类标签数据
  const categoryTabs = [
    { key: 'all', label: '全部商品' },
    ...categories.map(cat => ({
      key: String(cat.id),
      label: (
        <span className="flex items-center gap-1">
          {cat.icon && <img src={cat.icon} alt="" className="w-4 h-4" />}
          {cat.name}
        </span>
      )
    }))
  ]


  return (
    <Layout className="min-h-screen" style={{ background: 'var(--theme-bg)' }}>
      {/* 顶部导航栏 */}
      <Header
        className="theme-glass sticky top-0 z-50 px-4 md:px-8 flex items-center justify-between"
        style={{
          height: 'var(--theme-header-height)',
          lineHeight: 'var(--theme-header-height)',
          boxShadow: 'var(--theme-shadow-sm)',
        }}
      >
        <div className="flex items-center gap-3 cursor-pointer" onClick={() => navigate('/')}>
          <div
            className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0"
            style={{ background: `linear-gradient(135deg, var(--theme-gradient-start), var(--theme-gradient-end))` }}
          >
            <ShoppingCartOutlined className="text-white text-xl" />
          </div>
          <span className="text-lg font-bold theme-gradient-text hidden sm:block">
            LecFaka
          </span>
        </div>

        <div className="flex items-center gap-2 md:gap-4">
          <Link
            to="/query"
            className="hidden sm:flex items-center gap-1 transition-colors"
            style={{ color: 'var(--theme-text-secondary)' }}
          >
            <SearchOutlined />
            <span>订单查询</span>
          </Link>

          <Search
            placeholder="搜索商品..."
            allowClear
            className="w-32 sm:w-48 md:w-64"
            onSearch={(value) => setKeywords(value)}
          />

          {/* 暗色模式切换 */}
          <DarkModeToggle />

          {token && user ? (
            <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
              <div
                className="flex items-center gap-2 cursor-pointer rounded-lg px-3 py-1.5 transition-colors"
                style={{ ':hover': { background: 'var(--theme-surface-hover)' } } as any}
              >
                <Avatar
                  src={user.avatar}
                  icon={<UserOutlined />}
                  style={{ background: `linear-gradient(135deg, var(--theme-gradient-start), var(--theme-gradient-end))` }}
                />
                <div className="hidden md:block">
                  <div className="text-sm font-medium" style={{ color: 'var(--theme-text)' }}>{user.username}</div>
                  <div className="text-xs" style={{ color: 'var(--theme-accent)' }}>余额: ¥{user.balance.toFixed(2)}</div>
                </div>
              </div>
            </Dropdown>
          ) : (
            <div className="flex gap-2">
              <Link
                to="/login"
                className="px-4 py-1.5 font-medium transition-colors"
                style={{ color: 'var(--theme-primary)' }}
              >
                登录
              </Link>
              <Link
                to="/register"
                className="px-4 py-1.5 text-white rounded-lg hover:shadow-lg transition-all theme-gradient-btn"
              >
                注册
              </Link>
            </div>
          )}
        </div>
      </Header>

      <Content className="px-4 md:px-8 py-6 mx-auto w-full" style={{ maxWidth: 'var(--theme-content-max-width)' }}>
        {/* 公告栏 */}
        <div
          className="theme-glass mb-6 p-4"
          style={{ borderRadius: 'var(--theme-radius-lg)' }}
        >
          <div className="flex items-center gap-2">
            <BellOutlined style={{ color: 'var(--theme-accent)' }} />
            <Text strong style={{ color: 'var(--theme-text)' }}>公告</Text>
          </div>
          <Paragraph className="!mb-0 mt-2" style={{ color: 'var(--theme-text-secondary)' }}>
            欢迎使用 LecFaka 自动发卡系统！如有问题请联系客服。
          </Paragraph>
        </div>

        {/* 分类标签 */}
        <div
          className="theme-glass mb-6 p-4"
          style={{ borderRadius: 'var(--theme-radius-lg)' }}
        >
          <div className="flex items-center gap-2 mb-3">
            <ShoppingCartOutlined style={{ color: 'var(--theme-accent)' }} />
            <Text strong style={{ color: 'var(--theme-text)' }}>购买</Text>
          </div>
          <Tabs
            activeKey={selectedCategory}
            onChange={setSelectedCategory}
            items={categoryTabs}
            className="category-tabs"
          />
        </div>

        {/* 商品列表 */}
        <div
          className="theme-glass p-4 md:p-6 min-h-[400px]"
          style={{ borderRadius: 'var(--theme-radius-lg)' }}
        >
          {loading ? (
            <div className="flex justify-center items-center py-20">
              <Spin size="large" />
            </div>
          ) : commodities.length === 0 ? (
            <Empty description="暂无商品" className="py-20" />
          ) : (
            <Row gutter={[16, 16]}>
              {commodities.map((item) => (
                <Col key={item.id} xs={12} sm={12} md={8} lg={6} xl={6}>
                  <Link to={`/product/${item.id}`}>
                    <Card
                      hoverable
                      className="overflow-hidden border-0 h-full theme-card"
                      style={{ borderRadius: 'var(--theme-radius-lg)' }}
                      bodyStyle={{ padding: 12 }}
                      cover={
                        <div
                          className="h-32 sm:h-40 flex items-center justify-center overflow-hidden relative"
                          style={{ background: `linear-gradient(135deg, var(--theme-surface), var(--theme-surface-hover))` }}
                        >
                          {item.cover ? (
                            <img
                              alt={item.name}
                              src={item.cover}
                              className="w-full h-full object-cover hover:scale-110 transition-transform duration-500"
                            />
                          ) : (
                            <ShoppingCartOutlined className="text-4xl" style={{ color: 'var(--theme-text-muted)' }} />
                          )}
                        </div>
                      }
                    >
                      {/* 标签 */}
                      <div className="flex flex-wrap gap-1 mb-2">
                        {item.delivery_way === 0 && (
                          <Tag color="blue" className="text-xs m-0 rounded">
                            <ThunderboltOutlined /> 自动发货
                          </Tag>
                        )}
                        {item.recommend === 1 && (
                          <Tag color="red" className="text-xs m-0 rounded">
                            <FireOutlined /> 推荐
                          </Tag>
                        )}
                      </div>

                      {/* 商品名称 */}
                      <div
                        className="font-medium truncate text-sm mb-2"
                        title={item.name}
                        style={{ color: 'var(--theme-text)' }}
                      >
                        {item.name}
                      </div>

                      {/* 价格和库存 */}
                      <div className="flex items-end justify-between">
                        <div>
                          <span className="text-lg font-bold" style={{ color: 'var(--theme-accent)' }}>
                            ¥{(user ? item.user_price : item.price).toFixed(2)}
                          </span>
                        </div>
                        <div className="text-xs" style={{ color: 'var(--theme-text-muted)' }}>
                          <span>库存: {item.stock > 100 ? '充足' : item.stock > 0 ? item.stock : '即将售罄'}</span>
                        </div>
                      </div>

                      {/* 销量 */}
                      {item.sold_count > 0 && (
                        <div className="text-xs mt-1" style={{ color: 'var(--theme-text-muted)' }}>
                          已售: {item.sold_count}
                        </div>
                      )}
                    </Card>
                  </Link>
                </Col>
              ))}
            </Row>
          )}
        </div>
      </Content>

      {/* 页脚 */}
      <Footer className="text-center py-6" style={{ background: 'transparent' }}>
        <Text style={{ color: 'var(--theme-text-muted)', fontSize: '0.875rem' }}>
          © 2024 LecFaka - 基于 FastAPI + React 构建的现代化发卡系统
        </Text>
      </Footer>
    </Layout>
  )
}
