import { useEffect, useState } from 'react'
import {
  Card, Table, Button, Tag, Typography, Space, Switch,
  Modal, Form, Input, message, Tabs, Descriptions, Badge, Empty
} from 'antd'
import {
  AppstoreOutlined, SettingOutlined, CheckCircleOutlined,
  CloseCircleOutlined, LockOutlined, ApiOutlined,
  NotificationOutlined, SkinOutlined, ThunderboltOutlined,
  RocketOutlined
} from '@ant-design/icons'
import api from '../../api'

const { Title, Text, Paragraph } = Typography
const { TextArea } = Input

interface PluginInfo {
  id: string
  name: string
  version: string
  type: string
  author: { name: string; url?: string }
  description: string
  icon?: string
  is_builtin: boolean
  enabled: boolean
  license_required: boolean
  license_status: number
  price: number
  config_schema: Record<string, any>
  config: Record<string, any>
  channels?: Record<string, string>
  installed_at?: string
  changelog?: Record<string, string>
}

const typeIcons: Record<string, any> = {
  payment: <ApiOutlined />,
  theme: <SkinOutlined />,
  notify: <NotificationOutlined />,
  delivery: <RocketOutlined />,
  extension: <ThunderboltOutlined />,
}

const typeLabels: Record<string, string> = {
  payment: '支付插件',
  theme: '主题模板',
  notify: '通知插件',
  delivery: '发货插件',
  extension: '功能扩展',
}

const typeColors: Record<string, string> = {
  payment: 'blue',
  theme: 'purple',
  notify: 'green',
  delivery: 'orange',
  extension: 'cyan',
}

