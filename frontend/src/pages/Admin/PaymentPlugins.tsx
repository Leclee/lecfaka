import { useEffect, useState } from 'react'
import { Table, Button, Tag, Card, Typography, message, Switch, Space, Modal, Form, Input, Popconfirm, Select } from 'antd'
import { AppstoreAddOutlined, SettingOutlined, DeleteOutlined, FileTextOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import * as adminApi from '../../api/admin'

const { Title } = Typography

export default function PaymentPlugins() {
  const [loading, setLoading] = useState(false)
  const [data, setData] = useState<any[]>([])
  const [configModal, setConfigModal] = useState(false)
  const [editingPlugin, setEditingPlugin] = useState<any>(null)
  const [form] = Form.useForm()
  const navigate = useNavigate()

  const loadData = async () => {
    setLoading(true)
    try {
      const res = await adminApi.getPlugins('payment')
      setData(res.items || [])
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { loadData() }, [])

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

  const columns = [
    {
      title: '插件名称',
      key: 'name',
      width: 160,
      render: (_: any, r: any) => (
        <div className="flex items-center gap-2">
          {r.icon && <img src={r.icon} alt="" className="w-6 h-6 rounded" />}
          <span className="font-medium">{r.name}</span>
        </div>
      ),
    },
    {
      title: '操作',
      key: 'ops',
      width: 140,
      render: (_: any, r: any) => (
        <Space size={4}>
          <Button size="small" type="primary" icon={<SettingOutlined />} onClick={() => handleConfig(r)}>配置</Button>
          <Button size="small" icon={<FileTextOutlined />}>日志</Button>
        </Space>
      ),
    },
    { title: '版本号', dataIndex: 'version', width: 80 },
    {
      title: '功能',
      key: 'channels',
      width: 180,
      render: (_: any, r: any) => {
        const channels = r.channels || {}
        const channelColors: Record<string, string> = { alipay: 'blue', wxpay: 'green', qqpay: 'purple', usdt: 'orange' }
        return (
          <Space size={4} wrap>
            {Object.entries(channels).map(([k, v]) => (
              <Tag key={k} color={channelColors[k] || 'default'}>{v as string}</Tag>
            ))}
          </Space>
        )
      },
    },
    { title: '简介', dataIndex: 'description', ellipsis: true },
    { title: '作者', dataIndex: 'author', width: 80, render: (a: any) => typeof a === 'object' ? a?.name : a },
    {
      title: '卸载',
      key: 'actions',
      width: 120,
      render: (_: any, r: any) => (
        <Space size={4}>
          <Switch checked={r.enabled} onChange={(v) => handleToggle(r.id, v)} checkedChildren="启用" unCheckedChildren="禁用" />
          {!r.is_builtin && (
            <Popconfirm title="确定卸载此插件？" onConfirm={() => handleUninstall(r.id)}>
              <Button type="text" danger size="small" icon={<DeleteOutlined />} />
            </Popconfirm>
          )}
        </Space>
      ),
    },
  ]

  return (
    <div>
      <Title level={4}>支付插件</Title>
      <Card className="rounded-xl border-0 shadow-sm">
        <div className="mb-4">
          <Button type="primary" icon={<AppstoreAddOutlined />} onClick={() => navigate('/admin/store')}>
            安装更多插件
          </Button>
        </div>
        <Table rowKey="id" loading={loading} dataSource={data} columns={columns} pagination={false} size="middle" />
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
              label={
                <span>
                  {schema.label || key}
                  {schema.description && (
                    <span style={{ color: '#999', fontSize: 12, marginLeft: 8 }}>{schema.description}</span>
                  )}
                </span>
              }
              valuePropName={schema.type === 'switch' || schema.type === 'boolean' ? 'checked' : 'value'}
              rules={schema.required ? [{ required: true, message: `请输入${schema.label || key}` }] : []}
            >
              {schema.type === 'textarea' ? (
                <Input.TextArea rows={4} placeholder={schema.placeholder} />
              ) : schema.type === 'switch' || schema.type === 'boolean' ? (
                <Switch />
              ) : schema.type === 'select' && schema.options ? (
                <Select placeholder={`请选择${schema.label || key}`}>
                  {schema.options.map((opt: any) => (
                    <Select.Option key={opt.value} value={opt.value}>{opt.label}</Select.Option>
                  ))}
                </Select>
              ) : schema.type === 'color' ? (
                <Input type="color" style={{ width: 80, height: 32, padding: 2 }} />
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
