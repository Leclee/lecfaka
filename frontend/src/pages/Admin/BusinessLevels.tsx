import { useEffect, useState } from 'react'
import {
  Table, Button, Space, Modal, Form, Input, InputNumber,
  message, Popconfirm, Tag, Card, Typography, Switch
} from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined, ReloadOutlined } from '@ant-design/icons'
import * as adminApi from '../../api/admin'

const { Title } = Typography
const { TextArea } = Input

export default function BusinessLevels() {
  const [loading, setLoading] = useState(false)
  const [levels, setLevels] = useState<adminApi.BusinessLevel[]>([])
  const [modalVisible, setModalVisible] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [form] = Form.useForm()

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    setLoading(true)
    try {
      const res = await adminApi.getBusinessLevels()
      setLevels(res.items)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  const handleAdd = () => {
    setEditingId(null)
    form.resetFields()
    form.setFieldsValue({
      price: 0,
      supplier_fee: 0,
      can_supply: true,
      can_substation: true,
      can_bindomain: false,
      max_commodities: 100,
      max_substations: 0,
      sort: 0,
      status: 1,
    })
    setModalVisible(true)
  }

  const handleEdit = (record: adminApi.BusinessLevel) => {
    setEditingId(record.id)
    form.setFieldsValue({
      ...record,
      can_supply: record.can_supply === 1,
      can_substation: record.can_substation === 1,
      can_bindomain: record.can_bindomain === 1,
    })
    setModalVisible(true)
  }

  const handleDelete = async (id: number) => {
    try {
      await adminApi.deleteBusinessLevel(id)
      message.success('删除成功')
      loadData()
    } catch (e: any) {
      message.error(e.message || '删除失败')
    }
  }

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()
      const payload = {
        ...values,
        can_supply: values.can_supply ? 1 : 0,
        can_substation: values.can_substation ? 1 : 0,
        can_bindomain: values.can_bindomain ? 1 : 0,
      }
      
      if (editingId) {
        await adminApi.updateBusinessLevel(editingId, payload)
        message.success('更新成功')
      } else {
        await adminApi.createBusinessLevel(payload)
        message.success('创建成功')
      }
      
      setModalVisible(false)
      loadData()
    } catch (e: any) {
      if (e.errorFields) return
      message.error(e.message || '操作失败')
    }
  }

  const columns = [
    { title: 'ID', dataIndex: 'id', width: 60 },
    {
      title: '等级名称',
      dataIndex: 'name',
      render: (name: string, record: adminApi.BusinessLevel) => (
        <Space>
          {record.icon && <img src={record.icon} alt="" className="w-5 h-5" />}
          <Tag color="gold">{name}</Tag>
        </Space>
      ),
    },
    {
      title: '购买价格',
      dataIndex: 'price',
      render: (v: number) => <span className="text-red-500">¥{v}</span>,
    },
    {
      title: '供货商手续费',
      dataIndex: 'supplier_fee',
      render: (v: number) => `${(v * 100).toFixed(1)}%`,
    },
    {
      title: '供货权限',
      dataIndex: 'can_supply',
      width: 100,
      render: (v: number) => (
        <Tag color={v === 1 ? 'green' : 'default'}>{v === 1 ? 'ON' : 'OFF'}</Tag>
      ),
    },
    {
      title: '分站权限',
      dataIndex: 'can_substation',
      width: 100,
      render: (v: number) => (
        <Tag color={v === 1 ? 'green' : 'default'}>{v === 1 ? 'ON' : 'OFF'}</Tag>
      ),
    },
    {
      title: '绑定独立域名',
      dataIndex: 'can_bindomain',
      width: 120,
      render: (v: number) => (
        <Tag color={v === 1 ? 'green' : 'default'}>{v === 1 ? 'ON' : 'OFF'}</Tag>
      ),
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      render: (_: any, record: adminApi.BusinessLevel) => (
        <Space>
          <Button type="link" icon={<EditOutlined />} onClick={() => handleEdit(record)} />
          <Popconfirm title="确定删除此等级？" onConfirm={() => handleDelete(record.id)}>
            <Button type="link" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <div>
      <Title level={4}>商户等级</Title>

      <Card className="rounded-xl border-0 shadow-sm">
        <div className="flex justify-end mb-4">
          <Space>
            <Button icon={<ReloadOutlined />} onClick={loadData}>刷新</Button>
            <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
              新增等级
            </Button>
          </Space>
        </div>

        <Table
          columns={columns}
          dataSource={levels}
          rowKey="id"
          loading={loading}
          pagination={false}
        />
      </Card>

      <Modal
        title={editingId ? '编辑商户等级' : '新增商户等级'}
        open={modalVisible}
        onOk={handleSubmit}
        onCancel={() => setModalVisible(false)}
        width={600}
      >
        <Form form={form} layout="vertical" className="mt-4">
          <div className="grid grid-cols-2 gap-4">
            <Form.Item
              name="name"
              label="等级名称"
              rules={[{ required: true, message: '请输入等级名称' }]}
            >
              <Input placeholder="如：体验版、普通版、专业版" />
            </Form.Item>
            
            <Form.Item name="price" label="购买价格">
              <InputNumber min={0} precision={2} className="w-full" prefix="¥" />
            </Form.Item>
          </div>
          
          <Form.Item name="icon" label="图标URL">
            <Input placeholder="可选" />
          </Form.Item>
          
          <div className="grid grid-cols-2 gap-4">
            <Form.Item name="supplier_fee" label="供货商手续费比例">
              <InputNumber min={0} max={1} step={0.01} precision={4} className="w-full" />
            </Form.Item>
            
            <Form.Item name="max_commodities" label="最大商品数量">
              <InputNumber min={0} className="w-full" />
            </Form.Item>
          </div>
          
          <div className="grid grid-cols-3 gap-4">
            <Form.Item name="can_supply" label="供货权限" valuePropName="checked">
              <Switch checkedChildren="ON" unCheckedChildren="OFF" />
            </Form.Item>
            
            <Form.Item name="can_substation" label="分站权限" valuePropName="checked">
              <Switch checkedChildren="ON" unCheckedChildren="OFF" />
            </Form.Item>
            
            <Form.Item name="can_bindomain" label="绑定独立域名" valuePropName="checked">
              <Switch checkedChildren="ON" unCheckedChildren="OFF" />
            </Form.Item>
          </div>
          
          <Form.Item name="description" label="描述">
            <TextArea rows={3} placeholder="等级描述" />
          </Form.Item>
          
          <div className="grid grid-cols-2 gap-4">
            <Form.Item name="sort" label="排序">
              <InputNumber min={0} className="w-full" />
            </Form.Item>
            
            <Form.Item name="status" label="状态">
              <InputNumber min={0} max={1} className="w-full" />
            </Form.Item>
          </div>
        </Form>
      </Modal>
    </div>
  )
}