export default function Plugins() {
  const [plugins, setPlugins] = useState<PluginInfo[]>([])
  const [loading, setLoading] = useState(false)
  const [activeTab, setActiveTab] = useState('all')
  const [configModal, setConfigModal] = useState<PluginInfo | null>(null)
  const [configForm] = Form.useForm()

  const loadPlugins = async () => {
    setLoading(true)
    try {
      const res: any = await api.get('/admin/plugins')
      setPlugins(res.items || [])
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadPlugins()
  }, [])

  const handleToggle = async (plugin: PluginInfo, enable: boolean) => {
    try {
      const action = enable ? 'enable' : 'disable'
      const res: any = await api.post(`/admin/plugins/${plugin.id}/${action}`)
      message.success(res.message || (enable ? '已启用' : '已禁用'))
      loadPlugins()
    } catch (e: any) {
      message.error(e.message || '操作失败')
    }
  }

  const handleSaveConfig = async () => {
    if (!configModal) return
    try {
      const values = configForm.getFieldsValue()
      const res: any = await api.put(`/admin/plugins/${configModal.id}/config`, values)
      message.success(res.message || '配置已保存')
      setConfigModal(null)
      loadPlugins()
    } catch (e: any) {
      message.error(e.message || '保存失败')
    }
  }

  const openConfig = (plugin: PluginInfo) => {
    setConfigModal(plugin)
    configForm.setFieldsValue(plugin.config || {})
  }

  const filtered = activeTab === 'all'
    ? plugins
    : plugins.filter(p => p.type === activeTab)

  const tabItems = [
    { key: 'all', label: `全部 (${plugins.length})` },
    ...['payment', 'theme', 'notify', 'delivery', 'extension'].map(type => ({
      key: type,
      label: `${typeLabels[type]} (${plugins.filter(p => p.type === type).length})`,
    })),
  ]

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <AppstoreOutlined className="text-2xl text-blue-500" />
          <Title level={4} className="!mb-0">插件管理</Title>
        </div>
        <Button type="primary" disabled>
          插件商店（即将上线）
        </Button>
      </div>

      <Card className="mb-4">
        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          items={tabItems}
        />
      </Card>

      {filtered.length === 0 ? (
        <Card>
          <Empty description="暂无插件" />
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {filtered.map(plugin => (
            <Card
              key={plugin.id}
              className={`border ${plugin.enabled ? 'border-blue-200 shadow-md' : 'border-gray-200'} hover:shadow-lg transition-shadow`}
              size="small"
            >
              <div className="flex items-start gap-3 mb-3">
                <div className={`w-10 h-10 rounded-xl flex items-center justify-center text-white text-lg ${plugin.enabled ? 'bg-gradient-to-br from-blue-500 to-purple-600' : 'bg-gray-400'}`}>
                  {typeIcons[plugin.type] || <ThunderboltOutlined />}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <Text strong className="truncate">{plugin.name}</Text>
                    <Tag color={typeColors[plugin.type]} className="text-xs">
                      {typeLabels[plugin.type]}
                    </Tag>
                  </div>
                  <Text type="secondary" className="text-xs">
                    v{plugin.version}
                    {plugin.author?.name && ` · ${plugin.author.name}`}
                  </Text>
                </div>
              </div>

              <Paragraph type="secondary" ellipsis={{ rows: 2 }} className="!mb-3 text-sm">
                {plugin.description || '暂无描述'}
              </Paragraph>

              {/* 标签 */}
              <div className="flex flex-wrap gap-1 mb-3">
                {plugin.is_builtin && <Tag color="gold" className="text-xs">内置</Tag>}
                {plugin.license_required && (
                  <Tag
                    icon={plugin.license_status === 1 ? <CheckCircleOutlined /> : <LockOutlined />}
                    color={plugin.license_status === 1 ? 'green' : 'red'}
                    className="text-xs"
                  >
                    {plugin.license_status === 1 ? '已授权' : '需授权'}
                  </Tag>
                )}
                {plugin.price > 0 && (
                  <Tag color="orange" className="text-xs">¥{plugin.price}</Tag>
                )}
                {plugin.channels && Object.keys(plugin.channels).length > 0 && (
                  Object.values(plugin.channels).map((ch, i) => (
                    <Tag key={i} className="text-xs">{ch}</Tag>
                  ))
                )}
              </div>

              {/* 操作 */}
              <div className="flex items-center justify-between border-t pt-3">
                <Space>
                  <Switch
                    checked={plugin.enabled}
                    onChange={(checked) => handleToggle(plugin, checked)}
                    checkedChildren="启用"
                    unCheckedChildren="禁用"
                    size="small"
                  />
                  <Badge
                    status={plugin.enabled ? 'success' : 'default'}
                    text={<Text type="secondary" className="text-xs">{plugin.enabled ? '运行中' : '已停止'}</Text>}
                  />
                </Space>
                {Object.keys(plugin.config_schema).length > 0 && (
                  <Button
                    size="small"
                    icon={<SettingOutlined />}
                    onClick={() => openConfig(plugin)}
                  >
                    配置
                  </Button>
                )}
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* 配置弹窗 */}
      <Modal
        title={`配置 - ${configModal?.name || ''}`}
        open={!!configModal}
        onCancel={() => setConfigModal(null)}
        onOk={handleSaveConfig}
        okText="保存"
        cancelText="取消"
        width={600}
      >
        {configModal && (
          <Form form={configForm} layout="vertical">
            {Object.entries(configModal.config_schema).map(([key, schema]: [string, any]) => (
              <Form.Item
                key={key}
                name={key}
                label={schema.label || key}
                rules={schema.required ? [{ required: true, message: `请输入${schema.label || key}` }] : []}
              >
                {schema.type === 'textarea' ? (
                  <TextArea rows={4} placeholder={schema.placeholder} />
                ) : schema.type === 'boolean' ? (
                  <Switch defaultChecked={schema.default} />
                ) : schema.type === 'select' ? (
                  <Input placeholder={schema.placeholder} />
                ) : (
                  <Input
                    placeholder={schema.placeholder}
                    type={schema.encrypted ? 'password' : 'text'}
                  />
                )}
              </Form.Item>
            ))}
          </Form>
        )}
      </Modal>
    </div>
  )
}
