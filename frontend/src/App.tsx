import { Routes, Route } from 'react-router-dom'
import { Suspense, lazy } from 'react'
import { Spin } from 'antd'

// 页面懒加载
const Install = lazy(() => import('./pages/Install'))
const Home = lazy(() => import('./pages/Home'))
const Product = lazy(() => import('./pages/Home/Product'))
const Query = lazy(() => import('./pages/Order/Query'))
const Login = lazy(() => import('./pages/User/Login'))
const Register = lazy(() => import('./pages/User/Register'))

// 用户中心
const UserLayout = lazy(() => import('./pages/User/Layout'))
const UserDashboard = lazy(() => import('./pages/User/Dashboard'))
const UserShop = lazy(() => import('./pages/User/Shop'))
const UserRecharge = lazy(() => import('./pages/User/Recharge'))
const UserOrders = lazy(() => import('./pages/User/Orders'))
const UserCoins = lazy(() => import('./pages/User/Coins'))
const UserReferrals = lazy(() => import('./pages/User/Referrals'))
const UserBills = lazy(() => import('./pages/User/Bills'))
const UserSecurity = lazy(() => import('./pages/User/Security'))

// 管理后台
const AdminLayout = lazy(() => import('./pages/Admin/Layout'))
const AdminDashboard = lazy(() => import('./pages/Admin/Dashboard'))
const AdminCommodities = lazy(() => import('./pages/Admin/Commodities'))
const AdminCards = lazy(() => import('./pages/Admin/Cards'))
const AdminOrders = lazy(() => import('./pages/Admin/Orders'))
const AdminUsers = lazy(() => import('./pages/Admin/Users'))
const AdminSettings = lazy(() => import('./pages/Admin/Settings'))
const AdminCategories = lazy(() => import('./pages/Admin/Categories'))
const AdminUserGroups = lazy(() => import('./pages/Admin/UserGroups'))
const AdminBusinessLevels = lazy(() => import('./pages/Admin/BusinessLevels'))
const AdminRechargeOrders = lazy(() => import('./pages/Admin/RechargeOrders'))
const AdminWithdrawals = lazy(() => import('./pages/Admin/Withdrawals'))
const AdminCoupons = lazy(() => import('./pages/Admin/Coupons'))
const AdminBills = lazy(() => import('./pages/Admin/Bills'))
const AdminPlugins = lazy(() => import('./pages/Admin/Plugins'))
const AdminLogs = lazy(() => import('./pages/Admin/Logs'))
const AdminStore = lazy(() => import('./pages/Admin/Store'))
const AdminPaymentPlugins = lazy(() => import('./pages/Admin/PaymentPlugins'))
const AdminPaymentSettings = lazy(() => import('./pages/Admin/PaymentSettings'))
const AdminGeneralPlugins = lazy(() => import('./pages/Admin/GeneralPlugins'))

// 加载组件
const Loading = () => (
  <div className="flex items-center justify-center min-h-screen">
    <Spin size="large" />
  </div>
)

function App() {
  return (
    <Suspense fallback={<Loading />}>
      <Routes>
        {/* 安装向导 */}
        <Route path="/install" element={<Install />} />
        
        {/* 商城前台 */}
        <Route path="/" element={<Home />} />
        <Route path="/product/:id" element={<Product />} />
        <Route path="/query" element={<Query />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        
        {/* 用户中心 */}
        <Route path="/user" element={<UserLayout />}>
          <Route index element={<UserDashboard />} />
          <Route path="shop" element={<UserShop />} />
          <Route path="recharge" element={<UserRecharge />} />
          <Route path="orders" element={<UserOrders />} />
          <Route path="coins" element={<UserCoins />} />
          <Route path="referrals" element={<UserReferrals />} />
          <Route path="bills" element={<UserBills />} />
          <Route path="security" element={<UserSecurity />} />
        </Route>
        
        {/* 管理后台 */}
        <Route path="/admin" element={<AdminLayout />}>
          <Route index element={<AdminDashboard />} />
          <Route path="users" element={<AdminUsers />} />
          <Route path="recharge" element={<AdminRechargeOrders />} />
          <Route path="withdrawals" element={<AdminWithdrawals />} />
          <Route path="user-groups" element={<AdminUserGroups />} />
          <Route path="business-levels" element={<AdminBusinessLevels />} />
          <Route path="categories" element={<AdminCategories />} />
          <Route path="commodities" element={<AdminCommodities />} />
          <Route path="cards" element={<AdminCards />} />
          <Route path="coupons" element={<AdminCoupons />} />
          <Route path="orders" element={<AdminOrders />} />
          <Route path="bills" element={<AdminBills />} />
          <Route path="logs" element={<AdminLogs />} />
          <Route path="plugins" element={<AdminPlugins />} />
          <Route path="store" element={<AdminStore />} />
          <Route path="payment-plugins" element={<AdminPaymentPlugins />} />
          <Route path="payment-settings" element={<AdminPaymentSettings />} />
          <Route path="general-plugins" element={<AdminGeneralPlugins />} />
          <Route path="settings" element={<AdminSettings />} />
        </Route>
      </Routes>
    </Suspense>
  )
}

export default App
