import { useEffect, useState } from 'react'
import { Table, Button, Input, Tabs, Tag, Card, Typography, message, Space } from 'antd'
import { SearchOutlined, ShoppingCartOutlined, LinkOutlined } from '@ant-design/icons'
import * as adminApi from '../../api/admin'

const { Title } = Typography

export default function Store() {
  const [loading, setLoading] = useState(false)
  const [data, setData] = useState<any[]>([])
  const [keyword, setKeyword] = useState('')
  const [activeTab, setActiveTab] = useState('all')

  const loadData = async () => {
    setLoading(true)
    try {
      const categoryMap: Record<string, string | undefined> = {
        all: undefined, enterprise: 'enterprise', official: 'official',
        third_party: 'third_party', free: 'free',
      }
      const typeMap: Record<string, string | undefined> = {
        extension: 'extension', payment: 'payment', theme: 'theme',
      }
      const res = await adminApi.getStorePlugins({
        category: categoryMap[activeTab],
        type: typeMap[activeTab],
        keyword: keyword || undefined,
      })
      setData(res.items || [])
    } catch {
      // store 服务器可能未部署，使用空数据
      setData([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { loadData() }, [activeTab])

  const handleInstall = async (pluginId: string) => {
    try {
      const res = await adminApi.installFromStore(pluginId)
      message.success(res.message)
    } catch (e: any) {
      message.error(e.message || '安装失败')
    }
  }

  const typeTagColor: Record<string, string> = {
    payment: 'green', theme: 'purple', extension: 'blue', notify: 'orange', delivery: 'cyan',
  }

  const columns = [
    {
      title: '软件名称',
      key: 'name',
      width: 200,
      render: (_: any, r: any) => (
        <div className="flex items-center gap-2">
          {r.icon && <img src={r.icon} alt="" className="w-8 h-8 rounded" />}
          <span className="font-medium">{r.name}</span>
        </div>
      ),
    },
    { title: '开发商', dataIndex: 'author', width: 100 },
    {
      title: '类型',
      dataIndex: 'type',
      width: 100,
      render: (t: string) => <Tag color={typeTagColor[t] || 'default'}>{t}</Tag>,
    },
    {
      title: '简介',
      dataIndex: 'description',
      ellipsis: true,
    },
    {
      title: '官网',
      dataIndex: 'website',
      width: 120,
      render: (url: string) => url ? <a href={url} target="_blank" rel="noreferrer"><LinkOutlined /> 访问</a> : '-',
    },
    { title: '版本', dataIndex: 'version', width: 80 },
    {
      title: '价格',
      dataIndex: 'price',
      width: 100,
      render: (p: number, r: any) => r.is_free ? <Tag color="green">免费</Tag> : <span className="text-red-500 font-medium">¥{p}</span>,
    },
    {
      title: '操作',
      key: 'action',
      width: 120,
      render: (_: any, r: any) => (
        <Button type="primary" size="small" icon={<ShoppingCartOutlined />} onClick={() => handleInstall(r.id)}>
          {r.is_free ? '安装' : '立即购买'}
        </Button>
      ),
    },
  ]

  const tabItems = [
    { key: 'all', label: '全部' },
    { key: 'enterprise', label: '企业版应用' },
    { key: 'official', label: '官方应用' },
    { key: 'third_party', label: '第三方应用' },
    { key: 'extension', label: '通用插件' },
    { key: 'payment', label: '支付接口' },
    { key: 'theme', label: '主题/模版' },
    { key: 'free', label: '免费应用' },
  ]

  return (
    <div>
      <Title level={4}>应用商店</Title>
      <Card className="rounded-xl border-0 shadow-sm">
        <div className="flex gap-2 mb-4 justify-center">
          <Input placeholder="搜索应用..." value={keyword} onChange={e => setKeyword(e.target.value)} onPressEnter={loadData} allowClear style={{ width: 300 }} />
          <Button type="primary" icon={<SearchOutlined />} onClick={loadData}>查询</Button>
        </div>
        <Tabs activeKey={activeTab} onChange={setActiveTab} items={tabItems} className="!mb-2" />
        <Table rowKey="id" loading={loading} dataSource={data} columns={columns} pagination={false} size="middle"
          locale={{ emptyText: data.length === 0 && !loading ? '插件商店服务器暂未部署，请先部署 lecfaka-store' : undefined }}
        />
      </Card>
    </div>
  )
}
