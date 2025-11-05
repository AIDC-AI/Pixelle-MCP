'use client'

import "./globals.css";
import { Toaster } from "sonner";
import { RecoilRoot } from "recoil";
import { ChainlitAPI, ChainlitContext } from "@chainlit/react-client";
import { LOCAL_HOST } from "@/constans/data";

const apiClient = new ChainlitAPI(LOCAL_HOST, "webapp");

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <ChainlitContext.Provider value={apiClient}>
          <RecoilRoot>
            <Toaster position="top-center" richColors />
            {children}
          </RecoilRoot>
        </ChainlitContext.Provider>
      </body>
    </html>
  );
}
