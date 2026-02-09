import { useEffect, useState } from 'react'
import {
  Table, Button, Space, Modal, Form, Input, InputNumber,
  Select, message, Tag, Card, Typography, Descriptions, Switch
} from 'antd'
import { EyeOutlined, EditOutlined, ReloadOutlined, DollarOutlined, KeyOutlined } from '@ant-design/icons'
import * as adminApi from '../../api/admin'

const { Title } = Typography

export default function Users() {
  const [loading, setLoading] = useState(false)
  const [users, setUsers] = useState<adminApi.User[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [filters, setFilters] = useState<{
    status?: number
    keywords?: string
  }>({})

  // 详情弹窗
  const [detailModalVisible, setDetailModalVisible] = useState(false)
  const [currentUser, setCurrentUser] = useState<adminApi.UserDetail | null>(null)

  // 编辑弹窗
  const [editModalVisible, setEditModalVisible] = useState(false)
  const [editForm] = Form.useForm()

  // 调整余额弹窗
  const [balanceModalVisible, setBalanceModalVisible] = useState(false)
  const [balanceForm] = Form.useForm()

  // 重置密码弹窗
  const [passwordModalVisible, setPasswordModalVisible] = useState(false)
  const [passwordForm] = Form.useForm()

  useEffect(() => {
    loadUsers()
  }, [page, filters])

  const loadUsers = async () => {
    setLoading(true)
    try {
      const res = await adminApi.getUsers({
        ...filters,
        page,
        limit: 20,
      })
      setUsers(res.items)
      setTotal(res.total)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  const handleViewDetail = async (id: number) => {
    try {
      const detail = await adminApi.getUser(id)
      setCurrentUser(detail)
      setDetailModalVisible(true)
    } catch (e) {
      console.error(e)
    }
  }

  const handleEdit = (user: adminApi.User) => {
    setCurrentUser(user as any)
    editForm.setFieldsValue({
      status: user.status,
      is_admin: user.is_admin,
      business_level: user.business_level,
    })
    setEditModalVisible(true)
  }

  const handleEditSubmit = async () => {
    if (!currentUser) return

    try {
      const values = await editForm.validateFields()
      await adminApi.updateUser(currentUser.id, values)
      message.success('更新成功')
      setEditModalVisible(false)
      loadUsers()
    } catch (e) {
      console.error(e)
    }
  }

  const handleAdjustBalance = (user: adminApi.User) => {
    setCurrentUser(user as any)
    balanceForm.resetFields()
    setBalanceModalVisible(true)
  }

  const handleBalanceSubmit = async () => {
    if (!currentUser) return

    try {
      const values = await balanceForm.validateFields()
      await adminApi.adjustUserBalance(currentUser.id, values.amount, values.description)
      message.success('调整成功')
      setBalanceModalVisible(false)
      loadUsers()
    } catch (e) {
      console.error(e)
    }
  }

  const handleResetPassword = (user: adminApi.User) => {
    setCurrentUser(user as any)
    passwordForm.resetFields()
    setPasswordModalVisible(true)
  }

  const handlePasswordSubmit = async () => {
    if (!currentUser) return

    try {
      const values = await passwordForm.validateFields()
      await adminApi.resetUserPassword(currentUser.id, values.password)
      message.success('密码已重置')
      setPasswordModalVisible(false)
    } catch (e) {
      console.error(e)
    }
  }

  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 80 },
    {
      title: '用户名',
      dataIndex: 'username',
      key: 'username',
      render: (text: string, record: adminApi.User) => (
        <Space>
          <span>{text}</span>
          {record.is_admin && <Tag color="red">管理员</Tag>}
          {record.business_level > 0 && <Tag color="blue">商户</Tag>}
        </Space>
      ),
    },
    {
      title: '联系方式',
      key: 'contact',
      render: (_: any, record: adminApi.User) => (
        <div>
          {record.email && <div>{record.email}</div>}
          {record.phone && <div>{record.phone}</div>}
        </div>
      ),
    },
    {
      title: '余额',
      dataIndex: 'balance',
      key: 'balance',
      width: 120,
      render: (v: number) => <span className="text-green-600">¥{v.toFixed(2)}</span>,
    },
    {
      title: '累计充值',
      dataIndex: 'total_recharge',
      key: 'total_recharge',
      width: 120,
      render: (v: number) => `¥${v.toFixed(2)}`,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 80,
      render: (status: number) => (
        <Tag color={status === 1 ? 'green' : 'red'}>
          {status === 1 ? '正常' : '禁用'}
        </Tag>
      ),
    },
    {
      title: '注册时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
    },
    {
      title: '操作',
      key: 'action',
      width: 200,
      render: (_: any, record: adminApi.User) => (
        <Space size="small">
          <Button
            type="link"
            icon={<EyeOutlined />}
            size="small"
            onClick={() => handleViewDetail(record.id)}
          >
            详情
          </Button>
          <Button
            type="link"
            icon={<EditOutlined />}
            size="small"
            onClick={() => handleEdit(record)}
          >
            编辑
          </Button>
          <Button
            type="link"
            icon={<DollarOutlined />}
            size="small"
            onClick={() => handleAdjustBalance(record)}
          >
            余额
          </Button>
          <Button
            type="link"
            icon={<KeyOutlined />}
            size="small"
            onClick={() => handleResetPassword(record)}
          >
            密码
          </Button>
        </Space>
      ),
    },
  ]

  return (
    <div>
      <Title level={4}>用户管理</Title>

      <Card>
        <div className="flex justify-between mb-4">
          <Space>
            <Select
              placeholder="状态"
              allowClear
              style={{ width: 100 }}
              onChange={(v) => {
                setFilters({ ...filters, status: v })
                setPage(1)
              }}
            >
              <Select.Option value={1}>正常</Select.Option>
              <Select.Option value={0}>禁用</Select.Option>
            </Select>
            <Input.Search
              placeholder="搜索用户名/邮箱/手机"
              allowClear
              onSearch={(v) => {
                setFilters({ ...filters, keywords: v })
                setPage(1)
              }}
              style={{ width: 250 }}
            />
          </Space>
          <Button icon={<ReloadOutlined />} onClick={loadUsers}>
            刷新
          </Button>
        </div>

        <Table
          columns={columns}
          dataSource={users}
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

      {/* 用户详情弹窗 */}
      <Modal
        title="用户详情"
        open={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        footer={null}
        width={600}
      >
        {currentUser && (
          <Descriptions bordered column={2} size="small">
            <Descriptions.Item label="ID">{currentUser.id}</Descriptions.Item>
            <Descriptions.Item label="用户名">{currentUser.username}</Descriptions.Item>
            <Descriptions.Item label="邮箱">{currentUser.email || '-'}</Descriptions.Item>
            <Descriptions.Item label="手机">{currentUser.phone || '-'}</Descriptions.Item>
            <Descriptions.Item label="余额">
              <span className="text-green-600">¥{currentUser.balance.toFixed(2)}</span>
            </Descriptions.Item>
            <Descriptions.Item label="积分">{currentUser.coin}</Descriptions.Item>
            <Descriptions.Item label="累计充值">¥{currentUser.total_recharge.toFixed(2)}</Descriptions.Item>
            <Descriptions.Item label="上级ID">{currentUser.parent_id || '-'}</Descriptions.Item>
            <Descriptions.Item label="支付宝">{currentUser.alipay || '-'}</Descriptions.Item>
            <Descriptions.Item label="微信">{currentUser.wechat || '-'}</Descriptions.Item>
            <Descriptions.Item label="注册时间">{currentUser.created_at}</Descriptions.Item>
            <Descriptions.Item label="最后登录">{currentUser.last_login_at || '-'}</Descriptions.Item>
            <Descriptions.Item label="最后登录IP">{currentUser.last_login_ip || '-'}</Descriptions.Item>
            <Descriptions.Item label="状态">
              <Tag color={currentUser.status === 1 ? 'green' : 'red'}>
                {currentUser.status === 1 ? '正常' : '禁用'}
              </Tag>
            </Descriptions.Item>
          </Descriptions>
        )}
      </Modal>

      {/* 编辑用户弹窗 */}
      <Modal
        title="编辑用户"
        open={editModalVisible}
        onOk={handleEditSubmit}
        onCancel={() => setEditModalVisible(false)}
      >
        <Form form={editForm} layout="vertical">
          <Form.Item name="status" label="状态">
            <Select>
              <Select.Option value={1}>正常</Select.Option>
              <Select.Option value={0}>禁用</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item name="is_admin" label="管理员" valuePropName="checked">
            <Switch />
          </Form.Item>
          <Form.Item name="business_level" label="商户等级">
            <InputNumber min={0} className="w-full" />
          </Form.Item>
        </Form>
      </Modal>

      {/* 调整余额弹窗 */}
      <Modal
        title="调整余额"
        open={balanceModalVisible}
        onOk={handleBalanceSubmit}
        onCancel={() => setBalanceModalVisible(false)}
      >
        <Form form={balanceForm} layout="vertical">
          <Form.Item
            name="amount"
            label="调整金额"
            rules={[{ required: true, message: '请输入金额' }]}
            extra="正数为增加，负数为减少"
          >
            <InputNumber className="w-full" precision={2} />
          </Form.Item>
          <Form.Item
            name="description"
            label="调整原因"
            rules={[{ required: true, message: '请输入原因' }]}
          >
            <Input placeholder="如：充值奖励、系统补偿等" />
          </Form.Item>
        </Form>
      </Modal>

      {/* 重置密码弹窗 */}
      <Modal
        title="重置密码"
        open={passwordModalVisible}
        onOk={handlePasswordSubmit}
        onCancel={() => setPasswordModalVisible(false)}
      >
        <Form form={passwordForm} layout="vertical">
          <Form.Item
            name="password"
            label="新密码"
            rules={[
              { required: true, message: '请输入新密码' },
              { min: 6, message: '密码至少6位' },
            ]}
          >
            <Input.Password />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
