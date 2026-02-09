import { useEffect, useState } from 'react'
import {
  Table, Button, Space, Modal, Form, Input, InputNumber,
  Select, message, Popconfirm, Tag, Card, Typography, Tabs,
  DatePicker, Row, Col
} from 'antd'
import {
  DeleteOutlined, UploadOutlined,
  LockOutlined, UnlockOutlined, ExportOutlined, SearchOutlined,
  CheckCircleOutlined
} from '@ant-design/icons'
import * as adminApi from '../../api/admin'
import dayjs from 'dayjs'

const { Title, Text, Paragraph } = Typography
const { TextArea } = Input
const { RangePicker } = DatePicker

interface CardFilters {
  commodity_id?: number
  status?: number
  secret?: string
  secret_fuzzy?: string
  note?: string
  owner_id?: number
  race?: string
  start_time?: string
  end_time?: string
}

export default function Cards() {
  const [loading, setLoading] = useState(false)
  const [cards, setCards] = useState<adminApi.Card[]>([])
  const [commodities, setCommodities] = useState<adminApi.Commodity[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [activeTab, setActiveTab] = useState('all')
  const [filters, setFilters] = useState<CardFilters>({})
  const [searchForm] = Form.useForm()

  // 导入弹窗
  const [importModalVisible, setImportModalVisible] = useState(false)
  const [importForm] = Form.useForm()
  const [importing, setImporting] = useState(false)

  // 选中的卡密
  const [selectedRowKeys, setSelectedRowKeys] = useState<number[]>([])

  useEffect(() => {
    loadCommodities()
  }, [])

  useEffect(() => {
    loadCards()
  }, [page, pageSize, activeTab, filters])

  const loadCommodities = async () => {
    try {
      const res = await adminApi.getCommodities({ limit: 100 })
      setCommodities(res.items)
    } catch (e) {
      console.error(e)
    }
  }

  const loadCards = async () => {
    setLoading(true)
    try {
      // 根据 tab 设置状态筛选
      let statusFilter: number | undefined = filters.status
      if (activeTab === 'unsold') statusFilter = 0
      else if (activeTab === 'sold') statusFilter = 1
      else if (activeTab === 'locked') statusFilter = 2

      const res = await adminApi.getCards({
        ...filters,
        status: statusFilter,
        page,
        limit: pageSize,
      })
      setCards(res.items)
      setTotal(res.total)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = () => {
    const values = searchForm.getFieldsValue()
    const newFilters: CardFilters = {}
    
    if (values.secret) newFilters.secret = values.secret
    if (values.secret_fuzzy) newFilters.secret_fuzzy = values.secret_fuzzy
    if (values.note) newFilters.note = values.note
    if (values.owner_id !== undefined && values.owner_id !== '') {
      newFilters.owner_id = Number(values.owner_id)
    }
    if (values.commodity_id) newFilters.commodity_id = values.commodity_id
    if (values.dateRange && values.dateRange.length === 2) {
      newFilters.start_time = values.dateRange[0].format('YYYY-MM-DD')
      newFilters.end_time = values.dateRange[1].format('YYYY-MM-DD')
    }
    
    setFilters(newFilters)
    setPage(1)
  }

  const handleReset = () => {
    searchForm.resetFields()
    setFilters({})
    setPage(1)
  }

  const handleImport = async () => {
    try {
      const values = await importForm.validateFields()
      setImporting(true)
      const res = await adminApi.importCards(values)
      message.success(res.message || `成功导入 ${res.count} 条卡密`)
      setImportModalVisible(false)
      importForm.resetFields()
      loadCards()
    } catch (e) {
      console.error(e)
    } finally {
      setImporting(false)
    }
  }

  const handleDelete = async (id: number) => {
    try {
      await adminApi.deleteCard(id)
      message.success('删除成功')
      loadCards()
    } catch (e) {
      console.error(e)
    }
  }

  const handleBatchDelete = async () => {
    if (selectedRowKeys.length === 0) {
      message.warning('请选择要删除的卡密')
      return
    }

    try {
      const res = await adminApi.batchDeleteCards(selectedRowKeys)
      message.success(`成功删除 ${res.count} 条卡密`)
      setSelectedRowKeys([])
      loadCards()
    } catch (e) {
      console.error(e)
    }
  }

  const handleBatchLock = async () => {
    if (selectedRowKeys.length === 0) {
      message.warning('请选择要锁定的卡密')
      return
    }
    try {
      await adminApi.batchUpdateCardsStatus(selectedRowKeys, 2)
      message.success('锁定成功')
      setSelectedRowKeys([])
      loadCards()
    } catch (e) {
      console.error(e)
    }
  }

  const handleBatchUnlock = async () => {
    if (selectedRowKeys.length === 0) {
      message.warning('请选择要解锁的卡密')
      return
    }
    try {
      await adminApi.batchUpdateCardsStatus(selectedRowKeys, 0)
      message.success('解锁成功')
      setSelectedRowKeys([])
      loadCards()
    } catch (e) {
      console.error(e)
    }
  }

  const handleBatchMarkSold = async () => {
    if (selectedRowKeys.length === 0) {
      message.warning('请选择要标记的卡密')
      return
    }
    try {
      await adminApi.batchUpdateCardsStatus(selectedRowKeys, 1)
      message.success('标记为已出售成功')
      setSelectedRowKeys([])
      loadCards()
    } catch (e) {
      console.error(e)
    }
  }

  const handleExport = async () => {
    message.info('导出功能开发中...')
  }

  const columns = [
    {
      title: '卡密信息',
      dataIndex: 'secret',
      key: 'secret',
      width: 300,
      render: (text: string) => (
        <Paragraph
          copyable={{ text }}
          className="font-mono text-sm !mb-0"
          ellipsis={{ rows: 2 }}
        >
          {text}
        </Paragraph>
      ),
    },
    {
      title: '预告内容',
      dataIndex: 'draft',
      key: 'draft',
      width: 120,
      render: (text: string) => text || '-',
    },
    {
      title: '预选加价',
      dataIndex: 'draft_premium',
      key: 'draft_premium',
      width: 90,
      render: (val: number) => val > 0 ? `¥${val}` : '-',
    },
    {
      title: '商品',
      dataIndex: 'commodity_name',
      key: 'commodity_name',
      width: 180,
      render: (text: string, record: adminApi.Card) => (
        <div className="flex items-center gap-2">
          {record.commodity_cover && (
            <img src={record.commodity_cover} alt="" className="w-8 h-8 rounded object-cover" />
          )}
          <span className="truncate">{text}</span>
        </div>
      ),
    },
    {
      title: '类别',
      dataIndex: 'race',
      key: 'race',
      width: 100,
      render: (text: string) => text || '-',
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 170,
      render: (text: string) => text ? dayjs(text).format('YYYY-MM-DD HH:mm:ss') : '-',
    },
    {
      title: '备注信息',
      dataIndex: 'note',
      key: 'note',
      width: 120,
      render: (text: string) => text || '-',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 80,
      render: (status: number) => {
        const map: Record<number, { color: string; text: string }> = {
          0: { color: 'green', text: '未出售' },
          1: { color: 'red', text: '已出售' },
          2: { color: 'orange', text: '已锁定' },
        }
        const item = map[status] || { color: 'default', text: '未知' }
        return <Tag color={item.color}>{item.text}</Tag>
      },
    },
    {
      title: '出售时间',
      dataIndex: 'sold_at',
      key: 'sold_at',
      width: 170,
      render: (text: string) => text ? dayjs(text).format('YYYY-MM-DD HH:mm:ss') : '-',
    },
    {
      title: '订单号',
      dataIndex: 'order_trade_no',
      key: 'order_trade_no',
      width: 180,
      render: (text: string) => text || '-',
    },
    {
      title: 'SKU',
      dataIndex: 'sku',
      key: 'sku',
      width: 100,
      render: (text: string) => text || '-',
    },
    {
      title: '操作',
      key: 'action',
      width: 80,
      fixed: 'right' as const,
      render: (_: any, record: adminApi.Card) => (
        <Space>
          {record.status === 0 && (
            <Popconfirm
              title="确定删除该卡密？"
              onConfirm={() => handleDelete(record.id)}
            >
              <Button type="link" danger size="small">
                删除
              </Button>
            </Popconfirm>
          )}
        </Space>
      ),
    },
  ]

  const tabItems = [
    { key: 'all', label: '全部' },
    { key: 'unsold', label: '未出售' },
    { key: 'sold', label: '已出售' },
    { key: 'locked', label: '已锁定' },
  ]

  return (
    <div>
      <Title level={4} className="flex items-center gap-2">
        卡密管理
        <Text type="secondary" className="text-sm font-normal">(OwO)</Text>
      </Title>

      <Card className="mb-4">
        {/* 工具栏 */}
        <div className="flex flex-wrap gap-2 mb-4 pb-4 border-b">
          <Button
            type="primary"
            icon={<UploadOutlined />}
            onClick={() => setImportModalVisible(true)}
            className="bg-green-500 hover:bg-green-600 border-green-500"
          >
            上传卡密
          </Button>
          <Popconfirm
            title={`确定删除选中的 ${selectedRowKeys.length} 条卡密？`}
            onConfirm={handleBatchDelete}
            disabled={selectedRowKeys.length === 0}
          >
            <Button
              danger
              icon={<DeleteOutlined />}
              disabled={selectedRowKeys.length === 0}
            >
              移除选中卡密
            </Button>
          </Popconfirm>
          <Popconfirm
            title={`确定锁定选中的 ${selectedRowKeys.length} 条卡密？`}
            onConfirm={handleBatchLock}
            disabled={selectedRowKeys.length === 0}
          >
            <Button
              icon={<LockOutlined />}
              disabled={selectedRowKeys.length === 0}
            >
              锁定选中卡密
            </Button>
          </Popconfirm>
          <Popconfirm
            title={`确定解锁选中的 ${selectedRowKeys.length} 条卡密？`}
            onConfirm={handleBatchUnlock}
            disabled={selectedRowKeys.length === 0}
          >
            <Button
              icon={<UnlockOutlined />}
              disabled={selectedRowKeys.length === 0}
              className="bg-green-50 border-green-300 text-green-600 hover:bg-green-100"
            >
              解锁选中卡密
            </Button>
          </Popconfirm>
          <Popconfirm
            title={`确定将选中的 ${selectedRowKeys.length} 条卡密标记为已出售？`}
            onConfirm={handleBatchMarkSold}
            disabled={selectedRowKeys.length === 0}
          >
            <Button
              icon={<CheckCircleOutlined />}
              disabled={selectedRowKeys.length === 0}
              className="bg-blue-50 border-blue-300 text-blue-600 hover:bg-blue-100"
            >
              将卡密更改为已出售
            </Button>
          </Popconfirm>
          <Button
            icon={<ExportOutlined />}
            onClick={handleExport}
            className="bg-cyan-50 border-cyan-300 text-cyan-600 hover:bg-cyan-100"
          >
            导出筛选卡密
          </Button>
        </div>

        {/* 搜索表单 */}
        <Form form={searchForm} layout="vertical" className="mb-4">
          <Row gutter={16}>
            <Col xs={24} sm={12} md={8} lg={6}>
              <Form.Item name="secret" label="卡密信息(精确搜索,速度快)">
                <Input placeholder="精确搜索卡密" />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12} md={8} lg={6}>
              <Form.Item name="secret_fuzzy" label="卡密信息(模糊搜索,速度慢)">
                <Input placeholder="模糊搜索卡密" />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12} md={8} lg={6}>
              <Form.Item name="note" label="备注信息">
                <Input placeholder="搜索备注" />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12} md={8} lg={6}>
              <Form.Item name="owner_id" label="卡密所属会员ID，0=系统">
                <Input placeholder="会员ID" type="number" />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12} md={8} lg={6}>
              <Form.Item name="dateRange" label="入库时间范围">
                <RangePicker className="w-full" />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12} md={8} lg={6}>
              <Form.Item name="commodity_id" label="查询商品">
                <Select
                  placeholder="选择商品"
                  allowClear
                  showSearch
                  optionFilterProp="children"
                >
                  {commodities.map((c) => (
                    <Select.Option key={c.id} value={c.id}>{c.name}</Select.Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
          </Row>
          <Row>
            <Col>
              <Space>
                <Button type="primary" icon={<SearchOutlined />} onClick={handleSearch}>
                  查询
                </Button>
                <Button onClick={handleReset}>
                  重置
                </Button>
              </Space>
            </Col>
          </Row>
        </Form>

        {/* Tab 标签 */}
        <Tabs
          activeKey={activeTab}
          onChange={(key) => {
            setActiveTab(key)
            setPage(1)
          }}
          items={tabItems}
          className="mb-4"
        />

        {/* 表格 */}
        <Table
          columns={columns}
          dataSource={cards}
          rowKey="id"
          loading={loading}
          scroll={{ x: 1600 }}
          rowSelection={{
            selectedRowKeys,
            onChange: (keys) => setSelectedRowKeys(keys as number[]),
            getCheckboxProps: (record) => ({
              disabled: record.status === 1, // 已售出的不能选择
            }),
          }}
          pagination={{
            current: page,
            total,
            pageSize,
            onChange: (p, ps) => {
              setPage(p)
              if (ps) setPageSize(ps)
            },
            showSizeChanger: true,
            showTotal: (t) => `共 ${t} 条`,
            pageSizeOptions: ['10', '20', '50', '100'],
          }}
        />
      </Card>

      {/* 导入卡密弹窗 */}
      <Modal
        title="批量导入卡密"
        open={importModalVisible}
        onOk={handleImport}
        onCancel={() => setImportModalVisible(false)}
        confirmLoading={importing}
        width={700}
      >
        <Form form={importForm} layout="vertical">
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="commodity_id"
                label="选择商品"
                rules={[{ required: true, message: '请选择商品' }]}
              >
                <Select
                  placeholder="选择要导入卡密的商品"
                  showSearch
                  optionFilterProp="children"
                >
                  {commodities.map((c) => (
                    <Select.Option key={c.id} value={c.id}>{c.name}</Select.Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="race" label="商品种类（对应商品配置中的[category]）">
                <Input placeholder="如：月卡、年卡" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="draft" label="预选信息（开启预选后展示给用户）">
                <Input placeholder="预选信息" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="draft_premium" label="预选加价">
                <InputNumber
                  placeholder="0"
                  min={0}
                  precision={2}
                  className="w-full"
                  addonAfter="元"
                />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item name="note" label="备注信息">
            <Input placeholder="可选备注" />
          </Form.Item>

          <Form.Item
            name="cards"
            label="卡密内容"
            rules={[{ required: true, message: '请输入卡密内容' }]}
            extra="每行一个卡密，自动去重。支持格式：单行卡密 或 卡密----预选信息（用四个短横线分隔）"
          >
            <TextArea
              rows={12}
              placeholder={`每行一个卡密，例如：
ABCD-1234-5678
EFGH-9012-3456

或带预选信息：
account@email.com----mypassword----AccountID123
key-abc-123----有效期至2025年`}
            />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
