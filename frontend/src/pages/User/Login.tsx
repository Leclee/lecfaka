import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { Form, Input, Button, Card, Typography, message, Divider } from 'antd'
import { UserOutlined, LockOutlined, ShoppingCartOutlined } from '@ant-design/icons'
import { useAuthStore } from '../../store'

const { Title, Text } = Typography

export default function Login() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const { login } = useAuthStore()

  const onFinish = async (values: { username: string; password: string }) => {
    setLoading(true)
    try {
      await login(values.username, values.password)
      message.success('登录成功')
      navigate('/')
    } catch (e: any) {
      message.error(e.message || '登录失败')
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
          <Title level={3} className="!mb-2">欢迎回来</Title>
          <Text type="secondary">登录您的 LecFaka 账户</Text>
        </div>

        <Form
          name="login"
          onFinish={onFinish}
          autoComplete="off"
          size="large"
          layout="vertical"
        >
          <Form.Item
            name="username"
            rules={[{ required: true, message: '请输入用户名' }]}
          >
            <Input
              prefix={<UserOutlined className="text-gray-400" />}
              placeholder="用户名 / 邮箱 / 手机号"
              className="rounded-lg"
            />
          </Form.Item>

          <Form.Item
            name="password"
            rules={[{ required: true, message: '请输入密码' }]}
          >
            <Input.Password
              prefix={<LockOutlined className="text-gray-400" />}
              placeholder="密码"
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
              登 录
            </Button>
          </Form.Item>
        </Form>

        <Divider plain>
          <Text type="secondary" className="text-sm">还没有账号？</Text>
        </Divider>

        <Link to="/register">
          <Button block size="large" className="rounded-lg h-12">
            立即注册
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
