import { createContext, useContext, useState } from 'react'

const NotificationsContext = createContext<any>(null)

export function NotificationsProvider({ children }: { children: React.ReactNode }) {
    const [notifications, setNotifications] = useState([])

    return (
        <NotificationsContext.Provider value={{
            notifications,
            unreadCount: 0,
            markAsRead: () => { },
            markAllAsRead: () => { }
        }}>
            {children}
        </NotificationsContext.Provider>
    )
}

export const useNotifications = () => useContext(NotificationsContext)
