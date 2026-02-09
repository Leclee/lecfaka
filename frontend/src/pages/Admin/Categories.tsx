import { useEffect, useState } from 'react'
import { 
  Table, Button, Space, Modal, Form, Input, InputNumber, Switch, 
  message, Popconfirm, Card, Typography 
} from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons'
import * as adminApi from '../../api/admin'

const { Title } = Typography

interface Category {
  id: number
  name: string
  icon?: string
  description?: string
  sort: number
  status: number
}

export default function Categories() {
  const [loading, setLoading] = useState(false)
  const [data, setData] = useState<Category[]>([])
  const [modalOpen, setModalOpen] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [form] = Form.useForm()

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    setLoading(true)
    try {
      const res = await adminApi.getCategories()
      setData(res.items || [])
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  const handleAdd = () => {
    setEditingId(null)
    form.resetFields()
    form.setFieldsValue({ sort: 0, status: true })
    setModalOpen(true)
  }

  const handleEdit = (record: Category) => {
    setEditingId(record.id)
    form.setFieldsValue({
      ...record,
      status: record.status === 1,
    })
    setModalOpen(true)
  }

  const handleDelete = async (id: number) => {
    try {
      await adminApi.deleteCategory(id)
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
        status: values.status ? 1 : 0,
      }

      if (editingId) {
        await adminApi.updateCategory(editingId, payload)
        message.success('更新成功')
      } else {
        await adminApi.createCategory(payload)
        message.success('创建成功')
      }
      
      setModalOpen(false)
      loadData()
    } catch (e: any) {
      if (e.errorFields) return
      message.error(e.message || '操作失败')
    }
  }

  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      width: 80,
    },
    {
      title: '图标',
      dataIndex: 'icon',
      width: 80,
      render: (icon: string) => icon ? <img src={icon} alt="" className="w-8 h-8" /> : '-',
    },
    {
      title: '分类名称',
      dataIndex: 'name',
    },
    {
      title: '描述',
      dataIndex: 'description',
      ellipsis: true,
    },
    {
      title: '排序',
      dataIndex: 'sort',
      width: 80,
    },
    {
      title: '状态',
      dataIndex: 'status',
      width: 100,
      render: (status: number) => (
        <span className={status === 1 ? 'text-green-500' : 'text-gray-400'}>
          {status === 1 ? '显示' : '隐藏'}
        </span>
      ),
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      render: (_: any, record: Category) => (
        <Space>
          <Button 
            type="link" 
            size="small" 
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          >
            编辑
          </Button>
          <Popconfirm
            title="确定删除此分类？"
            onConfirm={() => handleDelete(record.id)}
          >
            <Button type="link" size="small" danger icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <Title level={4} className="!mb-0">分类管理</Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
          添加分类
        </Button>
      </div>

      <Card className="rounded-xl border-0 shadow-sm">
        <Table
          rowKey="id"
          loading={loading}
          dataSource={data}
          columns={columns}
          pagination={false}
        />
      </Card>

      <Modal
        title={editingId ? '编辑分类' : '添加分类'}
        open={modalOpen}
        onOk={handleSubmit}
        onCancel={() => setModalOpen(false)}
        destroyOnClose
      >
        <Form form={form} layout="vertical" className="mt-4">
          <Form.Item
            name="name"
            label="分类名称"
            rules={[{ required: true, message: '请输入分类名称' }]}
          >
            <Input placeholder="请输入分类名称" />
          </Form.Item>

          <Form.Item name="icon" label="图标URL">
            <Input placeholder="请输入图标URL" />
          </Form.Item>

          <Form.Item name="description" label="描述">
            <Input.TextArea placeholder="请输入描述" rows={3} />
          </Form.Item>

          <Form.Item name="sort" label="排序">
            <InputNumber min={0} className="w-full" />
          </Form.Item>

          <Form.Item name="status" label="状态" valuePropName="checked">
            <Switch checkedChildren="显示" unCheckedChildren="隐藏" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
