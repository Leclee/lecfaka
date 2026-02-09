import { useEffect, useState } from 'react'
import {
  Card, Tabs, Table, Button, Space, Modal, Form, Input,
  InputNumber, Select, Switch, message, Tag, Typography, 
  Upload, Alert, Spin, Divider
} from 'antd'
import { 
  PlusOutlined, EditOutlined, DeleteOutlined, ReloadOutlined, 
  UploadOutlined, SaveOutlined, SettingOutlined
} from '@ant-design/icons'
import type { UploadProps } from 'antd'
import * as adminApi from '../../api/admin'

const { Title, Text } = Typography
const { TextArea } = Input

// 图片上传组件
function ImageUploader({ 
  value, 
  onChange,
  category = 'images'
}: { 
  value?: string
  onChange?: (url: string) => void
  category?: string
}) {
  const [loading, setLoading] = useState(false)
  const [imageUrl, setImageUrl] = useState(value || '')

  useEffect(() => {
    setImageUrl(value || '')
  }, [value])

  const handleUpload = async (file: File) => {
    setLoading(true)
    try {
      const res = await adminApi.uploadFile(file, category)
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
    <div className="flex items-start gap-4">
      <div className="w-24 h-24 border border-dashed border-gray-300 rounded-lg flex items-center justify-center overflow-hidden bg-gray-50">
        {loading ? (
          <Spin size="small" />
        ) : imageUrl ? (
          <img src={imageUrl} alt="" className="w-full h-full object-contain" />
        ) : (
          <UploadOutlined className="text-2xl text-gray-400" />
        )}
      </div>
      <div className="flex-1">
        <Space direction="vertical" size="small">
          <Upload {...uploadProps}>
            <Button icon={<UploadOutlined />} loading={loading}>上传图片</Button>
          </Upload>
          <Input 
            value={imageUrl}
            onChange={(e) => {
              setImageUrl(e.target.value)
              onChange?.(e.target.value)
            }}
            placeholder="或输入图片URL"
            className="w-64"
          />
          <Text type="secondary" className="text-xs">
            支持 png, jpg, jpeg, gif, ico 格式
          </Text>
        </Space>
      </div>
    </div>
  )
}

export default function Settings() {
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [payments, setPayments] = useState<adminApi.PaymentConfig[]>([])
  const [_configs, setConfigs] = useState<Record<string, string>>({})

  // 支付配置弹窗
  const [paymentModalVisible, setPaymentModalVisible] = useState(false)
  const [editingPayment, setEditingPayment] = useState<adminApi.PaymentConfig | null>(null)
  const [paymentForm] = Form.useForm()

  // 设置表单
  const [basicForm] = Form.useForm()
  const [smsForm] = Form.useForm()
  const [emailForm] = Form.useForm()
  const [otherForm] = Form.useForm()

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    setLoading(true)
    try {
      const [paymentsRes, settingsRes] = await Promise.all([
        adminApi.getPaymentSettings(),
        adminApi.getSettingsFlat(),
      ])
      setPayments(paymentsRes.items)
      setConfigs(settingsRes)
      
      // 填充表单
      basicForm.setFieldsValue(settingsRes)
      smsForm.setFieldsValue(settingsRes)
      emailForm.setFieldsValue(settingsRes)
      otherForm.setFieldsValue(settingsRes)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  const loadPayments = async () => {
    try {
      const res = await adminApi.getPaymentSettings()
      setPayments(res.items)
    } catch (e) {
      console.error(e)
    }
  }

  // 初始化默认配置
  const handleInitSettings = async () => {
    try {
      const res = await adminApi.initSettings()
      message.success(res.message)
      loadData()
    } catch (e: any) {
      message.error(e.message || '初始化失败')
    }
  }

  // 保存基本设置
  const handleSaveBasic = async () => {
    try {
      const values = await basicForm.validateFields()
      setSaving(true)
      await adminApi.updateSettings(values)
      message.success('保存成功')
    } catch (e: any) {
      if (!e.errorFields) {
        message.error(e.message || '保存失败')
      }
    } finally {
      setSaving(false)
    }
  }

  // 保存短信设置
  const handleSaveSms = async () => {
    try {
      const values = await smsForm.validateFields()
      setSaving(true)
      await adminApi.updateSettings(values)
      message.success('保存成功')
    } catch (e: any) {
      if (!e.errorFields) {
        message.error(e.message || '保存失败')
      }
    } finally {
      setSaving(false)
    }
  }

  // 保存邮箱设置
  const handleSaveEmail = async () => {
    try {
      const values = await emailForm.validateFields()
      setSaving(true)
      await adminApi.updateSettings(values)
      message.success('保存成功')
    } catch (e: any) {
      if (!e.errorFields) {
        message.error(e.message || '保存失败')
      }
    } finally {
      setSaving(false)
    }
  }

  // 保存其他设置
  const handleSaveOther = async () => {
    try {
      const values = await otherForm.validateFields()
      setSaving(true)
      await adminApi.updateSettings(values)
      message.success('保存成功')
    } catch (e: any) {
      if (!e.errorFields) {
        message.error(e.message || '保存失败')
      }
    } finally {
      setSaving(false)
    }
  }

  // ============== 支付配置相关 ==============

  const handleAddPayment = () => {
    setEditingPayment(null)
    paymentForm.resetFields()
    paymentForm.setFieldsValue({
      cost: 0,
      cost_type: 0,
      commodity: 1,
      recharge: 1,
      equipment: 0,
      sort: 0,
      status: 1,
      config: '{}',
    })
    setPaymentModalVisible(true)
  }

  const handleEditPayment = (record: adminApi.PaymentConfig) => {
    setEditingPayment(record)
    paymentForm.setFieldsValue({
      ...record,
      config: JSON.stringify(record.config || {}, null, 2),
    })
    setPaymentModalVisible(true)
  }

  const handleDeletePayment = async (id: number) => {
    try {
      await adminApi.deletePaymentSetting(id)
      message.success('删除成功')
      loadPayments()
    } catch (e) {
      console.error(e)
    }
  }

  const handlePaymentSubmit = async () => {
    try {
      const values = await paymentForm.validateFields()
      
      let config = {}
      try {
        config = JSON.parse(values.config || '{}')
      } catch (e) {
        message.error('配置JSON格式错误')
        return
      }

      const data = { ...values, config }

      if (editingPayment) {
        await adminApi.updatePaymentSetting(editingPayment.id, data)
        message.success('更新成功')
      } else {
        await adminApi.createPaymentSetting(data)
        message.success('创建成功')
      }
      setPaymentModalVisible(false)
      loadPayments()
    } catch (e) {
      console.error(e)
    }
  }

  const paymentColumns = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
    {
      title: '名称',
      key: 'name',
      render: (_: any, record: adminApi.PaymentConfig) => (
        <Space>
          {record.icon && <img src={record.icon} alt="" className="w-5 h-5" />}
          <span>{record.name}</span>
        </Space>
      ),
    },
    { title: '处理器', dataIndex: 'handler', key: 'handler', width: 100 },
    { title: '通道', dataIndex: 'code', key: 'code', width: 80 },
    {
      title: '手续费',
      key: 'cost',
      width: 100,
      render: (_: any, record: adminApi.PaymentConfig) => (
        record.cost > 0 ? (
          record.cost_type === 0 ? `¥${record.cost}` : `${record.cost * 100}%`
        ) : '-'
      ),
    },
    {
      title: '适用',
      key: 'usage',
      width: 120,
      render: (_: any, record: adminApi.PaymentConfig) => (
        <Space size={4}>
          {record.commodity === 1 && <Tag color="blue">商品</Tag>}
          {record.recharge === 1 && <Tag color="green">充值</Tag>}
        </Space>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 70,
      render: (status: number) => (
        <Tag color={status === 1 ? 'green' : 'default'}>
          {status === 1 ? '启用' : '禁用'}
        </Tag>
      ),
    },
    {
      title: '操作',
      key: 'action',
      width: 120,
      render: (_: any, record: adminApi.PaymentConfig) => (
        <Space size={4}>
          <Button type="link" icon={<EditOutlined />} size="small" onClick={() => handleEditPayment(record)} />
          <Button type="link" danger icon={<DeleteOutlined />} size="small" onClick={() => handleDeletePayment(record.id)} />
        </Space>
      ),
    },
  ]

  const handlerOptions = [
    { value: 'epay', label: '易支付' },
    { value: 'usdt', label: 'USDT支付' },
    { value: '#balance', label: '余额支付' },
  ]

  const tabItems = [
    {
      key: 'basic',
      label: '基本设置',
      children: (
        <Card className="border-0 shadow-sm rounded-xl">
          <Form form={basicForm} layout="vertical" className="max-w-3xl">
            <Title level={5}>基本设置</Title>
            
            <Form.Item name="site_logo" label="LOGO">
              <ImageUploader category="logos" />
            </Form.Item>

            <div className="grid grid-cols-2 gap-4">
              <Form.Item name="site_name" label="店铺名称">
                <Input placeholder="请输入店铺名称" />
              </Form.Item>
              <Form.Item name="site_title" label="网站标题">
                <Input placeholder="请输入网站标题" />
              </Form.Item>
            </div>

            <Form.Item name="site_keywords" label="关键词">
              <Input placeholder="请输入网站关键词" />
            </Form.Item>

            <div className="grid grid-cols-2 gap-4">
              <Form.Item name="site_bg_pc" label="PC背景图片">
                <ImageUploader category="backgrounds" />
              </Form.Item>
              <Form.Item name="site_bg_mobile" label="手机背景图片">
                <ImageUploader category="backgrounds" />
              </Form.Item>
            </div>

            <Form.Item name="site_notice" label="店铺公告">
              <TextArea rows={4} placeholder="支持HTML" />
            </Form.Item>

            <Divider />
            <Title level={5}>注册登录设置</Title>

            <div className="grid grid-cols-2 gap-4">
              <Form.Item name="register_type" label="注册方式">
                <Select>
                  <Select.Option value="username_email">用户名+邮箱</Select.Option>
                  <Select.Option value="email">仅邮箱</Select.Option>
                  <Select.Option value="phone">仅手机</Select.Option>
                </Select>
              </Form.Item>
              <Form.Item name="register_username_length" label="用户名最小长度">
                <InputNumber min={3} max={20} className="w-full" />
              </Form.Item>
            </div>

            <div className="grid grid-cols-3 gap-4">
              <Form.Item name="register_captcha" label="注册人机验证" valuePropName="checked"
                getValueFromEvent={(checked) => checked ? '1' : '0'}
                getValueProps={(value) => ({ checked: value === '1' })}
              >
                <Switch />
              </Form.Item>
              <Form.Item name="register_email_captcha" label="注册邮箱验证码" valuePropName="checked"
                getValueFromEvent={(checked) => checked ? '1' : '0'}
                getValueProps={(value) => ({ checked: value === '1' })}
              >
                <Switch />
              </Form.Item>
              <Form.Item name="register_sms_captcha" label="注册手机验证码" valuePropName="checked"
                getValueFromEvent={(checked) => checked ? '1' : '0'}
                getValueProps={(value) => ({ checked: value === '1' })}
              >
                <Switch />
              </Form.Item>
            </div>

            <div className="grid grid-cols-3 gap-4">
              <Form.Item name="login_captcha" label="登录验证码" valuePropName="checked"
                getValueFromEvent={(checked) => checked ? '1' : '0'}
                getValueProps={(value) => ({ checked: value === '1' })}
              >
                <Switch />
              </Form.Item>
              <Form.Item name="order_captcha" label="下单验证码" valuePropName="checked"
                getValueFromEvent={(checked) => checked ? '1' : '0'}
                getValueProps={(value) => ({ checked: value === '1' })}
              >
                <Switch />
              </Form.Item>
              <Form.Item name="register_enabled" label="开启注册" valuePropName="checked"
                getValueFromEvent={(checked) => checked ? '1' : '0'}
                getValueProps={(value) => ({ checked: value === '1' })}
              >
                <Switch />
              </Form.Item>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <Form.Item name="password_reset_type" label="找回密码方式">
                <Select>
                  <Select.Option value="email">邮箱验证码</Select.Option>
                  <Select.Option value="sms">手机验证码</Select.Option>
                </Select>
              </Form.Item>
              <Form.Item name="session_timeout" label="会话保持时间(秒)">
                <InputNumber min={3600} className="w-full" placeholder="86400" />
              </Form.Item>
            </div>

            <Divider />
            <Title level={5}>维护设置</Title>
            
            <Form.Item name="maintenance_mode" label="店铺维护" valuePropName="checked"
              getValueFromEvent={(checked) => checked ? '1' : '0'}
              getValueProps={(value) => ({ checked: value === '1' })}
            >
              <Switch />
            </Form.Item>
            <Form.Item name="maintenance_notice" label="维护公告">
              <TextArea rows={2} placeholder="我们正在升级，请耐心等待完成。" />
            </Form.Item>

            <div className="mt-6">
              <Button type="primary" icon={<SaveOutlined />} onClick={handleSaveBasic} loading={saving}>
                保存设置 (Save Config)
              </Button>
            </div>
          </Form>
        </Card>
      ),
    },
    {
      key: 'sms',
      label: '短信设置',
      children: (
        <Card className="border-0 shadow-sm rounded-xl">
          <Form form={smsForm} layout="vertical" className="max-w-2xl">
            <Title level={5}>短信配置</Title>
            
            <Form.Item name="sms_platform" label="短信平台">
              <Select>
                <Select.Option value="aliyun">阿里云</Select.Option>
                <Select.Option value="tencent">腾讯云</Select.Option>
              </Select>
            </Form.Item>

            <Form.Item name="sms_access_key_id" label="AccessKeyId">
              <Input placeholder="请输入accessKeyId" />
            </Form.Item>

            <Form.Item name="sms_access_key_secret" label="AccessKeySecret">
              <Input.Password placeholder="请输入accessKeySecret" />
            </Form.Item>

            <Form.Item name="sms_sign_name" label="签名名称">
              <Input placeholder="请输入签名名称" />
            </Form.Item>

            <Form.Item name="sms_template_code" label="模版CODE">
              <Input placeholder="请输入模板CODE" />
            </Form.Item>

            <div className="mt-6">
              <Space>
                <Button type="primary" danger>发送测试短信 (Send Test Message)</Button>
                <Button type="primary" icon={<SaveOutlined />} onClick={handleSaveSms} loading={saving}>
                  保存设置 (Save Config)
                </Button>
              </Space>
            </div>
          </Form>
        </Card>
      ),
    },
    {
      key: 'email',
      label: '邮箱设置',
      children: (
        <Card className="border-0 shadow-sm rounded-xl">
          <Form form={emailForm} layout="vertical" className="max-w-2xl">
            <Title level={5}>SMTP配置</Title>
            
            <Alert 
              message="本系统默认内置SMTP发信功能，如果你想使用其他邮件服务，请通过安装插件来使用。" 
              type="info" 
              showIcon 
              className="mb-4"
            />

            <Form.Item name="smtp_host" label="SMTP服务器">
              <Input placeholder="smtp.qq.com" />
            </Form.Item>

            <div className="grid grid-cols-2 gap-4">
              <Form.Item name="smtp_encryption" label="通信加密协议">
                <Select>
                  <Select.Option value="ssl">SSL</Select.Option>
                  <Select.Option value="tls">TLS</Select.Option>
                  <Select.Option value="none">无加密</Select.Option>
                </Select>
              </Form.Item>
              <Form.Item name="smtp_port" label="端口">
                <InputNumber min={1} max={65535} className="w-full" placeholder="465" />
              </Form.Item>
            </div>

            <Form.Item name="smtp_username" label="用户名">
              <Input placeholder="your-email@qq.com" />
            </Form.Item>

            <Form.Item name="smtp_password" label="授权码">
              <Input.Password placeholder="邮箱授权码" />
            </Form.Item>

            <div className="mt-6">
              <Space>
                <Button type="primary" danger>发送测试邮件 (Send Test Message)</Button>
                <Button type="primary" icon={<SaveOutlined />} onClick={handleSaveEmail} loading={saving}>
                  保存设置 (Save Config)
                </Button>
              </Space>
            </div>
          </Form>
        </Card>
      ),
    },
    {
      key: 'other',
      label: '其他设置',
      children: (
        <Card className="border-0 shadow-sm rounded-xl">
          <Form form={otherForm} layout="vertical" className="max-w-3xl">
            <Title level={5}>其他设置</Title>

            <Form.Item name="payment_callback_domain" label="自定义支付回调域名">
              <Input placeholder="自定义支付回调域名，需要带http://" />
            </Form.Item>

            <Form.Item name="site_domain" label="主站域名配置">
              <TextArea rows={2} placeholder="支持多域名,使用逗号分割" />
            </Form.Item>

            <Form.Item name="dns_cname" label="DNS-CNAME(域名解析)">
              <Input placeholder="CNAME域名" />
            </Form.Item>

            <Form.Item name="show_supplier_goods" label="主站显示其他商家商品" valuePropName="checked"
              getValueFromEvent={(checked) => checked ? '1' : '0'}
              getValueProps={(value) => ({ checked: value === '1' })}
            >
              <Switch />
            </Form.Item>

            <Divider />
            <Title level={5}>充值设置</Title>

            <div className="grid grid-cols-2 gap-4">
              <Form.Item name="recharge_min" label="单次最低充值金额">
                <InputNumber min={1} className="w-full" />
              </Form.Item>
              <Form.Item name="recharge_max" label="单次最高充值金额">
                <InputNumber min={1} className="w-full" />
              </Form.Item>
            </div>

            <Form.Item name="recharge_bonus_enabled" label="充值赠送" valuePropName="checked"
              getValueFromEvent={(checked) => checked ? '1' : '0'}
              getValueProps={(value) => ({ checked: value === '1' })}
            >
              <Switch />
            </Form.Item>

            <Form.Item name="recharge_bonus_config" label="充值赠送配置" extra="格式: 充值金额-赠送金额，每行一条">
              <TextArea rows={4} placeholder="68-12&#10;100-20&#10;188-38" />
            </Form.Item>

            <Divider />
            <Title level={5}>客服与提现</Title>

            <div className="grid grid-cols-2 gap-4">
              <Form.Item name="customer_qq" label="客服QQ(主站)">
                <Input placeholder="QQ号码" />
              </Form.Item>
              <Form.Item name="customer_url" label="网页客服地址(主站)">
                <Input placeholder="https://..." />
              </Form.Item>
            </div>

            <Form.Item name="withdraw_methods" label="提现方式" extra="多个方式用逗号分隔">
              <Input placeholder="alipay,wechat" />
            </Form.Item>

            <div className="grid grid-cols-2 gap-4">
              <Form.Item name="withdraw_fee" label="提现手续费(单笔固定)">
                <InputNumber min={0} className="w-full" />
              </Form.Item>
              <Form.Item name="withdraw_min" label="最低提现金额">
                <InputNumber min={1} className="w-full" />
              </Form.Item>
            </div>

            <Divider />
            <Title level={5}>显示设置</Title>

            <Form.Item name="category_expand" label="默认展开分类" valuePropName="checked"
              getValueFromEvent={(checked) => checked ? '1' : '0'}
              getValueProps={(value) => ({ checked: value === '1' })}
            >
              <Switch />
            </Form.Item>

            <Form.Item name="recommend_enabled" label="首页商品推荐" valuePropName="checked"
              getValueFromEvent={(checked) => checked ? '1' : '0'}
              getValueProps={(value) => ({ checked: value === '1' })}
            >
              <Switch />
            </Form.Item>

            <Form.Item name="recommend_category_name" label="推荐分类名称">
              <Input placeholder="推荐" />
            </Form.Item>

            <div className="mt-6">
              <Button type="primary" icon={<SaveOutlined />} onClick={handleSaveOther} loading={saving}>
                保存设置 (Save Config)
              </Button>
            </div>
          </Form>
        </Card>
      ),
    },
    {
      key: 'payments',
      label: '支付管理',
      children: (
        <Card className="border-0 shadow-sm rounded-xl">
          <div className="flex justify-between mb-4">
            <Title level={5} className="!mb-0">支付配置</Title>
            <Space>
              <Button icon={<ReloadOutlined />} onClick={loadPayments}>刷新</Button>
              <Button type="primary" icon={<PlusOutlined />} onClick={handleAddPayment}>添加支付</Button>
            </Space>
          </div>

          <Table
            columns={paymentColumns}
            dataSource={payments}
            rowKey="id"
            loading={loading}
            pagination={false}
            size="small"
          />
        </Card>
      ),
    },
  ]

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <Title level={4} className="!mb-0">网站设置</Title>
        <Button icon={<SettingOutlined />} onClick={handleInitSettings}>
          初始化默认配置
        </Button>
      </div>

      <Tabs items={tabItems} />

      {/* 支付配置弹窗 */}
      <Modal
        title={editingPayment ? '编辑支付方式' : '添加支付方式'}
        open={paymentModalVisible}
        onOk={handlePaymentSubmit}
        onCancel={() => setPaymentModalVisible(false)}
        width={600}
      >
        <Form form={paymentForm} layout="vertical">
          <Form.Item name="name" label="名称" rules={[{ required: true, message: '请输入名称' }]}>
            <Input placeholder="如：支付宝、微信支付" />
          </Form.Item>

          <div className="grid grid-cols-2 gap-4">
            <Form.Item name="handler" label="处理器" rules={[{ required: true }]}>
              <Select options={handlerOptions} />
            </Form.Item>
            <Form.Item name="code" label="通道编码">
              <Input placeholder="如：alipay, wxpay" />
            </Form.Item>
          </div>

          <Form.Item name="icon" label="图标URL">
            <Input placeholder="可选" />
          </Form.Item>

          <Form.Item name="config" label="配置 (JSON)" extra="根据处理器类型填写相应配置">
            <TextArea rows={6} className="font-mono" placeholder={`{\n  "url": "...",\n  "pid": "...",\n  "key": "..."\n}`} />
          </Form.Item>

          <div className="grid grid-cols-3 gap-4">
            <Form.Item name="cost" label="手续费">
              <InputNumber min={0} precision={4} className="w-full" />
            </Form.Item>
            <Form.Item name="cost_type" label="手续费类型">
              <Select>
                <Select.Option value={0}>固定金额</Select.Option>
                <Select.Option value={1}>百分比</Select.Option>
              </Select>
            </Form.Item>
            <Form.Item name="sort" label="排序">
              <InputNumber min={0} className="w-full" />
            </Form.Item>
          </div>

          <div className="grid grid-cols-3 gap-4">
            <Form.Item name="commodity" label="商品购买">
              <Select>
                <Select.Option value={1}>可用</Select.Option>
                <Select.Option value={0}>不可用</Select.Option>
              </Select>
            </Form.Item>
            <Form.Item name="recharge" label="余额充值">
              <Select>
                <Select.Option value={1}>可用</Select.Option>
                <Select.Option value={0}>不可用</Select.Option>
              </Select>
            </Form.Item>
            <Form.Item name="status" label="状态">
              <Select>
                <Select.Option value={1}>启用</Select.Option>
                <Select.Option value={0}>禁用</Select.Option>
              </Select>
            </Form.Item>
          </div>

          <Form.Item name="equipment" label="设备限制">
            <Select>
              <Select.Option value={0}>全部设备</Select.Option>
              <Select.Option value={1}>仅手机</Select.Option>
              <Select.Option value={2}>仅PC</Select.Option>
            </Select>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
