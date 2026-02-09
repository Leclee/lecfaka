import { useEffect, useState } from 'react'
import { Card, Typography, Button, Row, Col, Alert, message } from 'antd'
import { ShopOutlined, CheckOutlined, CloseOutlined } from '@ant-design/icons'
import api from '../../api'

const { Title, Text } = Typography

interface BusinessLevel {
  id: number
  name: string
  icon?: string
  price: number
  supplier_fee: number
  can_supply: number
  can_substation: number
  can_bindomain: number
  max_commodities: number
  status: number
}

interface ShopInfo {
  id?: number
  name?: string
  level_id?: number
  level_name?: string
  domain?: string
  subdomain?: string
}

export default function UserShop() {
  const [_loading, setLoading] = useState(true)
  const [shop, _setShop] = useState<ShopInfo | null>(null)
  const [levels, setLevels] = useState<BusinessLevel[]>([])
  const [selectedLevel, setSelectedLevel] = useState<number | null>(null)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    setLoading(true)
    try {
      // 获取商户等级列表
      const levelsRes: any = await api.get('/admin/business-levels')
      setLevels(levelsRes.items || [])
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  const handleOpenShop = async () => {
    if (!selectedLevel) {
      message.warning('请选择要开通的版本')
      return
    }
    message.info('功能开发中...')
  }

  const levelColors = ['#ffc107', '#17a2b8', '#e91e63']
  const levelIcons = ['🥉', '🥈', '🥇']

  return (
    <div>
      <Title level={4} className="flex items-center gap-2">
        <ShopOutlined /> 我的店铺
      </Title>

      {/* 当前店铺状态 */}
      <Alert
        message={shop ? `当前店铺：${shop.name}` : '您还没有开通店铺'}
        type={shop ? 'success' : 'warning'}
        showIcon
        className="mb-6 rounded-xl"
      />

      {/* 等级选择 */}
      <Card className="border-0 shadow-sm rounded-xl mb-6">
        <Text className="text-gray-500 mb-4 block">请选择</Text>
        
        <Row gutter={16}>
          {levels.slice(0, 3).map((level, idx) => (
            <Col span={8} key={level.id}>
              <div 
                className={`
                  p-4 rounded-xl cursor-pointer transition-all border-2
                  ${selectedLevel === level.id 
                    ? 'border-pink-400 bg-pink-50' 
                    : 'border-gray-200 hover:border-pink-200'
                  }
                `}
                onClick={() => setSelectedLevel(level.id)}
              >
                <div className="text-center mb-3">
                  <span className="text-2xl">{levelIcons[idx] || '👑'}</span>
                  <div className="font-bold mt-1" style={{ color: levelColors[idx] }}>
                    {level.name} ¥{level.price}
                  </div>
                </div>
                
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-500">分站功能：</span>
                    {level.can_substation ? (
                      <CheckOutlined className="text-green-500" />
                    ) : (
                      <CloseOutlined className="text-gray-300" />
                    )}
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">分站返佣：</span>
                    {level.can_substation ? (
                      <CheckOutlined className="text-green-500" />
                    ) : (
                      <CloseOutlined className="text-gray-300" />
                    )}
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">独立域名：</span>
                    {level.can_bindomain ? (
                      <CheckOutlined className="text-green-500" />
                    ) : (
                      <CloseOutlined className="text-gray-300" />
                    )}
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">供货权限：</span>
                    {level.can_supply ? (
                      <CheckOutlined className="text-green-500" />
                    ) : (
                      <CloseOutlined className="text-gray-300" />
                    )}
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">供货手续费：</span>
                    <span className="text-pink-500">{level.supplier_fee}%</span>
                  </div>
                </div>
              </div>
            </Col>
          ))}
        </Row>
      </Card>

      {/* 说明 */}
      <Card className="border-0 shadow-sm rounded-xl mb-6">
        <ul className="text-gray-500 text-sm space-y-2 list-disc list-inside">
          <li>
            <Text type="secondary">分站返佣：</Text>
            开通分站后，您在分站售出的主站商品，将按差价返还佣金（实际成交金额 - 您的拿货价 = 您的佣金）。
          </li>
          <li>
            <Text type="secondary">独立域名：</Text>
            开通分站后，您可绑定自己的顶级域名，而无需使用系统默认分配的子域名。
          </li>
          <li>
            <Text type="secondary">供货权限：</Text>
            您可自建商品分类并上架商品进行销售，主站也将协助推广与售卖。
          </li>
          <li>
            <Text type="secondary">供货手续费：</Text>
            针对您自主上架的商品，每笔成功交易将收取一定比例的手续费。
          </li>
        </ul>
      </Card>

      {/* 开通按钮 */}
      <div className="text-center">
        <Button 
          type="primary"
          size="large"
          onClick={handleOpenShop}
          disabled={!selectedLevel}
          className="px-12 h-12 rounded-xl bg-gradient-to-r from-pink-400 to-pink-500 border-0"
        >
          立即开通
        </Button>
      </div>
    </div>
  )
}
