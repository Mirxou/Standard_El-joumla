export interface Message {
  id: string
  text: string
  sender: "user" | "ai"
  timestamp: Date
}

export interface PiAuthResult {
  accessToken: string
  user: {
    uid: string
    username: string
  }
}

declare global {
  interface Window {
    Pi: {
      init: (config: { version: string; sandbox?: boolean }) => Promise<void>
      authenticate: (scopes: string[]) => Promise<PiAuthResult>
    }
  }
}
