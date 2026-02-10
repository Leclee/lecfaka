import { useEffect, useState } from 'react'
import { Table, Button, Input, Tabs, Tag, Card, Typography, message, Modal, Space, Tooltip } from 'antd'
import { SearchOutlined, ShoppingCartOutlined, LinkOutlined, CopyOutlined, CheckCircleOutlined, KeyOutlined } from '@ant-design/icons'
import * as adminApi from '../../api/admin'

const { Title, Text, Paragraph } = Typography

export default function Store() {
  const [loading, setLoading] = useState(false)
  const [data, setData] = useState<any[]>([])
  const [keyword, setKeyword] = useState('')
  const [activeTab, setActiveTab] = useState('all')
  const [purchasing, setPurchasing] = useState(false)

  /** 购买结果弹窗 */
  const [purchaseResult, setPurchaseResult] = useState<{
    visible: boolean
    licenseKey?: string
    orderNo?: string
    pluginName?: string
    price?: number
    rebindLimit?: number
  }>({ visible: false })

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
      setData([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { loadData() }, [activeTab])

  /** 购买插件 */
  const handlePurchase = async (pluginId: string, pluginName: string, isFree: boolean) => {
    if (isFree) {
      // 免费插件直接安装
      try {
        const res = await adminApi.installFromStore(pluginId)
        message.success(res.message)
      } catch (e: any) {
        message.error(e.message || '安装失败')
      }
      return
    }

    // 付费插件 → 购买 → 弹窗显示授权码
    setPurchasing(true)
    try {
      const res = await adminApi.purchasePlugin(pluginId)
      if (res.success && res.license_key) {
        setPurchaseResult({
          visible: true,
          licenseKey: res.license_key,
          orderNo: res.order_no,
          pluginName: res.plugin_name || pluginName,
          price: res.price,
          rebindLimit: res.rebind_limit,
        })
        loadData() // 刷新列表
      } else {
        message.error(res.message || '购买失败')
      }
    } catch (e: any) {
      message.error(e.message || '购买失败，请检查商店服务器是否正常')
    } finally {
      setPurchasing(false)
    }
  }

  /** 复制授权码 */
  const copyLicenseKey = () => {
    if (purchaseResult.licenseKey) {
      navigator.clipboard.writeText(purchaseResult.licenseKey)
      message.success('授权码已复制到剪贴板')
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
        <Button
          type="primary"
          size="small"
          icon={r.is_free ? <ShoppingCartOutlined /> : <KeyOutlined />}
          loading={purchasing}
          onClick={() => handlePurchase(r.id, r.name, r.is_free)}
        >
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

      {/* 购买成功弹窗 */}
      <Modal
        title={
          <Space>
            <CheckCircleOutlined style={{ color: '#52c41a', fontSize: 20 }} />
            <span>购买成功</span>
          </Space>
        }
        open={purchaseResult.visible}
        onCancel={() => setPurchaseResult({ visible: false })}
        footer={[
          <Button key="copy" type="primary" icon={<CopyOutlined />} onClick={copyLicenseKey}>
            复制授权码
          </Button>,
          <Button key="close" onClick={() => setPurchaseResult({ visible: false })}>
            关闭
          </Button>,
        ]}
        width={520}
      >
        <div style={{ padding: '16px 0' }}>
          <Paragraph>
            <Text strong>插件：</Text> {purchaseResult.pluginName}
          </Paragraph>
          {purchaseResult.price !== undefined && purchaseResult.price > 0 && (
            <Paragraph>
              <Text strong>价格：</Text> <Text type="danger">¥{purchaseResult.price}</Text>
            </Paragraph>
          )}
          <Paragraph>
            <Text strong>订单号：</Text> <Text copyable>{purchaseResult.orderNo}</Text>
          </Paragraph>

          <div style={{
            background: '#f6ffed',
            border: '1px solid #b7eb8f',
            borderRadius: 8,
            padding: '16px 20px',
            margin: '16px 0',
            textAlign: 'center',
          }}>
            <Text type="secondary" style={{ fontSize: 12 }}>您的授权码</Text>
            <div style={{ margin: '8px 0' }}>
              <Tooltip title="点击复制">
                <Text
                  strong
                  style={{ fontSize: 20, letterSpacing: 1, cursor: 'pointer' }}
                  onClick={copyLicenseKey}
                >
                  {purchaseResult.licenseKey}
                </Text>
              </Tooltip>
            </div>
            <Text type="secondary" style={{ fontSize: 12 }}>
              可换绑域名 {purchaseResult.rebindLimit || 3} 次 · 首次激活自动绑定当前域名
            </Text>
          </div>

          <Paragraph type="secondary" style={{ fontSize: 13 }}>
            请前往 <Text strong>系统管理 → 插件管理</Text> 找到该插件，输入授权码并启用。
          </Paragraph>
        </div>
      </Modal>
    </div>
  )
}
