import { useEffect, useState } from 'react'
import {
  Table, Button, Space, Modal, Form, Input, Select,
  message, Tag, Card, Typography, Descriptions
} from 'antd'
import { EyeOutlined, SendOutlined, ReloadOutlined } from '@ant-design/icons'
import * as adminApi from '../../api/admin'

const { Title, Text } = Typography
const { TextArea } = Input

export default function Orders() {
  const [loading, setLoading] = useState(false)
  const [orders, setOrders] = useState<adminApi.Order[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [filters, setFilters] = useState<{
    status?: number
    delivery_status?: number
    trade_no?: string
    contact?: string
  }>({})

  // 详情弹窗
  const [detailModalVisible, setDetailModalVisible] = useState(false)
  const [currentOrder, setCurrentOrder] = useState<adminApi.OrderDetail | null>(null)

  // 发货弹窗
  const [deliverModalVisible, setDeliverModalVisible] = useState(false)
  const [deliverForm] = Form.useForm()
  const [delivering, setDelivering] = useState(false)

  useEffect(() => {
    loadOrders()
  }, [page, filters])

  const loadOrders = async () => {
    setLoading(true)
    try {
      const res = await adminApi.getOrders({
        ...filters,
        page,
        limit: 20,
      })
      setOrders(res.items)
      setTotal(res.total)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  const handleViewDetail = async (id: number) => {
    try {
      const detail = await adminApi.getOrder(id)
      setCurrentOrder(detail)
      setDetailModalVisible(true)
    } catch (e) {
      console.error(e)
    }
  }

  const handleDeliver = (order: adminApi.Order) => {
    setCurrentOrder(order as any)
    deliverForm.resetFields()
    setDeliverModalVisible(true)
  }

  const handleDeliverSubmit = async () => {
    if (!currentOrder) return

    try {
      const values = await deliverForm.validateFields()
      setDelivering(true)
      await adminApi.deliverOrder(currentOrder.id, values.secret)
      message.success('发货成功')
      setDeliverModalVisible(false)
      loadOrders()
    } catch (e) {
      console.error(e)
    } finally {
      setDelivering(false)
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
      width: 200,
      render: (text: string) => <Text copyable={{ text }}>{text}</Text>,
    },
    {
      title: '商品',
      dataIndex: 'commodity_name',
      key: 'commodity_name',
      ellipsis: true,
    },
    {
      title: '金额',
      dataIndex: 'amount',
      key: 'amount',
      width: 100,
      render: (v: number) => <span className="text-red-500">¥{v}</span>,
    },
    {
      title: '数量',
      dataIndex: 'quantity',
      key: 'quantity',
      width: 80,
    },
    {
      title: '联系方式',
      dataIndex: 'contact',
      key: 'contact',
      width: 150,
      ellipsis: true,
    },
    {
      title: '状态',
      key: 'status',
      width: 100,
      render: (_: any, record: adminApi.Order) => getStatusTag(record.status, record.delivery_status),
    },
    {
      title: '下单时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      render: (_: any, record: adminApi.Order) => (
        <Space>
          <Button
            type="link"
            icon={<EyeOutlined />}
            size="small"
            onClick={() => handleViewDetail(record.id)}
          >
            详情
          </Button>
          {record.status === 1 && record.delivery_status === 0 && (
            <Button
              type="link"
              icon={<SendOutlined />}
              size="small"
              onClick={() => handleDeliver(record)}
            >
              发货
            </Button>
          )}
        </Space>
      ),
    },
  ]

  return (
    <div>
      <Title level={4}>订单管理</Title>

      <Card>
        <div className="flex justify-between mb-4">
          <Space>
            <Select
              placeholder="订单状态"
              allowClear
              style={{ width: 120 }}
              onChange={(v) => {
                setFilters({ ...filters, status: v })
                setPage(1)
              }}
            >
              <Select.Option value={0}>待支付</Select.Option>
              <Select.Option value={1}>已支付</Select.Option>
              <Select.Option value={2}>已取消</Select.Option>
              <Select.Option value={3}>已退款</Select.Option>
            </Select>
            <Select
              placeholder="发货状态"
              allowClear
              style={{ width: 120 }}
              onChange={(v) => {
                setFilters({ ...filters, delivery_status: v })
                setPage(1)
              }}
            >
              <Select.Option value={0}>待发货</Select.Option>
              <Select.Option value={1}>已发货</Select.Option>
            </Select>
            <Input.Search
              placeholder="订单号"
              allowClear
              onSearch={(v) => {
                setFilters({ ...filters, trade_no: v })
                setPage(1)
              }}
              style={{ width: 200 }}
            />
            <Input.Search
              placeholder="联系方式"
              allowClear
              onSearch={(v) => {
                setFilters({ ...filters, contact: v })
                setPage(1)
              }}
              style={{ width: 150 }}
            />
          </Space>
          <Button icon={<ReloadOutlined />} onClick={loadOrders}>
            刷新
          </Button>
        </div>

        <Table
          columns={columns}
          dataSource={orders}
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

      {/* 订单详情弹窗 */}
      <Modal
        title="订单详情"
        open={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        footer={null}
        width={700}
      >
        {currentOrder && (
          <Descriptions bordered column={2} size="small">
            <Descriptions.Item label="订单号" span={2}>
              <Text copyable>{currentOrder.trade_no}</Text>
            </Descriptions.Item>
            <Descriptions.Item label="商品">{currentOrder.commodity_name}</Descriptions.Item>
            <Descriptions.Item label="支付方式">{currentOrder.payment_name}</Descriptions.Item>
            <Descriptions.Item label="金额">
              <span className="text-red-500">¥{currentOrder.amount}</span>
            </Descriptions.Item>
            <Descriptions.Item label="数量">{currentOrder.quantity}</Descriptions.Item>
            <Descriptions.Item label="联系方式">{currentOrder.contact}</Descriptions.Item>
            <Descriptions.Item label="状态">
              {getStatusTag(currentOrder.status, currentOrder.delivery_status)}
            </Descriptions.Item>
            <Descriptions.Item label="下单IP">{currentOrder.create_ip}</Descriptions.Item>
            <Descriptions.Item label="下单时间">{currentOrder.created_at}</Descriptions.Item>
            <Descriptions.Item label="支付时间">{currentOrder.paid_at || '-'}</Descriptions.Item>
            <Descriptions.Item label="第三方订单号">
              {currentOrder.external_trade_no || '-'}
            </Descriptions.Item>
            {currentOrder.secret && (
              <Descriptions.Item label="卡密内容" span={2}>
                <Text copyable className="whitespace-pre-wrap font-mono bg-gray-50 p-2 block">
                  {currentOrder.secret}
                </Text>
              </Descriptions.Item>
            )}
          </Descriptions>
        )}
      </Modal>

      {/* 发货弹窗 */}
      <Modal
        title="手动发货"
        open={deliverModalVisible}
        onOk={handleDeliverSubmit}
        onCancel={() => setDeliverModalVisible(false)}
        confirmLoading={delivering}
      >
        <Form form={deliverForm} layout="vertical">
          <Form.Item
            name="secret"
            label="发货内容"
            rules={[{ required: true, message: '请输入发货内容' }]}
          >
            <TextArea rows={6} placeholder="请输入要发送给用户的卡密或信息" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
