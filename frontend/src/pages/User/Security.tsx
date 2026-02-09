import { useEffect, useState } from 'react'
import { Card, Typography, Button, Form, Input, Tabs, message, Avatar, Upload } from 'antd'
import { SafetyOutlined, UserOutlined, LockOutlined, MailOutlined, UploadOutlined } from '@ant-design/icons'
import type { UploadProps } from 'antd'
import api from '../../api'
import { useAuthStore } from '../../store/auth'

const { Title, Text } = Typography

export default function UserSecurity() {
  const [loading, setLoading] = useState(false)
  const [profileForm] = Form.useForm()
  const [passwordForm] = Form.useForm()
  const [emailForm] = Form.useForm()
  const { user, fetchUser } = useAuthStore()

  useEffect(() => {
    if (user) {
      profileForm.setFieldsValue({
        qq: user.qq,
        alipay: user.alipay,
        wechat: user.wechat,
      })
    }
  }, [user])

  const handleUpdateProfile = async (values: any) => {
    setLoading(true)
    try {
      await api.put('/users/me', values)
      message.success('保存成功')
      fetchUser()
    } catch (e: any) {
      message.error(e.message || '保存失败')
    } finally {
      setLoading(false)
    }
  }

  const handleChangePassword = async (values: any) => {
    if (values.new_password !== values.confirm_password) {
      message.error('两次密码输入不一致')
      return
    }
    
    setLoading(true)
    try {
      await api.post('/users/me/password', {
        old_password: values.old_password,
        new_password: values.new_password,
      })
      message.success('密码修改成功')
      passwordForm.resetFields()
    } catch (e: any) {
      message.error(e.message || '密码修改失败')
    } finally {
      setLoading(false)
    }
  }

  const handleUploadAvatar = async (file: File) => {
    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('category', 'avatars')
      const res = await api.post('/admin/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      await api.put('/users/me', { avatar: res.url })
      message.success('头像上传成功')
      fetchUser()
    } catch (e: any) {
      message.error(e.message || '上传失败')
    }
    return false
  }

  const uploadProps: UploadProps = {
    beforeUpload: handleUploadAvatar,
    showUploadList: false,
    accept: 'image/*',
  }

  const tabItems = [
    {
      key: 'profile',
      label: (
        <span className="flex items-center gap-1">
          <UserOutlined /> 个人资料
        </span>
      ),
      children: (
        <Form
          form={profileForm}
          layout="vertical"
          onFinish={handleUpdateProfile}
          className="max-w-md"
        >
          {/* 头像上传 */}
          <div className="mb-6">
            <Upload {...uploadProps}>
              <div className="flex items-center gap-4 cursor-pointer">
                <Avatar 
                  size={80} 
                  src={user?.avatar} 
                  icon={<UserOutlined />}
                  className="bg-pink-100"
                />
                <Button icon={<UploadOutlined />}>更换头像</Button>
              </div>
            </Upload>
          </div>

          <Form.Item name="qq" label={<span className="text-pink-500">QQ号</span>}>
            <Input placeholder="请输入QQ号" className="rounded-lg" />
          </Form.Item>

          <Form.Item name="realname" label={<span className="text-pink-500">真实姓名(提现)</span>}>
            <Input placeholder="请输入您的真实姓名" className="rounded-lg" />
          </Form.Item>

          <Form.Item label={<span className="text-pink-500">自动结算方式</span>}>
            <Input disabled value="手动提现" className="rounded-lg bg-gray-50" />
          </Form.Item>

          <Form.Item name="alipay" label={<span className="text-pink-500">支付宝账号(提现)</span>}>
            <Input placeholder="兑现使用的支付宝账号" className="rounded-lg" />
          </Form.Item>

          <Form.Item name="wechat" label={<span className="text-pink-500">微信收款二维码(提现)</span>}>
            <Upload {...uploadProps}>
              <Button icon={<UploadOutlined />}>上传二维码</Button>
            </Upload>
          </Form.Item>

          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              loading={loading}
              className="rounded-xl bg-gradient-to-r from-pink-400 to-pink-500 border-0"
            >
              保存修改
            </Button>
          </Form.Item>
        </Form>
      ),
    },
    {
      key: 'password',
      label: (
        <span className="flex items-center gap-1">
          <LockOutlined /> 密码设置
        </span>
      ),
      children: (
        <Form
          form={passwordForm}
          layout="vertical"
          onFinish={handleChangePassword}
          className="max-w-md"
        >
          <Form.Item
            name="old_password"
            label="当前密码"
            rules={[{ required: true, message: '请输入当前密码' }]}
          >
            <Input.Password placeholder="请输入当前密码" className="rounded-lg" />
          </Form.Item>

          <Form.Item
            name="new_password"
            label="新密码"
            rules={[
              { required: true, message: '请输入新密码' },
              { min: 6, message: '密码至少6位' }
            ]}
          >
            <Input.Password placeholder="请输入新密码" className="rounded-lg" />
          </Form.Item>

          <Form.Item
            name="confirm_password"
            label="确认新密码"
            rules={[{ required: true, message: '请确认新密码' }]}
          >
            <Input.Password placeholder="请再次输入新密码" className="rounded-lg" />
          </Form.Item>

          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              loading={loading}
              className="rounded-xl bg-gradient-to-r from-pink-400 to-pink-500 border-0"
            >
              修改密码
            </Button>
          </Form.Item>
        </Form>
      ),
    },
    {
      key: 'email',
      label: (
        <span className="flex items-center gap-1">
          <MailOutlined /> 邮箱设置
        </span>
      ),
      children: (
        <Form
          form={emailForm}
          layout="vertical"
          className="max-w-md"
        >
          <div className="mb-4">
            <Text type="secondary">当前绑定邮箱：</Text>
            <Text strong>{user?.email || '未绑定'}</Text>
          </div>

          <Form.Item
            name="new_email"
            label="新邮箱"
            rules={[
              { required: true, message: '请输入新邮箱' },
              { type: 'email', message: '请输入有效的邮箱地址' }
            ]}
          >
            <Input placeholder="请输入新邮箱地址" className="rounded-lg" />
          </Form.Item>

          <Form.Item
            name="code"
            label="验证码"
            rules={[{ required: true, message: '请输入验证码' }]}
          >
            <div className="flex gap-2">
              <Input placeholder="请输入验证码" className="rounded-lg flex-1" />
              <Button className="rounded-lg">发送验证码</Button>
            </div>
          </Form.Item>

          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              className="rounded-xl bg-gradient-to-r from-pink-400 to-pink-500 border-0"
            >
              绑定邮箱
            </Button>
          </Form.Item>
        </Form>
      ),
    },
  ]

  return (
    <div>
      <Title level={4} className="flex items-center gap-2">
        <SafetyOutlined /> 安全中心
      </Title>

      <Card className="border-0 shadow-sm rounded-xl">
        <Tabs items={tabItems} />
      </Card>
    </div>
  )
}
