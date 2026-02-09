import { useEffect, useState } from 'react'
import { Card, Typography, Table, Statistic, Row, Col, Input, Button, message } from 'antd'
import { TeamOutlined, CopyOutlined, UserAddOutlined } from '@ant-design/icons'
import dayjs from 'dayjs'
import api from '../../api'

const { Title, Text } = Typography

interface ReferralItem {
  id: number
  username: string
  created_at: string
  total_recharge: number
}

interface InviteInfo {
  invite_code: string
  invite_link: string
}

export default function UserReferrals() {
  const [loading, setLoading] = useState(false)
  const [data, setData] = useState<ReferralItem[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize] = useState(20)
  const [inviteInfo, setInviteInfo] = useState<InviteInfo | null>(null)

  useEffect(() => {
    loadData()
    loadInviteInfo()
  }, [page])

  const loadData = async () => {
    setLoading(true)
    try {
      const res = await api.get('/users/me/referrals', {
        params: { page, limit: pageSize }
      })
      setData(res.items || [])
      setTotal(res.total || 0)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  const loadInviteInfo = async () => {
    try {
      const res = await api.get('/users/me/invite-link')
      setInviteInfo(res)
    } catch (e) {
      console.error(e)
    }
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
    message.success('已复制到剪贴板')
  }

  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 80,
    },
    {
      title: '用户名',
      dataIndex: 'username',
      key: 'username',
    },
    {
      title: '注册时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (text: string) => text ? dayjs(text).format('YYYY-MM-DD HH:mm') : '-',
    },
    {
      title: '累计充值',
      dataIndex: 'total_recharge',
      key: 'total_recharge',
      width: 120,
      render: (amount: number) => <Text className="text-green-500">¥{amount.toFixed(2)}</Text>,
    },
  ]

  return (
    <div>
      <Title level={4} className="flex items-center gap-2">
        <TeamOutlined /> 我的下级
      </Title>

      {/* 统计卡片 */}
      <Row gutter={16} className="mb-6">
        <Col span={8}>
          <Card className="border-0 shadow-sm rounded-xl">
            <Statistic 
              title="邀请人数" 
              value={total} 
              prefix={<UserAddOutlined />}
            />
          </Card>
        </Col>
        <Col span={16}>
          <Card className="border-0 shadow-sm rounded-xl">
            <div className="flex items-center gap-4">
              <Text type="secondary">推广链接：</Text>
              <Input 
                value={inviteInfo?.invite_link || ''} 
                readOnly 
                className="flex-1"
              />
              <Button 
                type="primary" 
                icon={<CopyOutlined />}
                onClick={() => copyToClipboard(inviteInfo?.invite_link || '')}
              >
                复制
              </Button>
            </div>
          </Card>
        </Col>
      </Row>

      {/* 下级列表 */}
      <Card className="border-0 shadow-sm rounded-xl">
        <Table
          rowKey="id"
          loading={loading}
          dataSource={data}
          columns={columns}
          pagination={{
            current: page,
            pageSize,
            total,
            onChange: setPage,
            showSizeChanger: false,
          }}
          size="small"
          locale={{ emptyText: '暂无下级用户' }}
        />
      </Card>
    </div>
  )
}
