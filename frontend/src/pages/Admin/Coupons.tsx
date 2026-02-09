import { useEffect, useState } from 'react'
import {
  Table, Button, Modal, Form, Input, InputNumber, Select,
  message, Popconfirm, Tag, Card, Typography, Row, Col, Statistic
} from 'antd'
import { 
  PlusOutlined, DeleteOutlined, ReloadOutlined, 
  LockOutlined, UnlockOutlined, ExportOutlined 
} from '@ant-design/icons'
import * as adminApi from '../../api/admin'

const { Title, Text } = Typography

export default function Coupons() {
  const [loading, setLoading] = useState(false)
  const [coupons, setCoupons] = useState<adminApi.Coupon[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [filters, setFilters] = useState<{ status?: number; code?: string }>({})
  const [stats, setStats] = useState({ total: 0, available: 0, expired: 0, locked: 0 })
  const [selectedRowKeys, setSelectedRowKeys] = useState<number[]>([])
  const [categories, setCategories] = useState<adminApi.Category[]>([])
  const [commodities, setCommodities] = useState<adminApi.Commodity[]>([])

  // 生成优惠券弹窗
  const [createVisible, setCreateVisible] = useState(false)
  const [createForm] = Form.useForm()

  useEffect(() => {
    loadData()
    loadStats()
    loadCategories()
    loadCommodities()
  }, [page, filters])

  const loadData = async () => {
    setLoading(true)
    try {
      const res = await adminApi.getCoupons({ ...filters, page, limit: 20 })
      setCoupons(res.items)
      setTotal(res.total)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  const loadStats = async () => {
    try {
      const res = await adminApi.getCouponStats()
      setStats(res)
    } catch (e) {
      console.error(e)
    }
  }

  const loadCategories = async () => {
    try {
      const res = await adminApi.getCategories()
      setCategories(res.items)
    } catch (e) {
      console.error(e)
    }
  }

  const loadCommodities = async () => {
    try {
      const res = await adminApi.getCommodities({ limit: 100 })
      setCommodities(res.items)
    } catch (e) {
      console.error(e)
    }
  }

  const handleCreate = async () => {
    try {
      const values = await createForm.validateFields()
      const res = await adminApi.createCoupons(values)
      message.success(`成功生成 ${res.count} 张优惠券`)
      setCreateVisible(false)
      createForm.resetFields()
      loadData()
      loadStats()
    } catch (e: any) {
      if (e.errorFields) return
      message.error(e.message || '操作失败')
    }
  }

  const handleDelete = async (id: number) => {
    try {
      await adminApi.deleteCoupon(id)
      message.success('删除成功')
      loadData()
      loadStats()
    } catch (e: any) {
      message.error(e.message || '删除失败')
    }
  }

  const handleBatch = async (action: 'delete' | 'lock' | 'unlock') => {
    if (selectedRowKeys.length === 0) {
      message.warning('请先选择优惠券')
      return
    }
    try {
      await adminApi.batchCoupons(selectedRowKeys, action)
      message.success('操作成功')
      setSelectedRowKeys([])
      loadData()
      loadStats()
    } catch (e: any) {
      message.error(e.message || '操作失败')
    }
  }

  const handleExport = async () => {
    if (selectedRowKeys.length === 0) {
      message.warning('请先选择优惠券')
      return
    }
    try {
      const res = await adminApi.exportCoupons(selectedRowKeys)
      const text = res.items.map(c => c.code).join('\n')
      navigator.clipboard.writeText(text)
      message.success(`已复制 ${res.items.length} 张优惠券码到剪贴板`)
    } catch (e: any) {
      message.error(e.message || '导出失败')
    }
  }

  const getStatusTag = (status: number) => {
    const map: Record<number, { color: string; text: string }> = {
      0: { color: 'green', text: '正常使用' },
      1: { color: 'default', text: '已失效' },
      2: { color: 'orange', text: '已锁定' },
    }
    const item = map[status] || { color: 'default', text: '未知' }
    return <Tag color={item.color}>{item.text}</Tag>
  }

  const columns = [
    {
      title: '券代码',
      dataIndex: 'code',
      width: 200,
      render: (v: string) => <Text copyable={{ text: v }}>{v}</Text>,
    },
    {
      title: '抵扣模式',
      dataIndex: 'mode',
      width: 100,
      render: (v: number) => <Tag color={v === 0 ? 'blue' : 'purple'}>{v === 0 ? '金额' : '按件'}</Tag>,
    },
    {
      title: '面值',
      dataIndex: 'money',
      width: 100,
      render: (v: number) => <span className="text-red-500">¥{v}</span>,
    },
    {
      title: '抵扣商品',
      key: 'scope',
      width: 180,
      render: (_: any, record: adminApi.Coupon) => {
        if (record.commodity_name) {
          return <Tag color="cyan">[商品分类] -&gt; {record.commodity_name}</Tag>
        }
        if (record.category_name) {
          return <Tag color="cyan">[商品分类] -&gt; {record.category_name}</Tag>
        }
        return <Tag>全部商品</Tag>
      },
    },
    {
      title: '到期时间',
      dataIndex: 'expires_at',
      width: 120,
      render: (v: string) => v ? v.split('T')[0] : '永久',
    },
    {
      title: '剩余次数',
      dataIndex: 'life',
      width: 100,
      render: (life: number, record: adminApi.Coupon) => `${life - record.use_life}`,
    },
    {
      title: '已使用次数',
      dataIndex: 'use_life',
      width: 100,
    },
    {
      title: '备注信息',
      dataIndex: 'remark',
      width: 150,
      ellipsis: true,
      render: (v: string) => v || '-',
    },
    {
      title: '状态',
      dataIndex: 'status',
      width: 100,
      render: (status: number) => getStatusTag(status),
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      render: (_: any, record: adminApi.Coupon) => (
        <Popconfirm title="确定删除此优惠券？" onConfirm={() => handleDelete(record.id)}>
          <Button type="link" danger icon={<DeleteOutlined />} size="small" />
        </Popconfirm>
      ),
    },
  ]

  const rowSelection = {
    selectedRowKeys,
    onChange: (keys: React.Key[]) => setSelectedRowKeys(keys as number[]),
  }

  return (
    <div>
      <Title level={4}>优惠券</Title>

      {/* 统计卡片 */}
      <Row gutter={16} className="mb-6">
        <Col span={6}>
          <Card className="rounded-xl border-0 shadow-sm">
            <Statistic title="全部" value={stats.total} />
          </Card>
        </Col>
        <Col span={6}>
          <Card className="rounded-xl border-0 shadow-sm">
            <Statistic title="正常使用" value={stats.available} valueStyle={{ color: '#52c41a' }} />
          </Card>
        </Col>
        <Col span={6}>
          <Card className="rounded-xl border-0 shadow-sm">
            <Statistic title="已失效" value={stats.expired} valueStyle={{ color: '#999' }} />
          </Card>
        </Col>
        <Col span={6}>
          <Card className="rounded-xl border-0 shadow-sm">
            <Statistic title="已锁定" value={stats.locked} valueStyle={{ color: '#fa8c16' }} />
          </Card>
        </Col>
      </Row>

      <Card className="rounded-xl border-0 shadow-sm">
        {/* 操作栏 */}
        <div className="flex flex-wrap gap-2 mb-4">
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateVisible(true)}>
            生成优惠券
          </Button>
          <Button danger icon={<DeleteOutlined />} onClick={() => handleBatch('delete')}>
            移除选中优惠券
          </Button>
          <Button icon={<LockOutlined />} onClick={() => handleBatch('lock')}>
            锁定选中优惠券
          </Button>
          <Button icon={<UnlockOutlined />} onClick={() => handleBatch('unlock')}>
            解锁选中优惠券
          </Button>
          <Button icon={<ExportOutlined />} onClick={handleExport}>
            导出所选优惠券
          </Button>
        </div>

        {/* 筛选栏 */}
        <div className="flex gap-4 mb-4">
          <Input.Search
            placeholder="券代码"
            allowClear
            onSearch={(v) => {
              setFilters({ ...filters, code: v })
              setPage(1)
            }}
            style={{ width: 200 }}
          />
          <Select
            placeholder="商品分类"
            allowClear
            style={{ width: 150 }}
            options={categories.map(c => ({ value: c.id, label: c.name }))}
            onChange={() => {
              setFilters({ ...filters })
              setPage(1)
            }}
          />
          <Button icon={<ReloadOutlined />} onClick={loadData}>刷新</Button>
        </div>

        {/* 状态Tab */}
        <div className="flex gap-2 mb-4">
          <Button 
            type={filters.status === undefined ? 'primary' : 'default'}
            onClick={() => { setFilters({}); setPage(1) }}
          >
            全部
          </Button>
          <Button 
            type={filters.status === 0 ? 'primary' : 'default'}
            onClick={() => { setFilters({ ...filters, status: 0 }); setPage(1) }}
          >
            正常使用
          </Button>
          <Button 
            type={filters.status === 1 ? 'primary' : 'default'}
            onClick={() => { setFilters({ ...filters, status: 1 }); setPage(1) }}
          >
            已失效
          </Button>
          <Button 
            type={filters.status === 2 ? 'primary' : 'default'}
            onClick={() => { setFilters({ ...filters, status: 2 }); setPage(1) }}
          >
            已锁定
          </Button>
        </div>

        <Table
          columns={columns}
          dataSource={coupons}
          rowKey="id"
          loading={loading}
          rowSelection={rowSelection}
          pagination={{
            current: page,
            total,
            pageSize: 20,
            onChange: setPage,
            showTotal: (t) => `共 ${t} 条`,
          }}
          scroll={{ x: 1200 }}
        />
      </Card>

      {/* 生成优惠券弹窗 */}
      <Modal
        title="生成优惠券"
        open={createVisible}
        onOk={handleCreate}
        onCancel={() => setCreateVisible(false)}
        width={500}
      >
        <Form form={createForm} layout="vertical" className="mt-4">
          <div className="grid grid-cols-2 gap-4">
            <Form.Item
              name="count"
              label="生成数量"
              initialValue={1}
              rules={[{ required: true }]}
            >
              <InputNumber min={1} max={100} className="w-full" />
            </Form.Item>
            
            <Form.Item
              name="money"
              label="面值"
              rules={[{ required: true, message: '请输入面值' }]}
            >
              <InputNumber min={0.01} precision={2} prefix="¥" className="w-full" />
            </Form.Item>
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <Form.Item name="mode" label="抵扣模式" initialValue={0}>
              <Select>
                <Select.Option value={0}>金额</Select.Option>
                <Select.Option value={1}>按件</Select.Option>
              </Select>
            </Form.Item>
            
            <Form.Item name="life" label="可用次数" initialValue={1}>
              <InputNumber min={1} className="w-full" />
            </Form.Item>
          </div>
          
          <Form.Item name="commodity_id" label="限制商品">
            <Select allowClear placeholder="不限制">
              {commodities.map(c => (
                <Select.Option key={c.id} value={c.id}>{c.name}</Select.Option>
              ))}
            </Select>
          </Form.Item>
          
          <Form.Item name="category_id" label="限制分类">
            <Select allowClear placeholder="不限制">
              {categories.map(c => (
                <Select.Option key={c.id} value={c.id}>{c.name}</Select.Option>
              ))}
            </Select>
          </Form.Item>
          
          <Form.Item name="expires_days" label="有效天数">
            <InputNumber min={1} className="w-full" placeholder="留空表示永久" />
          </Form.Item>
          
          <Form.Item name="remark" label="备注">
            <Input placeholder="可选" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
