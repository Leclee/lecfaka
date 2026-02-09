import { useEffect, useState } from 'react'
import { 
  Card, Typography, Table, Input, DatePicker, Button, Space, 
  Tag, Modal, message, Tabs
} from 'antd'
import { SearchOutlined, DownloadOutlined, ShoppingCartOutlined } from '@ant-design/icons'
import dayjs from 'dayjs'
import api from '../../api'

const { Title, Text } = Typography
const { RangePicker } = DatePicker

interface OrderItem {
  trade_no: string
  amount: number
  quantity: number
  status: number
  delivery_status: number
  delivery_way: number
  created_at: string
  paid_at?: string
  commodity_name?: string
  commodity_cover?: string
  contact?: string
  payment_method?: string
  cards_info?: string
  leave_message?: string
}

export default function UserOrders() {
  const [loading, setLoading] = useState(false)
  const [data, setData] = useState<OrderItem[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize] = useState(10)
  const [activeTab, setActiveTab] = useState('all')
  const [searchTradeNo, setSearchTradeNo] = useState('')
  const [detailModal, setDetailModal] = useState<OrderItem | null>(null)

  useEffect(() => {
    loadData()
  }, [page, activeTab])

  const loadData = async () => {
    setLoading(true)
    try {
      const status = activeTab === 'paid' ? 1 : activeTab === 'unpaid' ? 0 : undefined
      const res = await api.get('/users/me/orders', {
        params: { page, limit: pageSize, status, trade_no: searchTradeNo || undefined }
      })
      setData(res.items || [])
      setTotal(res.total || 0)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = () => {
    setPage(1)
    loadData()
  }

  const handleDownloadCards = (order: OrderItem) => {
    if (!order.cards_info) {
      message.warning('暂无卡密信息')
      return
    }
    const blob = new Blob([order.cards_info], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${order.trade_no}.txt`
    a.click()
    URL.revokeObjectURL(url)
    message.success('下载成功')
  }

  const getStatusTag = (status: number) => {
    if (status === 1) return <Tag color="success">已支付</Tag>
    return <Tag color="warning">未支付</Tag>
  }

  const getDeliveryStatusTag = (status: number) => {
    if (status === 1) return <Tag color="success">已发货</Tag>
    return <Tag color="processing">待发货</Tag>
  }

  const getDeliveryWayTag = (way: number) => {
    if (way === 0) return <Tag color="cyan">自动发货</Tag>
    return <Tag color="orange">手动发货</Tag>
  }

  const columns = [
    {
      title: '订单号',
      dataIndex: 'trade_no',
      key: 'trade_no',
      width: 180,
      render: (text: string) => (
        <Text className="text-xs font-mono">{text}</Text>
      ),
    },
    {
      title: '商品',
      key: 'commodity',
      render: (_: any, record: OrderItem) => (
        <div className="flex items-center gap-2">
          {record.commodity_cover && (
            <img src={record.commodity_cover} alt="" className="w-8 h-8 rounded" />
          )}
          <Text ellipsis className="max-w-32">{record.commodity_name || '-'}</Text>
        </div>
      ),
    },
    {
      title: '数量',
      dataIndex: 'quantity',
      key: 'quantity',
      width: 80,
    },
    {
      title: '金额',
      dataIndex: 'amount',
      key: 'amount',
      width: 100,
      render: (amount: number) => <Text className="text-red-500">¥{amount}</Text>,
    },
    {
      title: '发货方式',
      dataIndex: 'delivery_way',
      key: 'delivery_way',
      width: 100,
      render: (way: number) => getDeliveryWayTag(way),
    },
    {
      title: '付款状态',
      dataIndex: 'status',
      key: 'status',
      width: 90,
      render: (status: number) => getStatusTag(status),
    },
    {
      title: '发货状态',
      dataIndex: 'delivery_status',
      key: 'delivery_status',
      width: 90,
      render: (status: number) => getDeliveryStatusTag(status),
    },
    {
      title: '下单时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 160,
      render: (text: string) => text ? dayjs(text).format('YYYY-MM-DD HH:mm') : '-',
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      render: (_: any, record: OrderItem) => (
        <Space>
          <Button type="link" size="small" onClick={() => setDetailModal(record)}>
            详情
          </Button>
        </Space>
      ),
    },
  ]

  return (
    <div>
      <Title level={4} className="flex items-center gap-2">
        <ShoppingCartOutlined /> 购买记录
      </Title>

      {/* 搜索栏 */}
      <Card className="mb-4 border-0 shadow-sm rounded-xl">
        <Space wrap>
          <Input 
            placeholder="订单号" 
            value={searchTradeNo}
            onChange={(e) => setSearchTradeNo(e.target.value)}
            style={{ width: 200 }}
          />
          <RangePicker placeholder={['从 下单时间', '到 下单时间']} />
          <Button type="primary" icon={<SearchOutlined />} onClick={handleSearch}>
            查询
          </Button>
        </Space>
      </Card>

      {/* Tab切换 */}
      <Card className="border-0 shadow-sm rounded-xl">
        <Tabs
          activeKey={activeTab}
          onChange={(key) => {
            setActiveTab(key)
            setPage(1)
          }}
          items={[
            { key: 'all', label: '全部' },
            { key: 'paid', label: '已支付' },
            { key: 'unpaid', label: '未支付' },
          ]}
        />

        <Table
          rowKey="trade_no"
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
          scroll={{ x: 1000 }}
        />
      </Card>

      {/* 订单详情弹窗 */}
      <Modal
        title="订单详情"
        open={!!detailModal}
        onCancel={() => setDetailModal(null)}
        footer={null}
        width={600}
      >
        {detailModal && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Text type="secondary">订单号</Text>
                <div className="font-mono">{detailModal.trade_no}</div>
              </div>
              <div>
                <Text type="secondary">商品</Text>
                <div className="flex items-center gap-2">
                  {detailModal.commodity_cover && (
                    <img src={detailModal.commodity_cover} alt="" className="w-6 h-6 rounded" />
                  )}
                  {detailModal.commodity_name || '-'}
                </div>
              </div>
              <div>
                <Text type="secondary">SKU</Text>
                <div>-</div>
              </div>
              <div>
                <Text type="secondary">数量</Text>
                <div>{detailModal.quantity}</div>
              </div>
              <div>
                <Text type="secondary">金额</Text>
                <div className="text-red-500">¥{detailModal.amount}</div>
              </div>
              <div>
                <Text type="secondary">发货方式</Text>
                <div>{getDeliveryWayTag(detailModal.delivery_way)}</div>
              </div>
              <div>
                <Text type="secondary">支付方式</Text>
                <div>{detailModal.payment_method || '-'}</div>
              </div>
              <div>
                <Text type="secondary">付款状态</Text>
                <div>{getStatusTag(detailModal.status)}</div>
              </div>
              <div>
                <Text type="secondary">发货状态</Text>
                <div>{getDeliveryStatusTag(detailModal.delivery_status)}</div>
              </div>
              <div>
                <Text type="secondary">商家留言</Text>
                <div>{detailModal.leave_message || '-'}</div>
              </div>
            </div>

            {detailModal.cards_info && (
              <div>
                <Text type="secondary">宝贝信息</Text>
                <Card className="mt-2 bg-gray-50">
                  <pre className="whitespace-pre-wrap text-sm font-mono text-blue-600">
                    {detailModal.cards_info}
                  </pre>
                </Card>
                <div className="mt-2 text-center">
                  <Button 
                    type="link" 
                    icon={<DownloadOutlined />}
                    onClick={() => handleDownloadCards(detailModal)}
                  >
                    下载宝贝到本地(TXT)
                  </Button>
                </div>
              </div>
            )}
          </div>
        )}
      </Modal>
    </div>
  )
}
