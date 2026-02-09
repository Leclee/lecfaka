import { useEffect, useState } from 'react'
import {
  Table, Button, Space, Modal, Form, Input, InputNumber,
  message, Popconfirm, Tag, Card, Typography
} from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined, ReloadOutlined } from '@ant-design/icons'
import * as adminApi from '../../api/admin'

const { Title } = Typography

export default function UserGroups() {
  const [loading, setLoading] = useState(false)
  const [groups, setGroups] = useState<adminApi.UserGroup[]>([])
  const [modalVisible, setModalVisible] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [form] = Form.useForm()

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    setLoading(true)
    try {
      const res = await adminApi.getUserGroups()
      setGroups(res.items)
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
      min_recharge: 0,
      discount: 0,
      sort: 0,
      status: 1,
    })
    setModalVisible(true)
  }

  const handleEdit = (record: adminApi.UserGroup) => {
    setEditingId(record.id)
    form.setFieldsValue(record)
    setModalVisible(true)
  }

  const handleDelete = async (id: number) => {
    try {
      await adminApi.deleteUserGroup(id)
      message.success('删除成功')
      loadData()
    } catch (e: any) {
      message.error(e.message || '删除失败')
    }
  }

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()
      
      if (editingId) {
        await adminApi.updateUserGroup(editingId, values)
        message.success('更新成功')
      } else {
        await adminApi.createUserGroup(values)
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
    { title: 'ID', dataIndex: 'id', width: 80 },
    {
      title: '等级名称',
      dataIndex: 'name',
      render: (name: string, record: adminApi.UserGroup) => (
        <Tag color={record.color || 'blue'}>{name}</Tag>
      ),
    },
    {
      title: '最低充值',
      dataIndex: 'min_recharge',
      render: (v: number) => `¥${v}`,
    },
    {
      title: '折扣',
      dataIndex: 'discount',
      render: (v: number) => v > 0 ? `${(v * 100).toFixed(0)}%` : '-',
    },
    { title: '排序', dataIndex: 'sort', width: 80 },
    {
      title: '状态',
      dataIndex: 'status',
      width: 100,
      render: (status: number) => (
        <Tag color={status === 1 ? 'green' : 'default'}>
          {status === 1 ? '启用' : '禁用'}
        </Tag>
      ),
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      render: (_: any, record: adminApi.UserGroup) => (
        <Space>
          <Button type="link" icon={<EditOutlined />} onClick={() => handleEdit(record)}>
            修改
          </Button>
          <Popconfirm title="确定删除此等级？" onConfirm={() => handleDelete(record.id)}>
            <Button type="link" danger icon={<DeleteOutlined />}>删除</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <div>
      <Title level={4}>会员等级</Title>

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
          dataSource={groups}
          rowKey="id"
          loading={loading}
          pagination={false}
        />
      </Card>

      <Modal
        title={editingId ? '编辑会员等级' : '新增会员等级'}
        open={modalVisible}
        onOk={handleSubmit}
        onCancel={() => setModalVisible(false)}
        width={500}
      >
        <Form form={form} layout="vertical" className="mt-4">
          <Form.Item
            name="name"
            label="等级名称"
            rules={[{ required: true, message: '请输入等级名称' }]}
          >
            <Input placeholder="如：普通会员、VIP会员" />
          </Form.Item>
          
          <Form.Item name="color" label="标签颜色">
            <Input placeholder="如：blue、green、#ff0000" />
          </Form.Item>
          
          <Form.Item name="min_recharge" label="最低累计充值金额">
            <InputNumber min={0} precision={2} className="w-full" prefix="¥" />
          </Form.Item>
          
          <Form.Item 
            name="discount" 
            label="折扣比例"
            extra="0表示不打折，0.1表示9折"
          >
            <InputNumber min={0} max={1} step={0.01} precision={2} className="w-full" />
          </Form.Item>
          
          <Form.Item name="sort" label="排序">
            <InputNumber min={0} className="w-full" />
          </Form.Item>
          
          <Form.Item name="status" label="状态">
            <InputNumber min={0} max={1} className="w-full" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
