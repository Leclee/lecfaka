import { useEffect, useRef } from 'react'

interface Particle {
  x: number
  y: number
  baseVx: number  // 基础速度
  baseVy: number
  vx: number
  vy: number
  radius: number
}

interface ParticleNetworkProps {
  className?: string
  particleCount?: number
  lineColor?: string
  particleColor?: string
  maxDistance?: number
  mouseRadius?: number
}

export default function ParticleNetwork({
  className = '',
  particleCount = 80,
  lineColor = 'rgba(236, 72, 153, 0.3)',
  particleColor = 'rgba(236, 72, 153, 0.6)',
  maxDistance = 120,
  mouseRadius = 150,
}: ParticleNetworkProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const particlesRef = useRef<Particle[]>([])
  const mouseRef = useRef({ x: -1000, y: -1000 })
  const animationRef = useRef<number>()

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    // 初始化粒子
    const initParticles = (width: number, height: number) => {
      const particles: Particle[] = []
      for (let i = 0; i < particleCount; i++) {
        const vx = (Math.random() - 0.5) * 1.5
        const vy = (Math.random() - 0.5) * 1.5
        particles.push({
          x: Math.random() * width,
          y: Math.random() * height,
          baseVx: vx,
          baseVy: vy,
          vx: vx,
          vy: vy,
          radius: Math.random() * 2 + 1.5,
        })
      }
      particlesRef.current = particles
    }

    // 动画循环
    const animate = () => {
      const width = canvas.width
      const height = canvas.height
      const particles = particlesRef.current
      const mouse = mouseRef.current

      // 清空画布
      ctx.clearRect(0, 0, width, height)

      // 更新和绘制粒子
      particles.forEach((particle, i) => {
        // 始终保持基础运动
        particle.vx = particle.baseVx
        particle.vy = particle.baseVy

        // 鼠标影响 - 轻微吸引但不聚集成一点
        const dx = mouse.x - particle.x
        const dy = mouse.y - particle.y
        const dist = Math.sqrt(dx * dx + dy * dy)
        
        if (dist < mouseRadius && mouse.x > 0) {
          // 轻微的吸引力，不会完全吸到鼠标位置
          const force = (mouseRadius - dist) / mouseRadius * 0.3
          // 保持一定距离，不会聚成一点
          if (dist > 30) {
            particle.vx += (dx / dist) * force
            particle.vy += (dy / dist) * force
          } else {
            // 太近时有排斥力
            particle.vx -= (dx / dist) * 0.5
            particle.vy -= (dy / dist) * 0.5
          }
        }

        // 更新位置
        particle.x += particle.vx
        particle.y += particle.vy

        // 边界穿越（从另一边出来）
        if (particle.x < 0) particle.x = width
        if (particle.x > width) particle.x = 0
        if (particle.y < 0) particle.y = height
        if (particle.y > height) particle.y = 0

        // 绘制粒子
        ctx.beginPath()
        ctx.arc(particle.x, particle.y, particle.radius, 0, Math.PI * 2)
        ctx.fillStyle = particleColor
        ctx.fill()

        // 绘制粒子之间的连线
        for (let j = i + 1; j < particles.length; j++) {
          const other = particles[j]
          const lineDx = particle.x - other.x
          const lineDy = particle.y - other.y
          const lineDist = Math.sqrt(lineDx * lineDx + lineDy * lineDy)

          if (lineDist < maxDistance) {
            const opacity = (1 - lineDist / maxDistance) * 0.6
            ctx.beginPath()
            ctx.moveTo(particle.x, particle.y)
            ctx.lineTo(other.x, other.y)
            ctx.strokeStyle = lineColor.replace(/[\d.]+\)$/, `${opacity})`)
            ctx.lineWidth = 1
            ctx.stroke()
          }
        }

        // 鼠标与粒子连线
        if (dist < mouseRadius && mouse.x > 0) {
          const opacity = (1 - dist / mouseRadius) * 0.8
          ctx.beginPath()
          ctx.moveTo(particle.x, particle.y)
          ctx.lineTo(mouse.x, mouse.y)
          ctx.strokeStyle = lineColor.replace(/[\d.]+\)$/, `${opacity})`)
          ctx.lineWidth = 1.5
          ctx.stroke()
        }
      })

      animationRef.current = requestAnimationFrame(animate)
    }

    // 调整画布大小
    const resizeCanvas = () => {
      const parent = canvas.parentElement
      if (parent) {
        // 使用 offsetWidth/offsetHeight 获取完整尺寸
        canvas.width = parent.offsetWidth || parent.clientWidth
        canvas.height = parent.offsetHeight || parent.clientHeight
        
        // 确保最小尺寸
        if (canvas.width < 100) canvas.width = parent.getBoundingClientRect().width
        if (canvas.height < 100) canvas.height = parent.getBoundingClientRect().height
        
        initParticles(canvas.width, canvas.height)
      }
    }
    
    // 使用 ResizeObserver 监听父元素大小变化
    const resizeObserver = new ResizeObserver(() => {
      resizeCanvas()
    })

    // 鼠标事件
    const handleMouseMove = (e: MouseEvent) => {
      const rect = canvas.getBoundingClientRect()
      mouseRef.current = {
        x: e.clientX - rect.left,
        y: e.clientY - rect.top,
      }
    }

    const handleMouseLeave = () => {
      mouseRef.current = { x: -1000, y: -1000 }
    }

    resizeCanvas()
    
    const parent = canvas.parentElement
    if (parent) {
      resizeObserver.observe(parent)
    }
    
    window.addEventListener('resize', resizeCanvas)
    canvas.addEventListener('mousemove', handleMouseMove)
    canvas.addEventListener('mouseleave', handleMouseLeave)

    animationRef.current = requestAnimationFrame(animate)

    return () => {
      resizeObserver.disconnect()
      window.removeEventListener('resize', resizeCanvas)
      canvas.removeEventListener('mousemove', handleMouseMove)
      canvas.removeEventListener('mouseleave', handleMouseLeave)
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current)
      }
    }
  }, [particleCount, lineColor, particleColor, maxDistance, mouseRadius])

  return (
    <canvas
      ref={canvasRef}
      className={`${className}`}
      style={{ 
        pointerEvents: 'auto',
        width: '100%',
        height: '100%',
        display: 'block',
      }}
    />
  )
}
