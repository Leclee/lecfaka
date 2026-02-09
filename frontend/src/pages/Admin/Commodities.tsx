import { useEffect, useState } from 'react'
import { 
  Table, Button, Space, Modal, Form, Input, InputNumber, Switch, 
  Select, message, Popconfirm, Card, Typography, Tag, Row, Col, 
  Statistic, Tabs, Upload, Radio, Divider, Spin
} from 'antd'
import type { UploadProps } from 'antd'
import { 
  PlusOutlined, EditOutlined, DeleteOutlined, 
  ShoppingOutlined, CheckCircleOutlined, CloseCircleOutlined,
  UploadOutlined, LinkOutlined, MinusCircleOutlined
} from '@ant-design/icons'
import * as adminApi from '../../api/admin'

const { Title, Text } = Typography
const { TextArea } = Input
const { Option } = Select

interface Commodity {
  id: number
  name: string
  cover?: string
  category_id: number
  category_name?: string
  price: number
  user_price: number
  factory_price?: number
  stock: number
  delivery_way: number
  delivery_auto_mode?: number
  delivery_message?: string
  contact_type?: number
  password_status?: number
  send_email?: number
  minimum?: number
  maximum?: number
  purchase_count?: number
  only_user?: number
  coupon?: number
  api_status?: number
  recommend?: number
  hide?: number
  inventory_hidden?: number
  seckill_status?: number
  draft_status?: number
  level_disable?: number
  level_price?: string
  wholesale_config?: string
  config?: string
  description?: string
  leave_message?: string
  status: number
  sort: number
  sold_count?: number
}

interface Category {
  id: number
  name: string
}

interface UserGroup {
  id: number
  name: string
  discount: number
}

// 图标上传/选择组件
function IconUploader({ value, onChange }: { value?: string; onChange?: (v: string) => void }) {
  const [mode, setMode] = useState<'upload' | 'url'>('url')
  const [loading, setLoading] = useState(false)
  const [imageUrl, setImageUrl] = useState(value || '')

  useEffect(() => {
    setImageUrl(value || '')
  }, [value])

  const handleUpload = async (file: File) => {
    setLoading(true)
    try {
      const res = await adminApi.uploadFile(file, 'icons')
      setImageUrl(res.url)
      onChange?.(res.url)
      message.success('上传成功')
    } catch (e: any) {
      message.error(e.message || '上传失败')
    } finally {
      setLoading(false)
    }
    return false
  }

  const uploadProps: UploadProps = {
    beforeUpload: handleUpload,
    showUploadList: false,
    accept: 'image/*',
  }

  return (
    <div>
      <Radio.Group value={mode} onChange={(e) => setMode(e.target.value)} className="mb-3">
        <Radio.Button value="upload"><UploadOutlined /> 上传图标</Radio.Button>
        <Radio.Button value="url"><LinkOutlined /> 图片链接</Radio.Button>
      </Radio.Group>
      
      <div className="flex items-start gap-4">
        <div className="w-16 h-16 border border-dashed border-gray-300 rounded-lg flex items-center justify-center overflow-hidden bg-gray-50">
          {loading ? (
            <Spin size="small" />
          ) : imageUrl ? (
            <img src={imageUrl} alt="" className="w-full h-full object-contain" />
          ) : (
            <ShoppingOutlined className="text-xl text-gray-400" />
          )}
        </div>
        
        {mode === 'upload' ? (
          <Upload {...uploadProps}>
            <Button icon={<UploadOutlined />} loading={loading}>选择图片</Button>
          </Upload>
        ) : (
          <Input 
            value={imageUrl}
            onChange={(e) => {
              setImageUrl(e.target.value)
              onChange?.(e.target.value)
            }}
            placeholder="请输入图片URL"
            className="flex-1"
          />
        )}
      </div>
    </div>
  )
}

