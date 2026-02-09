import { useEffect, useState } from 'react'
import {
  Table, Button, Space, Select, Tag, Card, Typography,
  Row, Col, Statistic, message, Modal, Input, Descriptions
} from 'antd'
import { 
  ReloadOutlined, CheckOutlined, CloseOutlined, 
  DollarOutlined, EyeOutlined 
} from '@ant-design/icons'
import * as adminApi from '../../api/admin'

const { Title, Text } = Typography
const { TextArea } = Input

export default function Withdrawals() {
  const [loading, setLoading] = useState(false)
  const [withdrawals, setWithdrawals] = useState<adminApi.Withdrawal[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [filters, setFilters] = useState<{ status?: number }>({})
  const [stats, setStats] = useState({
    pending_count: 0,
    approved_count: 0,
    completed_amount: 0,
  })

  // 详情弹窗
  const [detailVisible, setDetailVisible] = useState(false)
  const [currentWithdrawal, setCurrentWithdrawal] = useState<adminApi.Withdrawal | null>(null)

  // 审核弹窗
  const [reviewVisible, setReviewVisible] = useState(false)
  const [reviewAction, setReviewAction] = useState<'approve' | 'reject'>('approve')
  const [reviewRemark, setReviewRemark] = useState('')

  useEffect(() => {
    loadData()
    loadStats()
  }, [page, filters])

  const loadData = async () => {
    setLoading(true)
    try {
      const res = await adminApi.getWithdrawals({
        ...filters,
        page,
        limit: 20,
      })
      setWithdrawals(res.items)
      setTotal(res.total)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  const loadStats = async () => {
    try {
      const res = await adminApi.getWithdrawalStats()
      setStats(res)
    } catch (e) {
      console.error(e)
    }
  }

  const handleReview = (withdrawal: adminApi.Withdrawal, action: 'approve' | 'reject') => {
    setCurrentWithdrawal(withdrawal)
    setReviewAction(action)
    setReviewRemark('')
    setReviewVisible(true)
  }

  const handleReviewSubmit = async () => {
    if (!currentWithdrawal) return
    
    try {
      await adminApi.reviewWithdrawal(currentWithdrawal.id, reviewAction, reviewRemark)
      message.success('操作成功')
      setReviewVisible(false)
      loadData()
      loadStats()
    } catch (e: any) {
      message.error(e.message || '操作失败')
    }
  }

  const handlePaid = async (id: number) => {
    try {
      await adminApi.paidWithdrawal(id)
      message.success('已确认打款')
      loadData()
      loadStats()
    } catch (e: any) {
      message.error(e.message || '操作失败')
    }
  }

  const getStatusTag = (status: number) => {
    const map: Record<number, { color: string; text: string }> = {
      0: { color: 'orange', text: '待审核' },
      1: { color: 'blue', text: '待打款' },
      2: { color: 'green', text: '已完成' },
      3: { color: 'red', text: '已拒绝' },
      4: { color: 'default', text: '已取消' },
    }
    const item = map[status] || { color: 'default', text: '未知' }
    return <Tag color={item.color}>{item.text}</Tag>
  }

  const getMethodTag = (method: string) => {
    const map: Record<string, { color: string; text: string }> = {
      alipay: { color: 'blue', text: '支付宝' },
      wechat: { color: 'green', text: '微信' },
      bank: { color: 'purple', text: '银行卡' },
    }
    const item = map[method] || { color: 'default', text: method }
    return <Tag color={item.color}>{item.text}</Tag>
  }

  const columns = [
    {
      title: '提现单号',
      dataIndex: 'withdraw_no',
      width: 180,
      render: (v: string) => <Text copyable={{ text: v }}>{v}</Text>,
    },
    { title: '会员', dataIndex: 'username', width: 100 },
    {
      title: '提现金额',
      dataIndex: 'amount',
      width: 100,
      render: (v: number) => <span className="text-red-500 font-medium">¥{v}</span>,
    },
    {
      title: '手续费',
      dataIndex: 'fee',
      width: 80,
      render: (v: number) => `¥${v}`,
    },
    {
      title: '实际到账',
      dataIndex: 'actual_amount',
      width: 100,
      render: (v: number) => <span className="text-green-500 font-medium">¥{v}</span>,
    },
    {
      title: '提现方式',
      dataIndex: 'method',
      width: 100,
      render: (v: string) => getMethodTag(v),
    },
    {
      title: '收款账号',
      dataIndex: 'account',
      ellipsis: true,
      width: 150,
    },
    {
      title: '状态',
      dataIndex: 'status',
      width: 100,
      render: (status: number) => getStatusTag(status),
    },
    { title: '申请时间', dataIndex: 'created_at', width: 170 },
    {
      title: '操作',
      key: 'action',
      width: 180,
      render: (_: any, record: adminApi.Withdrawal) => (
        <Space>
          <Button 
            type="link" 
            icon={<EyeOutlined />} 
            size="small"
            onClick={() => {
              setCurrentWithdrawal(record)
              setDetailVisible(true)
            }}
          >
            详情
          </Button>
          {record.status === 0 && (
            <>
              <Button 
                type="link" 
                icon={<CheckOutlined />} 
                size="small"
                onClick={() => handleReview(record, 'approve')}
              >
                通过
              </Button>
              <Button 
                type="link" 
                danger
                icon={<CloseOutlined />} 
                size="small"
                onClick={() => handleReview(record, 'reject')}
              >
                拒绝
              </Button>
            </>
          )}
          {record.status === 1 && (
            <Button 
              type="link" 
              icon={<DollarOutlined />} 
              size="small"
              onClick={() => handlePaid(record.id)}
            >
              确认打款
            </Button>
          )}
        </Space>
      ),
    },
  ]

  return (
    <div>
      <Title level={4}>提现管理</Title>

      {/* 统计卡片 */}
      <Row gutter={16} className="mb-6">
        <Col span={8}>
          <Card className="rounded-xl border-0 shadow-sm">
            <Statistic 
              title="待审核" 
              value={stats.pending_count} 
              valueStyle={{ color: '#fa8c16' }}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card className="rounded-xl border-0 shadow-sm">
            <Statistic 
              title="待打款" 
              value={stats.approved_count}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card className="rounded-xl border-0 shadow-sm">
            <Statistic 
              title="已完成金额" 
              value={stats.completed_amount} 
              precision={2}
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
      </Row>

      <Card className="rounded-xl border-0 shadow-sm">
        <div className="flex justify-between mb-4">
          <Space>
            <Select
              placeholder="状态"
              allowClear
              style={{ width: 120 }}
              onChange={(v) => {
                setFilters({ ...filters, status: v })
                setPage(1)
              }}
            >
              <Select.Option value={0}>待审核</Select.Option>
              <Select.Option value={1}>待打款</Select.Option>
              <Select.Option value={2}>已完成</Select.Option>
              <Select.Option value={3}>已拒绝</Select.Option>
            </Select>
          </Space>
          <Button icon={<ReloadOutlined />} onClick={loadData}>
            刷新
          </Button>
        </div>

        <Table
          columns={columns}
          dataSource={withdrawals}
          rowKey="id"
          loading={loading}
          pagination={{
            current: page,
            total,
            pageSize: 20,
            onChange: setPage,
            showTotal: (t) => `共 ${t} 条`,
          }}
        />
      </Card>

      {/* 详情弹窗 */}
      <Modal
        title="提现详情"
        open={detailVisible}
        onCancel={() => setDetailVisible(false)}
        footer={null}
        width={600}
      >
        {currentWithdrawal && (
          <Descriptions bordered column={2} size="small">
            <Descriptions.Item label="提现单号" span={2}>
              {currentWithdrawal.withdraw_no}
            </Descriptions.Item>
            <Descriptions.Item label="会员">{currentWithdrawal.username}</Descriptions.Item>
            <Descriptions.Item label="状态">{getStatusTag(currentWithdrawal.status)}</Descriptions.Item>
            <Descriptions.Item label="提现金额">
              <span className="text-red-500">¥{currentWithdrawal.amount}</span>
            </Descriptions.Item>
            <Descriptions.Item label="手续费">¥{currentWithdrawal.fee}</Descriptions.Item>
            <Descriptions.Item label="实际到账">
              <span className="text-green-500">¥{currentWithdrawal.actual_amount}</span>
            </Descriptions.Item>
            <Descriptions.Item label="提现方式">{getMethodTag(currentWithdrawal.method)}</Descriptions.Item>
            <Descriptions.Item label="收款账号" span={2}>{currentWithdrawal.account}</Descriptions.Item>
            <Descriptions.Item label="收款人">{currentWithdrawal.account_name || '-'}</Descriptions.Item>
            <Descriptions.Item label="申请时间">{currentWithdrawal.created_at}</Descriptions.Item>
            <Descriptions.Item label="用户备注" span={2}>
              {currentWithdrawal.user_remark || '-'}
            </Descriptions.Item>
            <Descriptions.Item label="管理员备注" span={2}>
              {currentWithdrawal.admin_remark || '-'}
            </Descriptions.Item>
          </Descriptions>
        )}
      </Modal>

      {/* 审核弹窗 */}
      <Modal
        title={reviewAction === 'approve' ? '审核通过' : '审核拒绝'}
        open={reviewVisible}
        onOk={handleReviewSubmit}
        onCancel={() => setReviewVisible(false)}
        okText={reviewAction === 'approve' ? '通过' : '拒绝'}
        okButtonProps={{ danger: reviewAction === 'reject' }}
      >
        <div className="mb-4">
          {currentWithdrawal && (
            <div className="bg-gray-50 p-4 rounded">
              <p>会员：{currentWithdrawal.username}</p>
              <p>提现金额：<span className="text-red-500">¥{currentWithdrawal.amount}</span></p>
              <p>收款账号：{currentWithdrawal.account}</p>
            </div>
          )}
        </div>
        <div>
          <label className="block mb-2">备注（可选）</label>
          <TextArea
            rows={3}
            value={reviewRemark}
            onChange={(e) => setReviewRemark(e.target.value)}
            placeholder={reviewAction === 'reject' ? '请填写拒绝原因' : '可选'}
          />
        </div>
      </Modal>
    </div>
  )
}
