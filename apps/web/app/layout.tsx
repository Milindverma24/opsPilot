import type { Metadata } from "next";
import "./globals.css";
import { CustomerChatWidget } from "@/components/customer/CustomerChatWidget";

export const metadata: Metadata = {
  title: "OpsPilot - Your AI Employee for Business Operations",
  description: "Autonomous business operations platform combining multi-agent reasoning, document intelligence, policy enforcement, and human-in-the-loop approvals.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full dark bg-[#030712]">
      <body className="h-full antialiased text-slate-100 bg-[#030712] selection:bg-indigo-500 selection:text-white">
        {children}
        <CustomerChatWidget />
      </body>
    </html>
  );
}
