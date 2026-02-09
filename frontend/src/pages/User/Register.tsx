import { useState } from 'react'
import { useNavigate, Link, useSearchParams } from 'react-router-dom'
import { Form, Input, Button, Card, Typography, message, Divider } from 'antd'
import { UserOutlined, LockOutlined, MailOutlined, ShoppingCartOutlined, GiftOutlined } from '@ant-design/icons'
import { useAuthStore } from '../../store'

const { Title, Text } = Typography

export default function Register() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const [loading, setLoading] = useState(false)
  const { register } = useAuthStore()

  const inviteCode = searchParams.get('invite') || ''

  const onFinish = async (values: any) => {
    if (values.password !== values.confirm_password) {
      message.error('两次输入的密码不一致')
      return
    }

    setLoading(true)
    try {
      await register({
        username: values.username,
        password: values.password,
        email: values.email,
        invite_code: values.invite_code,
      })
      message.success('注册成功')
      navigate('/')
    } catch (e: any) {
      message.error(e.message || '注册失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50 flex items-center justify-center p-4">
      <Card className="w-full max-w-md rounded-2xl shadow-xl border-0">
        {/* Logo 和标题 */}
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-purple-600 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <ShoppingCartOutlined className="text-white text-3xl" />
          </div>
          <Title level={3} className="!mb-2">创建账户</Title>
          <Text type="secondary">注册 LecFaka 会员，享受更多优惠</Text>
        </div>

        <Form
          name="register"
          onFinish={onFinish}
          autoComplete="off"
          size="large"
          layout="vertical"
          initialValues={{ invite_code: inviteCode }}
        >
          <Form.Item
            name="username"
            rules={[
              { required: true, message: '请输入用户名' },
              { min: 3, message: '用户名至少3个字符' },
              { max: 20, message: '用户名最多20个字符' },
            ]}
          >
            <Input
              prefix={<UserOutlined className="text-gray-400" />}
              placeholder="用户名"
              className="rounded-lg"
            />
          </Form.Item>

          <Form.Item
            name="email"
            rules={[
              { type: 'email', message: '请输入有效的邮箱地址' },
            ]}
          >
            <Input
              prefix={<MailOutlined className="text-gray-400" />}
              placeholder="邮箱（可选）"
              className="rounded-lg"
            />
          </Form.Item>

          <Form.Item
            name="password"
            rules={[
              { required: true, message: '请输入密码' },
              { min: 6, message: '密码至少6个字符' },
            ]}
          >
            <Input.Password
              prefix={<LockOutlined className="text-gray-400" />}
              placeholder="密码"
              className="rounded-lg"
            />
          </Form.Item>

          <Form.Item
            name="confirm_password"
            rules={[{ required: true, message: '请确认密码' }]}
          >
            <Input.Password
              prefix={<LockOutlined className="text-gray-400" />}
              placeholder="确认密码"
              className="rounded-lg"
            />
          </Form.Item>

          <Form.Item name="invite_code">
            <Input
              prefix={<GiftOutlined className="text-gray-400" />}
              placeholder="邀请码（可选）"
              className="rounded-lg"
            />
          </Form.Item>

          <Form.Item className="mb-4">
            <Button
              type="primary"
              htmlType="submit"
              loading={loading}
              block
              className="h-12 rounded-lg bg-gradient-to-r from-blue-500 to-purple-600 border-0 hover:shadow-lg transition-shadow"
            >
              立即注册
            </Button>
          </Form.Item>
        </Form>

        <Divider plain>
          <Text type="secondary" className="text-sm">已有账号？</Text>
        </Divider>

        <Link to="/login">
          <Button block size="large" className="rounded-lg h-12">
            返回登录
          </Button>
        </Link>

        <div className="mt-6 text-center">
          <Link to="/" className="text-gray-500 hover:text-blue-500 text-sm">
            返回首页
          </Link>
        </div>
      </Card>
    </div>
  )
}