// 批量优惠配置组件
function WholesaleConfig({ value, onChange }: { value?: string; onChange?: (v: string) => void }) {
  const [items, setItems] = useState<{ quantity: number; price: number }[]>([])

  useEffect(() => {
    if (value) {
      try {
        setItems(JSON.parse(value))
      } catch {
        setItems([])
      }
    } else {
      setItems([])
    }
  }, [value])

  const handleChange = (newItems: { quantity: number; price: number }[]) => {
    setItems(newItems)
    onChange?.(JSON.stringify(newItems))
  }

  const addItem = () => {
    handleChange([...items, { quantity: 10, price: 0 }])
  }

  const removeItem = (index: number) => {
    const newItems = items.filter((_, i) => i !== index)
    handleChange(newItems)
  }

  const updateItem = (index: number, field: 'quantity' | 'price', val: number) => {
    const newItems = [...items]
    newItems[index][field] = val
    handleChange(newItems)
  }

  return (
    <div>
      <Text type="secondary" className="text-xs mb-2 block">
        设置批量购买优惠价格，数量越多价格越低
      </Text>
      {items.map((item, index) => (
        <div key={index} className="flex items-center gap-2 mb-2">
          <span>购买</span>
          <InputNumber 
            min={2} 
            value={item.quantity} 
            onChange={(v) => updateItem(index, 'quantity', v || 2)}
            className="w-20"
          />
          <span>个及以上，单价</span>
          <InputNumber 
            min={0} 
            step={0.01}
            value={item.price} 
            onChange={(v) => updateItem(index, 'price', v || 0)}
            className="w-24"
            prefix="¥"
          />
          <Button 
            type="text" 
            danger 
            icon={<MinusCircleOutlined />} 
            onClick={() => removeItem(index)}
          />
        </div>
      ))}
      <Button type="dashed" onClick={addItem} icon={<PlusOutlined />} block>
        添加批量价格
      </Button>
    </div>
  )
}

// 会员等级价格配置组件
function LevelPriceConfig({ 
  value, 
  onChange,
  userGroups 
}: { 
  value?: string
  onChange?: (v: string) => void
  userGroups: UserGroup[]
}) {
  const [prices, setPrices] = useState<Record<string, number>>({})

  useEffect(() => {
    if (value) {
      try {
        setPrices(JSON.parse(value))
      } catch {
        setPrices({})
      }
    } else {
      setPrices({})
    }
  }, [value])

  const handleChange = (groupId: string, price: number) => {
    const newPrices = { ...prices, [groupId]: price }
    setPrices(newPrices)
    onChange?.(JSON.stringify(newPrices))
  }

  return (
    <div>
      <Text type="secondary" className="text-xs mb-2 block">
        为不同会员等级设置专属价格，未设置则使用默认会员价
      </Text>
      {userGroups.map((group) => (
        <div key={group.id} className="flex items-center gap-4 mb-2">
          <span className="w-24">{group.name}:</span>
          <InputNumber
            min={0}
            step={0.01}
            value={prices[group.id.toString()]}
            onChange={(v) => handleChange(group.id.toString(), v || 0)}
            placeholder="使用默认会员价"
            className="w-40"
            prefix="¥"
          />
          <Text type="secondary" className="text-xs">
            默认折扣: {group.discount}%
          </Text>
        </div>
      ))}
      {userGroups.length === 0 && (
        <Text type="secondary">暂无会员等级，请先在会员等级管理中创建</Text>
      )}
    </div>
  )
}

