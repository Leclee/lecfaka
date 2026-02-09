import { useEffect, useState, useCallback } from 'react'
import {
  Table, Button, Space, Modal, Form, Input, InputNumber, Switch,
  message, Popconfirm, Card, Typography, Tabs, Tag, Upload, Tooltip
} from 'antd'
import {
  PlusOutlined, EditOutlined, DeleteOutlined, CopyOutlined,
  CheckCircleOutlined, StopOutlined, PictureOutlined, LinkOutlined,
  SearchOutlined, UploadOutlined
} from '@ant-design/icons'
import type { UploadFile, RcFile } from 'antd/es/upload'
import * as adminApi from '../../api/admin'

const { Title } = Typography

interface Category {
  id: number
  name: string
  icon?: string
  description?: string
  sort: number
  status: number
  owner_id?: number
  owner_name?: string
  level_config?: string
  created_at?: string
}

export default function Categories() {
  const [loading, setLoading] = useState(false)
  const [data, setData] = useState<Category[]>([])
  const [modalOpen, setModalOpen] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [selectedRowKeys, setSelectedRowKeys] = useState<number[]>([])
  const [activeTab, setActiveTab] = useState<string>('all')
  const [keyword, setKeyword] = useState('')
  const [iconMode, setIconMode] = useState<'upload' | 'url'>('upload')
  const [iconUrl, setIconUrl] = useState('')
  const [fileList, setFileList] = useState<UploadFile[]>([])
  const [userGroups, setUserGroups] = useState<adminApi.UserGroup[]>([])
  const [levelConfig, setLevelConfig] = useState<Record<string, boolean>>({})
  const [modalTab, setModalTab] = useState('form')
  const [form] = Form.useForm()

  const loadData = useCallback(async () => {
    setLoading(true)
    try {
      const statusMap: Record<string, number | undefined> = {
        all: undefined,
        enabled: 1,
        disabled: 0,
      }
      const res = await adminApi.getCategories({
        status: statusMap[activeTab],
        keyword: keyword || undefined,
      })
      setData(res.items || [])
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }, [activeTab, keyword])

  useEffect(() => {
    loadData()
  }, [loadData])

  // 加载会员等级（打开弹窗时）
  const loadUserGroups = async () => {
    try {
      const res = await adminApi.getUserGroups()
      setUserGroups(res.items || [])
    } catch (e) {
      console.error(e)
    }
  }

  const handleAdd = () => {
    setEditingId(null)
    form.resetFields()
    form.setFieldsValue({ sort: 0, status: true, hide: false })
    setIconUrl('')
    setFileList([])
    setIconMode('upload')
    setLevelConfig({})
    setModalTab('form')
    loadUserGroups()
    setModalOpen(true)
  }

  const handleEdit = (record: Category) => {
    setEditingId(record.id)
    form.setFieldsValue({
      name: record.name,
      description: record.description,
      sort: record.sort,
      status: record.status === 1,
      hide: record.status === 0,
    })
    setIconUrl(record.icon || '')
    if (record.icon) {
      setFileList([{ uid: '-1', name: 'icon', status: 'done', url: record.icon }])
      setIconMode('upload')
    } else {
      setFileList([])
      setIconMode('upload')
    }
    // 解析会员等级配置
    try {
      setLevelConfig(record.level_config ? JSON.parse(record.level_config) : {})
    } catch {
      setLevelConfig({})
    }
    setModalTab('form')
    loadUserGroups()
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

  const handleStatusChange = async (id: number, checked: boolean) => {
    try {
      await adminApi.updateCategory(id, { status: checked ? 1 : 0 })
      message.success(checked ? '已启用' : '已停用')
      loadData()
    } catch (e: any) {
      message.error(e.message || '操作失败')
    }
  }

  const handleBatch = async (action: string) => {
    if (selectedRowKeys.length === 0) {
      message.warning('请先选择分类')
      return
    }
    try {
      const res = await adminApi.batchUpdateCategories({ ids: selectedRowKeys, action })
      message.success(res.message)
      setSelectedRowKeys([])
      loadData()
    } catch (e: any) {
      message.error(e.message || '操作失败')
    }
  }

  const handleCopyLink = (id: number) => {
    const link = `${window.location.origin}/?cid=${id}`
    navigator.clipboard.writeText(link).then(() => {
      message.success('推广链接已复制')
    }).catch(() => {
      message.warning('复制失败，请手动复制')
    })
  }

  const handleIconUpload = async (file: RcFile) => {
    try {
      const res = await adminApi.uploadFile(file, 'icons')
      setIconUrl(res.url)
      setFileList([{ uid: '-1', name: file.name, status: 'done', url: res.url }])
      message.success('图标上传成功')
    } catch (e: any) {
      message.error('上传失败')
    }
    return false // 阻止默认上传
  }

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()
      const finalIcon = iconMode === 'url' ? values.iconUrl : iconUrl
      const payload: adminApi.CategoryForm = {
        name: values.name,
        icon: finalIcon || undefined,
        description: values.description || undefined,
        sort: values.sort ?? 0,
        status: values.hide ? 0 : (values.status ? 1 : 0),
        level_config: Object.keys(levelConfig).length > 0 ? JSON.stringify(levelConfig) : undefined,
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
      title: '图标',
      dataIndex: 'icon',
      width: 70,
      render: (icon: string) =>
        icon ? (
          <img src={icon} alt="" className="w-8 h-8 rounded object-cover" />
        ) : (
          <div className="w-8 h-8 rounded bg-gray-100 flex items-center justify-center">
            <PictureOutlined className="text-gray-300" />
          </div>
        ),
    },
    {
      title: '分类名称',
      dataIndex: 'name',
      ellipsis: true,
    },
    {
      title: '排序(越小越前)',
      dataIndex: 'sort',
      width: 120,
      sorter: (a: Category, b: Category) => a.sort - b.sort,
    },
    {
      title: '推广链接',
      key: 'link',
      width: 100,
      render: (_: any, record: Category) => (
        <Button
          type="primary"
          size="small"
          icon={<CopyOutlined />}
          onClick={() => handleCopyLink(record.id)}
          className="!rounded"
        >
          复制
        </Button>
      ),
    },
    {
      title: '隐藏',
      dataIndex: 'status',
      width: 90,
      render: (status: number) =>
        status === 0 ? (
          <Tag color="error">隐藏</Tag>
        ) : (
          <Tag color="default">未隐藏</Tag>
        ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'statusSwitch',
      width: 90,
      render: (status: number, record: Category) => (
        <Switch
          checked={status === 1}
          checkedChildren="启用"
          unCheckedChildren="停用"
          onChange={(checked) => handleStatusChange(record.id, checked)}
        />
      ),
    },
    {
      title: '操作',
      key: 'action',
      width: 120,
      render: (_: any, record: Category) => (
        <Space size={4}>
          <Tooltip title="编辑">
            <Button
              type="text"
              size="small"
              icon={<EditOutlined />}
              onClick={() => handleEdit(record)}
            />
          </Tooltip>
          <Popconfirm
            title="确定删除此分类？"
            description="删除后不可恢复"
            onConfirm={() => handleDelete(record.id)}
          >
            <Tooltip title="删除">
              <Button type="text" size="small" danger icon={<DeleteOutlined />} />
            </Tooltip>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  const tabItems = [
    { key: 'all', label: '全部' },
    { key: 'enabled', label: '已启用' },
    { key: 'disabled', label: '未启用' },
  ]

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <Title level={4} className="!mb-0">分类管理</Title>
      </div>

      <Card className="rounded-xl border-0 shadow-sm">
        {/* 顶部操作栏 */}
        <div className="flex flex-wrap gap-2 mb-4">
          <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
            添加分类
          </Button>
          <Button
            icon={<CheckCircleOutlined />}
            onClick={() => handleBatch('enable')}
            disabled={selectedRowKeys.length === 0}
          >
            启用选中分类
          </Button>
          <Button
            icon={<StopOutlined />}
            onClick={() => handleBatch('disable')}
            disabled={selectedRowKeys.length === 0}
          >
            停用选中分类
          </Button>
          <Popconfirm
            title={`确定删除选中的 ${selectedRowKeys.length} 个分类？`}
            onConfirm={() => handleBatch('delete')}
            disabled={selectedRowKeys.length === 0}
          >
            <Button
              danger
              icon={<DeleteOutlined />}
              disabled={selectedRowKeys.length === 0}
            >
              移除选中分类
            </Button>
          </Popconfirm>
        </div>

        {/* 搜索区 */}
        <div className="flex gap-2 mb-4">
          <Input
            placeholder="分类名称"
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            onPressEnter={loadData}
            allowClear
            style={{ width: 200 }}
          />
          <Button type="primary" icon={<SearchOutlined />} onClick={loadData}>
            查询
          </Button>
        </div>

        {/* 状态 Tab */}
        <Tabs
          activeKey={activeTab}
          onChange={(key) => {
            setActiveTab(key)
            setSelectedRowKeys([])
          }}
          items={tabItems}
          className="!mb-2"
        />

        {/* 表格 */}
        <Table
          rowKey="id"
          loading={loading}
          dataSource={data}
          columns={columns}
          pagination={false}
          rowSelection={{
            selectedRowKeys,
            onChange: (keys) => setSelectedRowKeys(keys as number[]),
          }}
          size="middle"
        />
      </Card>

      {/* 添加/编辑弹窗 */}
      <Modal
        title={
          <Tabs
            activeKey={modalTab}
            onChange={setModalTab}
            items={[
              { key: 'form', label: editingId ? '编辑分类' : '添加分类' },
              { key: 'levels', label: '会员等级' },
            ]}
            className="!mb-0"
          />
        }
        open={modalOpen}
        onOk={handleSubmit}
        onCancel={() => setModalOpen(false)}
        okText="保存"
        cancelText="取消"
        destroyOnClose
        width={560}
      >
        {/* Tab 1: 分类表单 */}
        <div style={{ display: modalTab === 'form' ? 'block' : 'none' }}>
          <Form form={form} layout="vertical" className="mt-2">
            <Form.Item label="图标">
              <Space direction="vertical" className="w-full">
                <Space>
                  <Button
                    type={iconMode === 'upload' ? 'primary' : 'default'}
                    size="small"
                    icon={<PictureOutlined />}
                    onClick={() => setIconMode('upload')}
                  >
                    上传图片
                  </Button>
                  <Button
                    type={iconMode === 'url' ? 'primary' : 'default'}
                    size="small"
                    icon={<LinkOutlined />}
                    onClick={() => setIconMode('url')}
                  >
                    URL 链接
                  </Button>
                </Space>
                {iconMode === 'upload' ? (
                  <Upload
                    listType="picture-card"
                    fileList={fileList}
                    beforeUpload={handleIconUpload}
                    onRemove={() => {
                      setFileList([])
                      setIconUrl('')
                    }}
                    maxCount={1}
                    accept="image/*"
                  >
                    {fileList.length === 0 && (
                      <div>
                        <UploadOutlined />
                        <div className="mt-1 text-xs">选择图标</div>
                      </div>
                    )}
                  </Upload>
                ) : (
                  <Form.Item name="iconUrl" noStyle>
                    <Input
                      placeholder="请输入图标URL"
                      value={iconUrl}
                      onChange={(e) => setIconUrl(e.target.value)}
                    />
                  </Form.Item>
                )}
              </Space>
            </Form.Item>

            <Form.Item
              name="name"
              label="分类名称"
              rules={[{ required: true, message: '请输入分类名称' }]}
            >
              <Input placeholder="请输入分类名称" />
            </Form.Item>

            <Form.Item name="description" label="描述">
              <Input.TextArea placeholder="请输入描述" rows={3} />
            </Form.Item>

            <Form.Item name="sort" label="排序">
              <InputNumber min={0} className="w-full" placeholder="值越小，排名越靠前哦~" />
            </Form.Item>

            <Form.Item name="hide" label="隐藏分类" valuePropName="checked">
              <Switch />
            </Form.Item>

            <Form.Item name="status" label="状态" valuePropName="checked">
              <Switch />
            </Form.Item>
          </Form>
        </div>

        {/* Tab 2: 会员等级配置 */}
        <div style={{ display: modalTab === 'levels' ? 'block' : 'none' }}>
          <div className="mt-2 rounded-lg border border-gray-100 p-4">
            <div className="flex justify-between items-center mb-4 pb-2 border-b">
              <span className="font-medium">会员</span>
              <span className="font-medium">绝对显示</span>
            </div>
            {userGroups.length > 0 ? (
              <div className="space-y-4">
                {userGroups.map((group) => (
                  <div key={group.id} className="flex justify-between items-center">
                    <Tag
                      color={group.color || 'blue'}
                      className="!text-sm !px-3 !py-1"
                    >
                      {group.name}
                    </Tag>
                    <Switch
                      checked={!!levelConfig[String(group.id)]}
                      checkedChildren="开启"
                      unCheckedChildren="关闭"
                      onChange={(checked) => {
                        setLevelConfig((prev) => ({
                          ...prev,
                          [String(group.id)]: checked,
                        }))
                      }}
                    />
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center text-gray-400 py-8">
                暂无会员等级，请先在「会员等级」中创建
              </div>
            )}
          </div>
        </div>
      </Modal>
    </div>
  )
}
