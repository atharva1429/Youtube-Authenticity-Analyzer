import { useEffect, useState } from 'react'
import { motion, useSpring, useTransform } from 'framer-motion'

export default function AnimatedCounter({ value, duration = 1.2 }) {
  const spring = useSpring(0, { duration: duration * 1000, bounce: 0 })
  const display = useTransform(spring, (v) => Math.round(v))
  const [current, setCurrent] = useState(0)

  useEffect(() => {
    spring.set(value)
  }, [value, spring])

  useEffect(() => {
    return display.on('change', (v) => setCurrent(v))
  }, [display])

  return <motion.span>{current}</motion.span>
}