export default function Commodities() {
  const [loading, setLoading] = useState(false)
  const [data, setData] = useState<Commodity[]>([])
  const [categories, setCategories] = useState<Category[]>([])
  const [userGroups, setUserGroups] = useState<UserGroup[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize] = useState(20)
  const [modalOpen, setModalOpen] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [form] = Form.useForm()
  const [activeTab, setActiveTab] = useState('all')
  const [modalTab, setModalTab] = useState('basic')

  const [stats, setStats] = useState({ total: 0, online: 0, offline: 0 })

  useEffect(() => {
    loadCategories()
    loadUserGroups()
  }, [])

  useEffect(() => {
    loadData()
  }, [page, activeTab])

  const loadCategories = async () => {
    try {
      const res = await adminApi.getCategories()
      setCategories(res.items || [])
    } catch (e) {
      console.error(e)
    }
  }

  const loadUserGroups = async () => {
    try {
      const res = await adminApi.getUserGroups()
      setUserGroups(res.items || [])
    } catch (e) {
      console.error(e)
    }
  }

  const loadData = async () => {
    setLoading(true)
    try {
      const status = activeTab === 'online' ? 1 : activeTab === 'offline' ? 0 : undefined
      const res = await adminApi.getCommodities({ page, limit: pageSize, status })
      setData(res.items || [])
      setTotal(res.total || 0)
      
      const [onlineRes, offlineRes] = await Promise.all([
        adminApi.getCommodities({ status: 1, limit: 1 }),
        adminApi.getCommodities({ status: 0, limit: 1 }),
      ])
      setStats({
        total: (onlineRes.total || 0) + (offlineRes.total || 0),
        online: onlineRes.total || 0,
        offline: offlineRes.total || 0,
      })
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  const handleAdd = () => {
    setEditingId(null)
    setModalTab('basic')
    form.resetFields()
    form.setFieldsValue({
      price: 1,
      user_price: 1,
      delivery_way: 0,
      delivery_auto_mode: 0,
      contact_type: 0,
      sort: 0,
      status: true,
      minimum: 1,
      maximum: 100,
      send_email: false,
      password_status: false,
      only_user: false,
      coupon: true,
      api_status: false,
      recommend: false,
      hide: false,
      inventory_hidden: false,
      seckill_status: false,
      draft_status: false,
      level_disable: false,
    })
    setModalOpen(true)
  }

  const handleEdit = async (record: Commodity) => {
    setEditingId(record.id)
    setModalTab('basic')
    try {
      const detail = await adminApi.getCommodity(record.id)
      form.setFieldsValue({
        ...detail,
        status: detail.status === 1,
        send_email: detail.send_email === 1,
        password_status: detail.password_status === 1,
        only_user: detail.only_user === 1,
        coupon: detail.coupon === 1,
        api_status: detail.api_status === 1,
        recommend: detail.recommend === 1,
        hide: detail.hide === 1,
        inventory_hidden: detail.inventory_hidden === 1,
        seckill_status: detail.seckill_status === 1,
        draft_status: detail.draft_status === 1,
        level_disable: detail.level_disable === 1,
      })
      setModalOpen(true)
    } catch (e) {
      message.error('获取商品详情失败')
    }
  }

  const handleDelete = async (id: number) => {
    try {
      await adminApi.deleteCommodity(id)
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
        send_email: values.send_email ? 1 : 0,
        password_status: values.password_status ? 1 : 0,
        only_user: values.only_user ? 1 : 0,
        coupon: values.coupon ? 1 : 0,
        api_status: values.api_status ? 1 : 0,
        recommend: values.recommend ? 1 : 0,
        hide: values.hide ? 1 : 0,
        inventory_hidden: values.inventory_hidden ? 1 : 0,
        seckill_status: values.seckill_status ? 1 : 0,
        draft_status: values.draft_status ? 1 : 0,
        level_disable: values.level_disable ? 1 : 0,
      }

      if (editingId) {
        await adminApi.updateCommodity(editingId, payload)
        message.success('更新成功')
      } else {
        await adminApi.createCommodity(payload)
        message.success('创建成功')
      }
      
      setModalOpen(false)
      loadData()
    } catch (e: any) {
      if (e.errorFields) return
      message.error(e.message || '操作失败')
    }
  }

  const handleToggleStatus = async (record: Commodity) => {
    try {
      await adminApi.updateCommodity(record.id, { 
        status: record.status === 1 ? 0 : 1 
      })
      message.success('状态已更新')
      loadData()
    } catch (e: any) {
      message.error(e.message || '操作失败')
    }
  }

  const columns = [
    {
      title: '',
      dataIndex: 'cover',
      width: 60,
      render: (cover: string) => (
        <div className="w-10 h-10 bg-gray-100 rounded overflow-hidden">
          {cover ? (
            <img src={cover} alt="" className="w-full h-full object-cover" />
          ) : (
            <div className="w-full h-full flex items-center justify-center">
              <ShoppingOutlined className="text-gray-300" />
            </div>
          )}
        </div>
      ),
    },
    {
      title: '分类',
      dataIndex: 'category_name',
      width: 120,
      render: (name: string) => <Tag color="blue">{name || '未分类'}</Tag>,
    },
    {
      title: '商品名称',
      dataIndex: 'name',
      ellipsis: true,
    },
    {
      title: '库存',
      dataIndex: 'stock',
      width: 80,
      render: (stock: number) => (
        <span className={stock > 10 ? 'text-green-500' : stock > 0 ? 'text-orange-500' : 'text-red-500'}>
          {stock > 0 ? stock : '售罄'}
        </span>
      ),
    },
    {
      title: '零售价',
      dataIndex: 'price',
      width: 90,
      render: (price: number) => <span className="text-red-500">¥{price}</span>,
    },
    {
      title: '会员价',
      dataIndex: 'user_price',
      width: 90,
      render: (price: number) => <span className="text-orange-500">¥{price}</span>,
    },
    {
      title: '销量',
      dataIndex: 'sold_count',
      width: 70,
      render: (count: number) => count || 0,
    },
    {
      title: '排序',
      dataIndex: 'sort',
      width: 60,
    },
    {
      title: '状态',
      dataIndex: 'status',
      width: 80,
      render: (status: number, record: Commodity) => (
        <Switch 
          checked={status === 1} 
          checkedChildren="上架" 
          unCheckedChildren="下架"
          onChange={() => handleToggleStatus(record)}
        />
      ),
    },
    {
      title: '操作',
      key: 'action',
      width: 140,
      render: (_: any, record: Commodity) => (
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
            title="确定删除此商品？"
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

  const modalTabItems = [
    {
      key: 'basic',
      label: '添加商品',
      children: (
        <div className="py-4">
          <Form.Item name="category_id" label="商品分类" rules={[{ required: true, message: '请选择分类' }]}>
            <Select placeholder="请选择商品分类">
              {categories.map(cat => (
                <Option key={cat.id} value={cat.id}>{cat.name}</Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item name="cover" label="商品图标">
            <IconUploader />
          </Form.Item>

          <Form.Item name="name" label="商品名称" rules={[{ required: true, message: '请输入名称' }]}>
            <Input placeholder="商品名称" />
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="price" label="零售价" rules={[{ required: true }]}>
                <InputNumber min={0} step={0.01} className="w-full" placeholder="零售价" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="user_price" label="会员零售价" rules={[{ required: true }]}>
                <InputNumber min={0} step={0.01} className="w-full" placeholder="会员零售价" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="sort" label="排序">
                <InputNumber min={0} className="w-full" placeholder="排序，越小越靠前" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="status" label="状态" valuePropName="checked">
                <Switch checkedChildren="ON" unCheckedChildren="OFF" />
              </Form.Item>
            </Col>
          </Row>
        </div>
      ),
    },
    {
      key: 'delivery',
      label: '发货设置',
      children: (
        <div className="py-4">
          <Form.Item name="delivery_way" label="发货方式">
            <Radio.Group>
              <Radio value={0}>自动发货</Radio>
              <Radio value={1}>手动/插件发货</Radio>
            </Radio.Group>
          </Form.Item>

          <Form.Item name="delivery_auto_mode" label="卡密排序">
            <Radio.Group>
              <Radio value={0}>旧卡先发</Radio>
              <Radio value={1}>随机发卡</Radio>
              <Radio value={2}>新卡先发</Radio>
            </Radio.Group>
          </Form.Item>

          <Form.Item name="delivery_message" label="发货留言">
            <TextArea rows={3} placeholder="当用户购买商品后，该留言会显示在订单中" />
          </Form.Item>

          <Form.Item name="contact_type" label="联系方式">
            <Radio.Group>
              <Radio value={0}>任意</Radio>
              <Radio value={1}>手机</Radio>
              <Radio value={2}>邮箱</Radio>
              <Radio value={3}>QQ</Radio>
            </Radio.Group>
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="send_email" label="邮件发送" valuePropName="checked">
                <Switch checkedChildren="ON" unCheckedChildren="OFF" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="password_status" label="查询密码" valuePropName="checked">
                <Switch checkedChildren="ON" unCheckedChildren="OFF" />
              </Form.Item>
            </Col>
          </Row>
        </div>
      ),
    },
    {
      key: 'description',
      label: '商品介绍',
      children: (
        <div className="py-4">
          <Form.Item name="description" label="商品描述">
            <TextArea rows={10} placeholder="请输入商品描述，支持HTML格式" />
          </Form.Item>
          <Form.Item name="leave_message" label="售后留言">
            <TextArea rows={4} placeholder="购买后显示的售后说明" />
          </Form.Item>
        </div>
      ),
    },
    {
      key: 'limit',
      label: '商品限制',
      children: (
        <div className="py-4">
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="minimum" label="最低购买数量">
                <InputNumber min={0} className="w-full" placeholder="0表示不限制" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="maximum" label="最大购买数量">
                <InputNumber min={0} className="w-full" placeholder="0表示不限制" />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item name="coupon" label="优惠卷" valuePropName="checked">
            <Switch checkedChildren="ON" unCheckedChildren="OFF" />
          </Form.Item>

          <Form.Item name="seckill_status" label="限时秒杀" valuePropName="checked">
            <Switch checkedChildren="ON" unCheckedChildren="OFF" />
          </Form.Item>

          <Form.Item name="draft_status" label="卡密预选" valuePropName="checked">
            <Switch checkedChildren="ON" unCheckedChildren="OFF" />
          </Form.Item>

          <Form.Item name="only_user" label="仅限会员购买" valuePropName="checked">
            <Switch checkedChildren="ON" unCheckedChildren="OFF" />
          </Form.Item>

          <Form.Item name="purchase_count" label="会员限购">
            <InputNumber min={0} className="w-full" placeholder="0表示不限购" />
          </Form.Item>

          <Form.Item name="api_status" label="API对接" valuePropName="checked">
            <Switch checkedChildren="ON" unCheckedChildren="OFF" />
          </Form.Item>

          <Form.Item name="inventory_hidden" label="隐藏库存" valuePropName="checked">
            <Switch checkedChildren="ON" unCheckedChildren="OFF" />
          </Form.Item>

          <Form.Item name="hide" label="隐藏商品" valuePropName="checked">
            <Switch checkedChildren="ON" unCheckedChildren="OFF" />
          </Form.Item>

          <Form.Item name="level_disable" label="禁用折扣" valuePropName="checked">
            <Switch checkedChildren="ON" unCheckedChildren="OFF" />
          </Form.Item>

          <Form.Item name="recommend" label="首页推荐" valuePropName="checked">
            <Switch checkedChildren="ON" unCheckedChildren="OFF" />
          </Form.Item>
        </div>
      ),
    },
    {
      key: 'wholesale',
      label: '批量优惠',
      children: (
        <div className="py-4">
          <Form.Item name="wholesale_config" label="批量销售优惠">
            <WholesaleConfig />
          </Form.Item>

          <Divider />

          <Form.Item name="factory_price" label="成本价">
            <InputNumber min={0} step={0.01} className="w-full" prefix="¥" placeholder="用于计算利润" />
          </Form.Item>
        </div>
      ),
    },
    {
      key: 'level',
      label: '会员等级',
      children: (
        <div className="py-4">
          <Form.Item name="level_price" label="会员等级专属价格">
            <LevelPriceConfig userGroups={userGroups} />
          </Form.Item>
        </div>
      ),
    },
  ]

  return (
    <div>
      <Title level={4} className="mb-4">商品管理</Title>

      <Row gutter={16} className="mb-6">
        <Col span={8}>
          <Card className="rounded-xl border-0 shadow-sm">
            <Statistic title="总商品" value={stats.total} prefix={<ShoppingOutlined />} />
          </Card>
        </Col>
        <Col span={8}>
          <Card className="rounded-xl border-0 shadow-sm">
            <Statistic 
              title="已上架" 
              value={stats.online} 
              valueStyle={{ color: '#52c41a' }}
              prefix={<CheckCircleOutlined />} 
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card className="rounded-xl border-0 shadow-sm">
            <Statistic 
              title="已下架" 
              value={stats.offline} 
              valueStyle={{ color: '#ff4d4f' }}
              prefix={<CloseCircleOutlined />} 
            />
          </Card>
        </Col>
      </Row>

      <Card className="rounded-xl border-0 shadow-sm mb-4">
        <div className="flex justify-between items-center">
          <Tabs
            activeKey={activeTab}
            onChange={setActiveTab}
            items={[
              { key: 'all', label: '全部' },
              { key: 'online', label: '已上架' },
              { key: 'offline', label: '已下架' },
            ]}
          />
          <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
            添加商品
          </Button>
        </div>
      </Card>

      <Card className="rounded-xl border-0 shadow-sm">
        <Table
          rowKey="id"
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
        />
      </Card>

      <Modal
        title={editingId ? '编辑商品' : '添加商品'}
        open={modalOpen}
        onOk={handleSubmit}
        onCancel={() => setModalOpen(false)}
        width={800}
        destroyOnClose
        okText="保存"
        cancelText="取消"
      >
        <Form form={form} layout="vertical">
          <Tabs 
            activeKey={modalTab} 
            onChange={setModalTab}
            items={modalTabItems}
          />
        </Form>
      </Modal>
    </div>
  )
}
