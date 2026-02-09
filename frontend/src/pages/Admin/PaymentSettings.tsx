import { useEffect, useState } from 'react'
import {
  Table, Button, Space, Modal, Form, Input, InputNumber, Switch, Select,
  Tag, Card, Typography, message, Popconfirm, Tabs
} from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined, SearchOutlined } from '@ant-design/icons'
import * as adminApi from '../../api/admin'

const { Title } = Typography

export default function PaymentSettings() {
  const [loading, setLoading] = useState(false)
  const [data, setData] = useState<adminApi.PaymentConfig[]>([])
  const [plugins, setPlugins] = useState<any[]>([])
  const [modalOpen, setModalOpen] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [selectedRowKeys, setSelectedRowKeys] = useState<number[]>([])
  const [activeTab, setActiveTab] = useState('all')
  const [keyword, setKeyword] = useState('')
  const [form] = Form.useForm()

  const loadData = async () => {
    setLoading(true)
    try {
      const [payRes, pluginRes] = await Promise.all([
        adminApi.getPaymentSettings(),
        adminApi.getPlugins('payment'),
      ])
      setData(payRes.items || [])
      setPlugins(pluginRes.items || [])
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { loadData() }, [])

  const filteredData = data.filter(item => {
    if (activeTab !== 'all' && item.handler !== activeTab) return false
    if (keyword && !item.name.includes(keyword)) return false
    return true
  })

  const handleAdd = () => {
    setEditingId(null)
    form.resetFields()
    form.setFieldsValue({ sort: 0, status: 1, commodity: 1, recharge: 1, cost: 0, cost_type: 0, equipment: 0 })
    setModalOpen(true)
  }

  const handleEdit = (record: adminApi.PaymentConfig) => {
    setEditingId(record.id)
    form.setFieldsValue(record)
    setModalOpen(true)
  }

  const handleDelete = async (id: number) => {
    try {
      await adminApi.deletePaymentSetting(id)
      message.success('删除成功')
      loadData()
    } catch (e: any) {
      message.error(e.message || '删除失败')
    }
  }

  const handleBatchDelete = async () => {
    for (const id of selectedRowKeys) {
      try {
        await adminApi.deletePaymentSetting(id)
      } catch {}
    }
    message.success('批量删除完成')
    setSelectedRowKeys([])
    loadData()
  }

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()
      if (editingId) {
        await adminApi.updatePaymentSetting(editingId, values)
        message.success('更新成功')
      } else {
        await adminApi.createPaymentSetting(values)
        message.success('创建成功')
      }
      setModalOpen(false)
      loadData()
    } catch (e: any) {
      if (e.errorFields) return
      message.error(e.message || '操作失败')
    }
  }

  const handleStatusChange = async (id: number, field: 'commodity' | 'recharge', checked: boolean) => {
    try {
      await adminApi.updatePaymentSetting(id, { [field]: checked ? 1 : 0 })
      message.success('已更新')
      loadData()
    } catch (e: any) {
      message.error(e.message || '操作失败')
    }
  }

  // 动态 tab：按支付插件分组
  const handlerTabs = [
    { key: 'all', label: '全部' },
    ...Array.from(new Set(data.map(d => d.handler))).filter(h => h !== '#balance').map(h => ({
      key: h,
      label: plugins.find(p => p.id === h)?.name || h,
    })),
  ]

  const channelTagColor: Record<string, string> = {
    alipay: 'blue', wxpay: 'green', qqpay: 'purple', 'TRC20-USDT': 'orange',
  }

  const columns = [
    {
      title: '支付名称',
      key: 'name',
      width: 140,
      render: (_: any, r: adminApi.PaymentConfig) => (
        <div className="flex items-center gap-2">
          {r.icon && <img src={r.icon} alt="" className="w-6 h-6 rounded" />}
          <span className="font-medium">{r.name}</span>
        </div>
      ),
    },
    {
      title: '所属插件',
      dataIndex: 'handler',
      width: 100,
      render: (h: string) => {
        if (h === '#balance') return <Tag>余额</Tag>
        return <Tag color="blue">{plugins.find(p => p.id === h)?.name || h}</Tag>
      },
    },
    {
      title: '手续费',
      key: 'cost',
      width: 90,
      render: (_: any, r: adminApi.PaymentConfig) =>
        r.cost > 0 ? (r.cost_type === 0 ? `¥${r.cost}` : `${(r.cost * 100).toFixed(1)}%`) : '-',
    },
    {
      title: '支付方式',
      dataIndex: 'code',
      width: 100,
      render: (code: string) => code ? <Tag color={channelTagColor[code] || 'default'}>{code}</Tag> : '-',
    },
    {
      title: '商品下单',
      dataIndex: 'commodity',
      width: 90,
      render: (v: number, r: adminApi.PaymentConfig) => (
        <Switch checked={v === 1} size="small" onChange={c => handleStatusChange(r.id, 'commodity', c)} checkedChildren="通用" unCheckedChildren="关闭" />
      ),
    },
    {
      title: '余额充值',
      dataIndex: 'recharge',
      width: 90,
      render: (v: number, r: adminApi.PaymentConfig) => (
        <Switch checked={v === 1} size="small" onChange={c => handleStatusChange(r.id, 'recharge', c)} checkedChildren="通用" unCheckedChildren="关闭" />
      ),
    },
    {
      title: '排序',
      dataIndex: 'sort',
      width: 70,
      sorter: (a: adminApi.PaymentConfig, b: adminApi.PaymentConfig) => a.sort - b.sort,
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      render: (_: any, r: adminApi.PaymentConfig) => (
        <Space size={4}>
          <Button type="text" size="small" icon={<EditOutlined />} onClick={() => handleEdit(r)} />
          <Popconfirm title="确定删除？" onConfirm={() => handleDelete(r.id)}>
            <Button type="text" size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <div>
      <Title level={4}>支付设置</Title>
      <Card className="rounded-xl border-0 shadow-sm">
        <div className="flex flex-wrap gap-2 mb-4">
          <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>添加支付</Button>
          <Popconfirm title={`确定删除 ${selectedRowKeys.length} 个支付？`} onConfirm={handleBatchDelete} disabled={selectedRowKeys.length === 0}>
            <Button danger icon={<DeleteOutlined />} disabled={selectedRowKeys.length === 0}>移除选中支付</Button>
          </Popconfirm>
        </div>
        <div className="flex gap-2 mb-4">
          <Input placeholder="支付名称" value={keyword} onChange={e => setKeyword(e.target.value)} allowClear style={{ width: 180 }} />
          <Button icon={<SearchOutlined />} onClick={() => {}}>查询</Button>
        </div>
        <Tabs activeKey={activeTab} onChange={setActiveTab} items={handlerTabs} className="!mb-2" />
        <Table
          rowKey="id" loading={loading} dataSource={filteredData} columns={columns} pagination={false} size="middle"
          rowSelection={{ selectedRowKeys, onChange: keys => setSelectedRowKeys(keys as number[]) }}
        />
      </Card>

      <Modal
        title={editingId ? '编辑支付' : '添加支付'}
        open={modalOpen} onOk={handleSubmit} onCancel={() => setModalOpen(false)}
        okText="保存" destroyOnClose width={560}
      >
        <Form form={form} layout="vertical" className="mt-4">
          <Form.Item name="name" label="支付名称" rules={[{ required: true }]}>
            <Input placeholder="如: 支付宝" />
          </Form.Item>
          <Form.Item name="handler" label="所属插件" rules={[{ required: true }]}>
            <Select placeholder="选择支付插件">
              <Select.Option value="#balance">余额支付</Select.Option>
              {plugins.map(p => (
                <Select.Option key={p.id} value={p.id}>{p.name}</Select.Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item name="code" label="支付通道">
            <Input placeholder="如: alipay / wxpay / qqpay" />
          </Form.Item>
          <Form.Item name="icon" label="图标URL">
            <Input placeholder="支付方式图标" />
          </Form.Item>
          <div className="grid grid-cols-2 gap-4">
            <Form.Item name="cost" label="手续费"><InputNumber min={0} className="w-full" /></Form.Item>
            <Form.Item name="cost_type" label="手续费类型">
              <Select>
                <Select.Option value={0}>固定金额</Select.Option>
                <Select.Option value={1}>百分比</Select.Option>
              </Select>
            </Form.Item>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <Form.Item name="commodity" label="商品下单" valuePropName="checked" getValueFromEvent={(v: boolean) => v ? 1 : 0} getValueProps={(v: number) => ({ checked: v === 1 })}>
              <Switch checkedChildren="启用" unCheckedChildren="禁用" />
            </Form.Item>
            <Form.Item name="recharge" label="余额充值" valuePropName="checked" getValueFromEvent={(v: boolean) => v ? 1 : 0} getValueProps={(v: number) => ({ checked: v === 1 })}>
              <Switch checkedChildren="启用" unCheckedChildren="禁用" />
            </Form.Item>
          </div>
          <Form.Item name="sort" label="排序"><InputNumber min={0} className="w-full" /></Form.Item>
          <Form.Item name="status" label="状态" valuePropName="checked" getValueFromEvent={(v: boolean) => v ? 1 : 0} getValueProps={(v: number) => ({ checked: v === 1 })}>
            <Switch checkedChildren="启用" unCheckedChildren="禁用" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
