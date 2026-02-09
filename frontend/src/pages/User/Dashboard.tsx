import { useEffect, useState } from 'react'
import { Card, Row, Col, Typography, Button, Statistic, message, Input, Tag } from 'antd'
import { 
  WalletOutlined, GiftOutlined, DollarOutlined, 
  TeamOutlined, CopyOutlined, ReloadOutlined,
  GlobalOutlined, ClockCircleOutlined, SafetyOutlined
} from '@ant-design/icons'
import { useAuthStore } from '../../store/auth'
import api from '../../api'

const { Title, Text } = Typography

interface UserProfile {
  id: number
  username: string
  email?: string
  avatar?: string
  balance: number
  coin: number
  total_recharge: number
  total_income: number
  merchant_id: number
  merchant_key: string
  referral_count: number
  last_login_at?: string
  last_login_ip?: string
  created_at?: string
}

interface InviteInfo {
  invite_code: string
  invite_link: string
}

export default function UserDashboard() {
  const [profile, setProfile] = useState<UserProfile | null>(null)
  const [inviteInfo, setInviteInfo] = useState<InviteInfo | null>(null)
  const [_loading, setLoading] = useState(true)
  useAuthStore()

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    setLoading(true)
    try {
      const [profileRes, inviteRes] = await Promise.all([
        api.get('/users/me'),
        api.get('/users/me/invite-link'),
      ])
      setProfile(profileRes)
      setInviteInfo(inviteRes)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  const copyToClipboard = (text: string, label: string) => {
    navigator.clipboard.writeText(text)
    message.success(`${label}已复制`)
  }

  const handleResetKey = async () => {
    try {
      const res = await api.post('/users/me/reset-merchant-key')
      message.success(res.message)
      loadData()
    } catch (e: any) {
      message.error(e.message || '重置失败')
    }
  }

  const formatDate = (dateStr?: string) => {
    if (!dateStr) return '-'
    return new Date(dateStr).toLocaleString('zh-CN')
  }

  if (!profile) {
    return <div className="flex justify-center items-center h-64">加载中...</div>
  }

  return (
    <div>
      <Title level={4} className="flex items-center gap-2">
        <SafetyOutlined /> 我的主页
      </Title>

      {/* 欢迎信息 */}
      <Card className="mb-6 border-0 shadow-sm rounded-xl bg-gradient-to-r from-pink-50 to-purple-50">
        <Text className="text-pink-500">欢迎回来，{profile.username}</Text>
      </Card>

      {/* 登录信息 */}
      <Card className="mb-6 border-0 shadow-sm rounded-xl">
        <Row gutter={[24, 16]}>
          <Col span={12}>
            <div className="flex items-center gap-2 text-gray-600">
              <GlobalOutlined />
              <Text type="secondary">登录IP地址：</Text>
              <Text className="text-blue-500">{profile.last_login_ip || '-'}</Text>
            </div>
          </Col>
          <Col span={12}>
            <div className="flex items-center gap-2 text-gray-600">
              <ClockCircleOutlined />
              <Text type="secondary">登录时间：</Text>
              <Text>{formatDate(profile.last_login_at)}</Text>
            </div>
          </Col>
          <Col span={12}>
            <div className="flex items-center gap-2 text-gray-600">
              <GlobalOutlined />
              <Text type="secondary">上次登录IP：</Text>
              <Text className="text-blue-500">{profile.last_login_ip || '-'}</Text>
              {profile.last_login_ip && (
                <Tag color="red">异地登录</Tag>
              )}
            </div>
          </Col>
          <Col span={12}>
            <div className="flex items-center gap-2 text-gray-600">
              <ClockCircleOutlined />
              <Text type="secondary">上次登录时间：</Text>
              <Text>{formatDate(profile.last_login_at)}</Text>
            </div>
          </Col>
        </Row>
      </Card>

      {/* 商户信息 */}
      <Card className="mb-6 border-0 shadow-sm rounded-xl">
        <Row gutter={[24, 16]}>
          <Col span={12}>
            <div className="flex items-center gap-2">
              <Text type="secondary">商户ID：</Text>
              <Tag color="processing">{profile.merchant_id}</Tag>
            </div>
          </Col>
          <Col span={12}>
            <div className="flex items-center gap-2">
              <Text type="secondary">商户密钥：</Text>
              <Tag color="gold">{profile.merchant_key}</Tag>
              <Button 
                type="primary" 
                size="small" 
                onClick={handleResetKey}
                icon={<ReloadOutlined />}
              >
                重置
              </Button>
            </div>
          </Col>
          <Col span={24}>
            <div className="flex items-center gap-2">
              <Text type="secondary">推广链接：</Text>
              <Input 
                value={inviteInfo?.invite_link || ''} 
                readOnly 
                className="flex-1"
                addonAfter={
                  <CopyOutlined 
                    className="cursor-pointer" 
                    onClick={() => copyToClipboard(inviteInfo?.invite_link || '', '推广链接')}
                  />
                }
              />
            </div>
            <Text type="secondary" className="text-xs mt-1 block">
              通过该链接消费的人会给您丰厚的佣金
            </Text>
          </Col>
          <Col span={12}>
            <div className="flex items-center gap-2">
              <Text type="secondary">推广人数：</Text>
              <Text>{profile.referral_count}</Text>
            </div>
          </Col>
        </Row>
      </Card>

      {/* 资产统计 */}
      <Row gutter={16}>
        <Col xs={24} sm={12} lg={6}>
          <Card className="border-0 shadow-sm rounded-xl bg-gradient-to-br from-blue-50 to-blue-100">
            <Statistic
              title={<span className="text-blue-600"><WalletOutlined /> 余额</span>}
              value={profile.balance}
              precision={2}
              prefix="¥"
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card className="border-0 shadow-sm rounded-xl bg-gradient-to-br from-yellow-50 to-yellow-100">
            <Statistic
              title={<span className="text-yellow-600"><GiftOutlined /> 硬币</span>}
              value={profile.coin}
              precision={2}
              prefix="¥"
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card className="border-0 shadow-sm rounded-xl bg-gradient-to-br from-green-50 to-green-100">
            <Statistic
              title={<span className="text-green-600"><DollarOutlined /> 总充值</span>}
              value={profile.total_recharge}
              precision={2}
              prefix="¥"
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card className="border-0 shadow-sm rounded-xl bg-gradient-to-br from-purple-50 to-purple-100">
            <Statistic
              title={<span className="text-purple-600"><TeamOutlined /> 总收入(硬币)</span>}
              value={profile.total_income}
              precision={2}
              prefix="¥"
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
      </Row>
    </div>
  )
}
