import { useEffect, useState } from 'react'
import {
  Table, Button, Tag, Card, Typography, message, Switch, Space,
  Modal, Form, Input, Popconfirm, Upload, Tabs
} from 'antd'
import { AppstoreAddOutlined, SettingOutlined, DeleteOutlined, UploadOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import * as adminApi from '../../api/admin'

const { Title } = Typography

export default function GeneralPlugins() {
  const [loading, setLoading] = useState(false)
  const [data, setData] = useState<any[]>([])
  const [activeTab, setActiveTab] = useState('all')
  const [configModal, setConfigModal] = useState(false)
  const [editingPlugin, setEditingPlugin] = useState<any>(null)
  const [form] = Form.useForm()
  const navigate = useNavigate()

  const loadData = async () => {
    setLoading(true)
    try {
      // 加载非支付类插件
      const res = await adminApi.getPlugins()
      const nonPayment = (res.items || []).filter((p: any) => p.type !== 'payment')
      setData(nonPayment)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { loadData() }, [])

  const filteredData = activeTab === 'all' ? data : data.filter(p => p.type === activeTab)

  const handleToggle = async (pluginId: string, enable: boolean) => {
    try {
      if (enable) {
        await adminApi.enablePlugin(pluginId)
        message.success('已启用')
      } else {
        await adminApi.disablePlugin(pluginId)
        message.success('已禁用')
      }
      loadData()
    } catch (e: any) {
      message.error(e.message || '操作失败')
    }
  }

  const handleConfig = (plugin: any) => {
    setEditingPlugin(plugin)
    form.setFieldsValue(plugin.config || {})
    setConfigModal(true)
  }

  const handleConfigSave = async () => {
    if (!editingPlugin) return
    try {
      const values = await form.validateFields()
      await adminApi.updatePluginConfig(editingPlugin.id, values)
      message.success('配置已保存')
      setConfigModal(false)
      loadData()
    } catch (e: any) {
      if (e.errorFields) return
      message.error(e.message || '保存失败')
    }
  }

  const handleUninstall = async (pluginId: string) => {
    try {
      const res = await adminApi.uninstallPlugin(pluginId)
      message.success(res.message)
      loadData()
    } catch (e: any) {
      message.error(e.message || '卸载失败')
    }
  }

  const handleUploadInstall = async (file: File) => {
    try {
      const res = await adminApi.installPlugin(file)
      message.success(res.message)
      loadData()
    } catch (e: any) {
      message.error(e.message || '安装失败')
    }
    return false
  }

  const typeTagColor: Record<string, string> = {
    extension: 'blue', notify: 'orange', delivery: 'cyan', theme: 'purple',
  }
  const typeLabel: Record<string, string> = {
    extension: '通用扩展', notify: '通知插件', delivery: '发货插件', theme: '主题模板',
  }

  const columns = [
    {
      title: '插件名称',
      key: 'name',
      width: 180,
      render: (_: any, r: any) => (
        <div className="flex items-center gap-2">
          {r.icon && <img src={r.icon} alt="" className="w-6 h-6 rounded" />}
          <div>
            <div className="font-medium">{r.name}</div>
            {r.is_builtin && <Tag color="default" className="!text-xs">内置</Tag>}
          </div>
        </div>
      ),
    },
    {
      title: '类型',
      dataIndex: 'type',
      width: 100,
      render: (t: string) => <Tag color={typeTagColor[t] || 'default'}>{typeLabel[t] || t}</Tag>,
    },
    { title: '版本', dataIndex: 'version', width: 70 },
    { title: '简介', dataIndex: 'description', ellipsis: true },
    { title: '作者', dataIndex: 'author', width: 80, render: (a: any) => typeof a === 'object' ? a?.name : a },
    {
      title: '状态',
      key: 'status',
      width: 100,
      render: (_: any, r: any) => (
        <Switch checked={r.enabled} onChange={v => handleToggle(r.id, v)} checkedChildren="启用" unCheckedChildren="禁用" />
      ),
    },
    {
      title: '操作',
      key: 'action',
      width: 120,
      render: (_: any, r: any) => (
        <Space size={4}>
          {r.config_schema && Object.keys(r.config_schema).length > 0 && (
            <Button size="small" icon={<SettingOutlined />} onClick={() => handleConfig(r)}>配置</Button>
          )}
          {!r.is_builtin && (
            <Popconfirm title="确定卸载？" onConfirm={() => handleUninstall(r.id)}>
              <Button type="text" danger size="small" icon={<DeleteOutlined />} />
            </Popconfirm>
          )}
        </Space>
      ),
    },
  ]

  const tabItems = [
    { key: 'all', label: '全部' },
    { key: 'extension', label: '通用扩展' },
    { key: 'notify', label: '通知插件' },
    { key: 'delivery', label: '发货插件' },
    { key: 'theme', label: '主题模板' },
  ]

  return (
    <div>
      <Title level={4}>通用插件</Title>
      <Card className="rounded-xl border-0 shadow-sm">
        <div className="flex gap-2 mb-4">
          <Button type="primary" icon={<AppstoreAddOutlined />} onClick={() => navigate('/admin/store')}>
            安装更多插件
          </Button>
          <Upload beforeUpload={handleUploadInstall as any} showUploadList={false} accept=".zip">
            <Button icon={<UploadOutlined />}>上传安装</Button>
          </Upload>
        </div>
        <Tabs activeKey={activeTab} onChange={setActiveTab} items={tabItems} className="!mb-2" />
        <Table rowKey="id" loading={loading} dataSource={filteredData} columns={columns} pagination={false} size="middle" />
      </Card>

      {/* 配置弹窗 */}
      <Modal
        title={`配置 - ${editingPlugin?.name || ''}`}
        open={configModal}
        onOk={handleConfigSave}
        onCancel={() => setConfigModal(false)}
        okText="保存"
        destroyOnClose
      >
        <Form form={form} layout="vertical" className="mt-4">
          {editingPlugin?.config_schema && Object.entries(editingPlugin.config_schema).map(([key, schema]: [string, any]) => (
            <Form.Item
              key={key}
              name={key}
              label={schema.label || key}
              rules={schema.required ? [{ required: true, message: `请输入${schema.label || key}` }] : []}
            >
              {schema.type === 'boolean' ? (
                <Switch />
              ) : schema.type === 'textarea' ? (
                <Input.TextArea rows={3} placeholder={schema.placeholder} />
              ) : (
                <Input placeholder={schema.placeholder} type={schema.encrypted ? 'password' : 'text'} />
              )}
            </Form.Item>
          ))}
        </Form>
      </Modal>
    </div>
  )
}
