import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "배움동행",
  description: "학생별 학습 진행 관리와 맞춤형 수업 지원을 위한 교육 AI 시스템",
  icons: {
    icon: "/favicon.ico",
    shortcut: "/favicon.ico",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="ko"
      className="h-full antialiased"
    >
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
