import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Card, Steps, Form, Input, Button, Typography, Result, Spin, message } from 'antd'
import {
  RocketOutlined,
  UserOutlined,
  LockOutlined,
  MailOutlined,
  CheckCircleOutlined,
  SettingOutlined,
} from '@ant-design/icons'
import api from '../api'

const { Title, Text, Paragraph } = Typography

interface AdminData {
  username: string
  password: string
  email?: string
}

export default function Install() {
  const navigate = useNavigate()
  const [current, setCurrent] = useState(0)
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [installed, setInstalled] = useState(false)
  const [adminForm] = Form.useForm()
  const [siteForm] = Form.useForm()
  const [adminData, setAdminData] = useState<AdminData | null>(null)
  const [result, setResult] = useState<{ admin_username: string } | null>(null)

  useEffect(() => {
    checkStatus()
  }, [])

  const checkStatus = async () => {
    try {
      const data = await api.get<{ installed: boolean }>('/install/status')
      if (data.installed) {
        setInstalled(true)
      }
    } catch {
      // ignore
    } finally {
      setLoading(false)
    }
  }

  const handleInstall = async () => {
    if (!adminData) {
      message.error('请先填写管理员信息')
      setCurrent(1)
      return
    }

    try {
      const siteValues = siteForm.getFieldsValue()
      setSubmitting(true)
      const data = await api.post<{ success: boolean; admin_username: string }>('/install', {
        admin_username: adminData.username,
        admin_password: adminData.password,
        admin_email: adminData.email || null,
        site_name: siteValues.site_name || 'LecFaka',
      })
      setResult(data)
      setCurrent(3)
      message.success('安装完成')
    } catch (e: any) {
      message.error(e.message || '安装失败')
    } finally {
      setSubmitting(false)
    }
  }

  const nextStep = async () => {
    if (current === 1) {
      try {
        const values = await adminForm.validateFields()
        setAdminData({ username: values.username, password: values.password, email: values.email })
        setCurrent(2)
      } catch {
        // validation failed
      }
    } else if (current === 2) {
      await handleInstall()
    } else {
      setCurrent(current + 1)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50">
        <Spin size="large" />
      </div>
    )
  }

  if (installed) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50 p-4">
        <Card className="w-full max-w-lg rounded-2xl shadow-xl border-0">
          <Result
            status="info"
            title="系统已安装"
            subTitle="此系统已经完成安装配置，无需重复安装。"
            extra={
              <Button type="primary" size="large" onClick={() => navigate('/login')}>
                前往登录
              </Button>
            }
          />
        </Card>
      </div>
    )
  }

  const steps = [
    { title: '欢迎', icon: <RocketOutlined /> },
    { title: '管理员', icon: <UserOutlined /> },
    { title: '站点配置', icon: <SettingOutlined /> },
    { title: '完成', icon: <CheckCircleOutlined /> },
  ]

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50 flex items-center justify-center p-4">
      <Card className="w-full max-w-2xl rounded-2xl shadow-xl border-0">
        <div className="text-center mb-6">
          <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-purple-600 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <RocketOutlined className="text-white text-3xl" />
          </div>
          <Title level={3} className="!mb-1">LecFaka 安装向导</Title>
          <Text type="secondary">首次部署，请完成以下配置</Text>
        </div>

        <Steps current={current} items={steps} className="mb-8" />

        {/* Step 0: 欢迎 */}
        {current === 0 && (
          <div className="text-center py-8">
            <Title level={4}>欢迎使用 LecFaka</Title>
            <Paragraph type="secondary" className="max-w-md mx-auto">
              现代化自动发卡系统。接下来将引导您完成系统的初始化配置，
              包括创建管理员账号和基本站点设置。
            </Paragraph>
            <Paragraph type="secondary" className="text-xs mt-4">
              如果您看到此页面，说明 Docker 服务已成功启动，数据库连接正常。
            </Paragraph>
            <Button type="primary" size="large" onClick={nextStep} className="mt-4">
              开始安装
            </Button>
          </div>
        )}

        {/* Step 1: 管理员账号 */}
        {current === 1 && (
          <div className="max-w-md mx-auto">
            <Title level={4} className="text-center !mb-6">创建管理员账号</Title>
            <Form
              form={adminForm}
              layout="vertical"
              size="large"
              initialValues={adminData ? { username: adminData.username, email: adminData.email } : undefined}
            >
              <Form.Item
                name="username"
                label="管理员用户名"
                rules={[
                  { required: true, message: '请输入用户名' },
                  { min: 3, message: '用户名至少3个字符' },
                ]}
              >
                <Input prefix={<UserOutlined />} placeholder="admin" />
              </Form.Item>
              <Form.Item
                name="password"
                label="管理员密码"
                rules={[
                  { required: true, message: '请输入密码' },
                  { min: 6, message: '密码至少6个字符' },
                ]}
              >
                <Input.Password prefix={<LockOutlined />} placeholder="设置一个强密码" />
              </Form.Item>
              <Form.Item
                name="confirm_password"
                label="确认密码"
                dependencies={['password']}
                rules={[
                  { required: true, message: '请确认密码' },
                  ({ getFieldValue }) => ({
                    validator(_, value) {
                      if (!value || getFieldValue('password') === value) {
                        return Promise.resolve()
                      }
                      return Promise.reject(new Error('两次密码不一致'))
                    },
                  }),
                ]}
              >
                <Input.Password prefix={<LockOutlined />} placeholder="再次输入密码" />
              </Form.Item>
              <Form.Item name="email" label="邮箱（可选）">
                <Input prefix={<MailOutlined />} placeholder="admin@example.com" />
              </Form.Item>
            </Form>
            <div className="flex justify-between mt-4">
              <Button onClick={() => setCurrent(0)}>上一步</Button>
              <Button type="primary" onClick={nextStep}>下一步</Button>
            </div>
          </div>
        )}

        {/* Step 2: 站点配置 */}
        {current === 2 && (
          <div className="max-w-md mx-auto">
            <Title level={4} className="text-center !mb-6">站点配置</Title>
            <Form form={siteForm} layout="vertical" size="large" initialValues={{ site_name: 'LecFaka' }}>
              <Form.Item name="site_name" label="站点名称">
                <Input placeholder="LecFaka" />
              </Form.Item>
            </Form>
            <Paragraph type="secondary" className="text-xs">
              更多配置（支付方式、邮件、USDT 等）可在安装完成后进入管理后台设置。
            </Paragraph>
            <div className="flex justify-between mt-6">
              <Button onClick={() => setCurrent(1)}>上一步</Button>
              <Button type="primary" loading={submitting} onClick={nextStep}>
                {submitting ? '安装中...' : '确认安装'}
              </Button>
            </div>
          </div>
        )}

        {/* Step 3: 完成 */}
        {current === 3 && result && (
          <Result
            status="success"
            title="安装完成"
            subTitle={`管理员账号 ${result.admin_username} 已创建成功`}
            extra={[
              <Button type="primary" size="large" key="login" onClick={() => navigate('/login')}>
                前往登录
              </Button>,
              <Button size="large" key="home" onClick={() => navigate('/')}>
                访问首页
              </Button>,
            ]}
          />
        )}
      </Card>
    </div>
  )
}
