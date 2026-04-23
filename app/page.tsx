'use client'
import { useRouter, usePathname } from 'next/navigation'

export default function Home() {
  const router = useRouter()
  const pathname = usePathname()

  return (
    <div key={pathname} className="flex flex-col items-center justify-center h-screen gap-6">
      <h1 className="text-3xl font-bold">모드 선택</h1>

      <div className="flex gap-4">
        <button
          onClick={() => router.replace('/dashboard')}
          className="px-6 py-3 bg-black text-white rounded-xl hover:bg-gray-800 transition"
        >
          관리자 보기
        </button>

        <button
          onClick={() => router.replace('/student')}
          className="px-6 py-3 bg-gray-200 text-black rounded-xl hover:bg-gray-300 transition"
        >
          학생 보기
        </button>
      </div>
    </div>
  )
}