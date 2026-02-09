import { useEffect, useState } from 'react'
import { Card, Row, Col, Statistic, Typography, Tag, Spin, Alert } from 'antd'
import { 
  ShoppingCartOutlined, UserOutlined, 
  CreditCardOutlined, ClockCircleOutlined,
  BankOutlined
} from '@ant-design/icons'
import * as adminApi from '../../api/admin'

const { Title, Text } = Typography

export default function Dashboard() {
  const [loading, setLoading] = useState(true)
  const [data, setData] = useState<adminApi.DashboardData | null>(null)
  const [announcements, setAnnouncements] = useState<adminApi.Announcement[]>([])

  useEffect(() => {
    loadData()
    loadAnnouncements()
  }, [])

  const loadData = async () => {
    try {
      const res = await adminApi.getDashboard()
      setData(res)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  const loadAnnouncements = async () => {
    try {
      const res = await adminApi.getDashboardAnnouncements()
      setAnnouncements(res.items || [])
    } catch (e) {
      console.error(e)
    }
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <Spin size="large" />
      </div>
    )
  }

  return (
    <div>
      <Title level={4} className="mb-6">控制台</Title>

      {/* 公告区域 */}
      {announcements.length > 0 && (
        <Card className="rounded-xl border-0 shadow-sm mb-6" title="官方公告">
          <div className="space-y-3 max-h-64 overflow-y-auto">
            {announcements.map(item => (
              <Alert
                key={item.id}
                message={
                  <div className="flex justify-between items-center">
                    <span className={item.type === 2 ? 'text-red-500' : item.type === 1 ? 'text-orange-500' : ''}>
                      {item.title}
                    </span>
                    <Text type="secondary" className="text-xs">
                      {item.created_at?.split('T')[0]}
                    </Text>
                  </div>
                }
                type={item.type === 2 ? 'error' : item.type === 1 ? 'warning' : 'info'}
                showIcon
              />
            ))}
          </div>
        </Card>
      )}

      {/* 今日数据 */}
      <Card className="rounded-xl border-0 shadow-sm mb-6" title="今日数据">
        <Row gutter={[16, 16]}>
          <Col xs={12} sm={8} md={4}>
            <Statistic
              title="交易金额"
              value={data?.sales?.today || 0}
              prefix="¥"
              valueStyle={{ color: '#1890ff' }}
            />
          </Col>
          <Col xs={12} sm={8} md={4}>
            <Statistic
              title="订单"
              value={data?.orders?.today || 0}
              valueStyle={{ color: '#52c41a' }}
            />
          </Col>
          <Col xs={12} sm={8} md={4}>
            <Statistic
              title="注册用户"
              value={data?.users?.today || 0}
              valueStyle={{ color: '#722ed1' }}
            />
          </Col>
          <Col xs={12} sm={8} md={4}>
            <Statistic
              title="充值金额"
              value={data?.recharge?.today || 0}
              prefix="¥"
              valueStyle={{ color: '#fa8c16' }}
            />
          </Col>
          <Col xs={12} sm={8} md={4}>
            <Statistic
              title="待处理提现"
              value={data?.withdrawals?.pending || 0}
              valueStyle={{ color: data?.withdrawals?.pending ? '#ff4d4f' : '#52c41a' }}
            />
          </Col>
          <Col xs={12} sm={8} md={4}>
            <Statistic
              title="商家"
              value={data?.users?.merchants || 0}
              valueStyle={{ color: '#13c2c2' }}
            />
          </Col>
        </Row>
      </Card>

      {/* 统计卡片 */}
      <Row gutter={[16, 16]} className="mb-6">
        <Col xs={12} sm={8} md={4}>
          <Card className="rounded-xl border-0 shadow-sm text-center">
            <Statistic title="总用户" value={data?.users?.total || 0} prefix={<UserOutlined />} />
          </Card>
        </Col>
        <Col xs={12} sm={8} md={4}>
          <Card className="rounded-xl border-0 shadow-sm text-center">
            <Statistic 
              title="用户总余额" 
              value={data?.users?.total_balance || 0} 
              prefix="¥"
              precision={2}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={8} md={4}>
          <Card className="rounded-xl border-0 shadow-sm text-center">
            <Statistic 
              title="总充值" 
              value={data?.users?.total_recharge || 0} 
              prefix="¥"
              precision={2}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={8} md={4}>
          <Card className="rounded-xl border-0 shadow-sm text-center">
            <Statistic title="总商品" value={data?.commodities?.total || 0} />
          </Card>
        </Col>
        <Col xs={12} sm={8} md={4}>
          <Card className="rounded-xl border-0 shadow-sm text-center">
            <Statistic 
              title="已上架" 
              value={data?.commodities?.online || 0}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={8} md={4}>
          <Card className="rounded-xl border-0 shadow-sm text-center">
            <Statistic 
              title="卡密库存" 
              value={data?.cards?.stock || 0}
              valueStyle={{ color: data?.cards?.stock && data.cards.stock < 100 ? '#ff4d4f' : undefined }}
            />
          </Card>
        </Col>
      </Row>

      {/* 销售统计 */}
      <Row gutter={[16, 16]} className="mb-6">
        <Col xs={24} md={16}>
          <Card title="销售概览" className="rounded-xl border-0 shadow-sm h-full">
            <Row gutter={[24, 24]}>
              <Col xs={12} sm={6}>
                <Statistic
                  title="今日销售"
                  value={data?.sales?.today || 0}
                  prefix="¥"
                  valueStyle={{ color: '#1890ff', fontWeight: 'bold' }}
                />
              </Col>
              <Col xs={12} sm={6}>
                <Statistic
                  title="昨日销售"
                  value={data?.sales?.yesterday || 0}
                  prefix="¥"
                  valueStyle={{ color: '#52c41a' }}
                />
              </Col>
              <Col xs={12} sm={6}>
                <Statistic
                  title="本周销售"
                  value={data?.sales?.week || 0}
                  prefix="¥"
                  valueStyle={{ color: '#722ed1' }}
                />
              </Col>
              <Col xs={12} sm={6}>
                <Statistic
                  title="本月销售"
                  value={data?.sales?.month || 0}
                  prefix="¥"
                  valueStyle={{ color: '#fa8c16' }}
                />
              </Col>
            </Row>
            <div className="mt-6 pt-4 border-t border-gray-100">
              <Row gutter={16}>
                <Col span={12}>
                  <Text type="secondary">总销售额：</Text>
                  <Text strong className="text-red-500">¥{(data?.sales?.total || 0).toLocaleString()}</Text>
                </Col>
                <Col span={12}>
                  <Text type="secondary">已售卡密：</Text>
                  <Text strong>{data?.cards?.sold || 0} 张</Text>
                </Col>
              </Row>
            </div>
          </Card>
        </Col>
        
        <Col xs={24} md={8}>
          <Card title="订单状态" className="rounded-xl border-0 shadow-sm h-full">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <Text>待支付</Text>
                <Tag color="orange">{data?.orders?.pending || 0}</Tag>
              </div>
              <div className="flex items-center justify-between">
                <Text>已支付</Text>
                <Tag color="green">{data?.orders?.paid || 0}</Tag>
              </div>
              <div className="flex items-center justify-between">
                <Text>总订单</Text>
                <Tag color="blue">{data?.orders?.total || 0}</Tag>
              </div>
              <div className="border-t pt-4 mt-4">
                <div className="flex items-center justify-between">
                  <Text type="secondary">待处理提现金额</Text>
                  <Text className="text-orange-500">¥{data?.withdrawals?.pending_amount || 0}</Text>
                </div>
              </div>
            </div>
          </Card>
        </Col>
      </Row>

      {/* 快捷操作 */}
      <Row gutter={[16, 16]}>
        <Col xs={24} md={12}>
          <Card title="快捷操作" className="rounded-xl border-0 shadow-sm">
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <a href="/admin/commodities" className="p-4 bg-blue-50 rounded-xl hover:bg-blue-100 transition-colors text-center">
                <ShoppingCartOutlined className="text-2xl text-blue-500 mb-2" />
                <div className="text-xs text-gray-600">添加商品</div>
              </a>
              <a href="/admin/cards" className="p-4 bg-green-50 rounded-xl hover:bg-green-100 transition-colors text-center">
                <CreditCardOutlined className="text-2xl text-green-500 mb-2" />
                <div className="text-xs text-gray-600">导入卡密</div>
              </a>
              <a href="/admin/orders" className="p-4 bg-orange-50 rounded-xl hover:bg-orange-100 transition-colors text-center">
                <ClockCircleOutlined className="text-2xl text-orange-500 mb-2" />
                <div className="text-xs text-gray-600">处理订单</div>
              </a>
              <a href="/admin/withdrawals" className="p-4 bg-red-50 rounded-xl hover:bg-red-100 transition-colors text-center">
                <BankOutlined className="text-2xl text-red-500 mb-2" />
                <div className="text-xs text-gray-600">提现审核</div>
              </a>
            </div>
          </Card>
        </Col>
        
        <Col xs={24} md={12}>
          <Card title="系统信息" className="rounded-xl border-0 shadow-sm">
            <div className="space-y-3">
              <div className="flex justify-between">
                <Text type="secondary">系统版本</Text>
                <Text>v1.0.0</Text>
              </div>
              <div className="flex justify-between">
                <Text type="secondary">后端框架</Text>
                <Text>FastAPI</Text>
              </div>
              <div className="flex justify-between">
                <Text type="secondary">前端框架</Text>
                <Text>React + Ant Design</Text>
              </div>
              <div className="flex justify-between">
                <Text type="secondary">数据库</Text>
                <Text>PostgreSQL</Text>
              </div>
            </div>
          </Card>
        </Col>
      </Row>
    </div>
  )
}
