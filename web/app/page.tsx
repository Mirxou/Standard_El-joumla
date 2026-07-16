"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { ArrowLeft, Zap, Layers, BarChart3, ChevronRight, Globe, Shield, Activity, Users } from "lucide-react"
import Dashboard from "@/components/dashboard"
import { motion, AnimatePresence } from "framer-motion"
import AuthGuard from "@/components/auth-guard"

export default function Home() {
  const [showDashboard, setShowDashboard] = useState(false)
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  if (!mounted) return null

  return (
    <AnimatePresence mode="wait">
      {showDashboard ? (
        <motion.div
          key="dashboard"
          initial={{ opacity: 0, scale: 0.95, filter: "blur(10px)" }}
          animate={{ opacity: 1, scale: 1, filter: "blur(0px)" }}
          transition={{ duration: 0.8, ease: "circOut" }}
          className="min-h-screen bg-background"
        >
          <AuthGuard>
            <Dashboard />
          </AuthGuard>
        </motion.div>
      ) : (
        <LandingPage onStart={() => setShowDashboard(true)} />
      )}
    </AnimatePresence>
  )
}

function LandingPage({ onStart }: { onStart: () => void }) {
  return (
    <div className="min-h-screen relative flex flex-col bg-background overflow-hidden" dir="rtl">

      {/* Background Mesh Animation */}
      <div className="absolute inset-0 z-0 bg-mesh opacity-40" />
      <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-primary/20 rounded-full blur-[120px] animate-pulse" />
      <div className="absolute bottom-0 left-0 w-[500px] h-[500px] bg-accent/20 rounded-full blur-[120px] animate-pulse-soft" />

      {/* Hero Section */}
      <main className="flex-1 relative z-10 flex flex-col items-center justify-center container mx-auto px-4 pt-20 lg:pt-32">

        {/* Badge */}
        <motion.div
          initial={{ y: -20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          className="glass-button px-4 py-1.5 rounded-full flex items-center gap-2 mb-8 cursor-default"
        >
          <span className="relative flex h-3 w-3">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-3 w-3 bg-cyan-500"></span>
          </span>
          <span className="text-sm font-medium text-cyan-100">مستقبل إدارة الأعمال 2026</span>
        </motion.div>

        {/* Headline */}
        <motion.h1
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.1 }}
          className="text-5xl lg:text-8xl font-black text-center leading-[1.1] tracking-tighter mb-6"
        >
          نُعيد صياغة <span className="text-gradient">المستقبل</span>
          <br />
          <span className="text-white">لإدارة أعمالك.</span>
        </motion.h1>

        {/* Sub-headline */}
        <motion.p
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.2 }}
          className="text-lg lg:text-2xl text-gray-400 text-center max-w-3xl mb-12 leading-relaxed font-light"
        >
          بتقنيات تسبق عصرها، نمنحك السيطرة المطلقة على المخزون والمبيعات بتجربة رقمية تفاعلية.
        </motion.p>

        {/* CTA Buttons */}
        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.3 }}
          className="flex flex-col sm:flex-row items-center gap-6 mb-20"
        >
          <div className="relative group">
            <div className="absolute -inset-1 bg-gradient-to-r from-cyan-500 to-purple-600 rounded-2xl blur opacity-40 group-hover:opacity-100 transition duration-1000 group-hover:duration-200"></div>
            <button
              onClick={onStart}
              className="relative px-8 py-4 bg-background rounded-2xl leading-none flex items-center gap-3 text-xl font-bold text-white transition-all transform group-hover:translate-x-1"
            >
              <Zap className="text-cyan-400 w-6 h-6 fill-current" />
              ابدأ رحلة القيادة الآن
            </button>
          </div>

          <button className="flex items-center gap-3 text-gray-400 hover:text-white transition-colors text-lg group">
            <span className="w-12 h-12 rounded-full border border-white/10 flex items-center justify-center group-hover:bg-white/10 transition-all">
              <span className="block w-0 h-0 border-t-[6px] border-t-transparent border-l-[10px] border-l-white border-b-[6px] border-b-transparent ml-1"></span>
            </span>
            شاهد الفيديو التعريفي
          </button>
        </motion.div>

        {/* 3D Dashboard Mockup */}
        <motion.div
          initial={{ opacity: 0, rotateX: 20, y: 100 }}
          animate={{ opacity: 1, rotateX: 10, y: 0 }}
          transition={{ duration: 1, delay: 0.4 }}
          className="w-full max-w-6xl relative perspective-1000 perspective-origin-center"
        >
          <div className="relative glass-panel rounded-t-3xl border-b-0 p-2 lg:p-4 animate-float-delayed transform-style-3d bg-slate-900/80">
            {/* Fake Dashboard UI for Immersive Effect */}
            <div className="flex items-center gap-4 mb-4 px-4">
              <div className="flex gap-2">
                <div className="w-3 h-3 rounded-full bg-red-500/80" />
                <div className="w-3 h-3 rounded-full bg-yellow-500/80" />
                <div className="w-3 h-3 rounded-full bg-green-500/80" />
              </div>
              <div className="flex-1 h-8 rounded-lg bg-white/5 border border-white/5 mx-4" />
            </div>
            <div className="grid grid-cols-12 gap-4 h-[300px] lg:h-[500px]">
              <div className="col-span-3 hidden lg:block rounded-xl bg-white/5 border border-white/5 animate-pulse-soft" />
              <div className="col-span-12 lg:col-span-9 rounded-xl bg-gradient-to-br from-cyan-500/10 to-purple-500/10 border border-white/10 relative overflow-hidden group">
                <div className="absolute inset-0 bg-grid-white/[0.02]" />
                {/* Floating Elements inside Mockup */}
                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-center">
                  <Activity className="w-16 h-16 text-cyan-500 mx-auto mb-4 animate-bounce" />
                  <h3 className="text-2xl font-bold text-white">نظامك يعمل بذكاء...</h3>
                  <p className="text-cyan-400 mt-2">جاري تحليل البيانات</p>
                </div>
              </div>
            </div>
          </div>
          {/* Reflection */}
          <div className="absolute -bottom-20 left-0 right-0 h-20 bg-gradient-to-t from-background to-transparent z-20" />
        </motion.div>
      </main>

      {/* Value Proposition Section */}
      <section className="relative z-10 py-32 container mx-auto px-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <FeatureCard
            icon={Layers}
            title="تصميم عصري"
            desc="واجهات صُممت لتلائم ذكائك؛ جمالية بصرية تلتقي مع انسيابية الاستخدام."
            delay={0.2}
          />
          <FeatureCard
            icon={Zap}
            title="أداء فائق"
            desc="ليست مجرد سرعة، بل استجابة لحظية تجعل من تعقيد البيانات عملية بسيطة."
            delay={0.4}
            active
          />
          <FeatureCard
            icon={BarChart3}
            title="تقارير ذكية"
            desc="لا تقرأ الماضي، بل توقع المستقبل. تقاريرنا تضعك دائماً في الخطوة التالية."
            delay={0.6}
          />
        </div>
      </section>

      {/* Social Proof */}
      <div className="border-t border-white/10 bg-black/20 backdrop-blur-sm py-8">
        <div className="container mx-auto text-center">
          <p className="text-gray-500 mb-6 text-sm font-medium tracking-widest uppercase">الخيار الأول للمنشآت التي ترفض التقليد</p>
          <div className="flex flex-wrap justify-center gap-12 opacity-50 grayscale hover:grayscale-0 transition-all duration-500">
            {/* Replace with actual logos or generic placeholders */}
            <div className="flex items-center gap-2 text-xl font-bold text-gray-300"><Globe className="w-5 h-5" /> GlobalCorp</div>
            <div className="flex items-center gap-2 text-xl font-bold text-gray-300"><Shield className="w-5 h-5" /> SecureSys</div>
            <div className="flex items-center gap-2 text-xl font-bold text-gray-300"><Users className="w-5 h-5" /> TeamFlow</div>
            <div className="flex items-center gap-2 text-xl font-bold text-gray-300"><Activity className="w-5 h-5" /> GrowthInc</div>
          </div>
        </div>
      </div>
    </div>
  )
}

function FeatureCard({ icon: Icon, title, desc, delay, active = false }: any) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 50 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ delay, duration: 0.6 }}
      className={`glass-card p-8 rounded-3xl relative overflow-hidden group ${active ? 'border-cyan-500/30 bg-cyan-500/5' : ''}`}
    >
      <div className={`w-14 h-14 rounded-2xl flex items-center justify-center mb-6 
        ${active ? 'bg-cyan-500 shadow-lg shadow-cyan-500/40 text-black' : 'bg-white/5 text-gray-300 group-hover:bg-white/10'}`}>
        <Icon className="w-7 h-7" />
      </div>

      <h3 className={`text-2xl font-bold mb-4 ${active ? 'text-white' : 'text-gray-200'} group-hover:text-cyan-400 transition-colors`}>
        {title}
      </h3>

      <p className="text-gray-400 leading-relaxed">
        {desc}
      </p>

      {/* Hover Gradient */}
      <div className="absolute -right-20 -bottom-20 w-40 h-40 bg-cyan-500/10 rounded-full blur-3xl group-hover:bg-cyan-500/20 transition-all duration-500" />
    </motion.div>
  )
}
