import { useEffect, useState } from 'react'
import apiClient from '../services/apiClient'

export default function useBackendStatus() {
    const [status, setStatus] = useState({ apiOnline: false, databaseReady: false, checking: true })

    useEffect(() => {
        let cancelled = false
        let timer
        const check = async() => {
            const [health, ready] = await Promise.allSettled([apiClient.get('/health'), apiClient.get('/ready')])
            if (!cancelled) {
                setStatus({
                    apiOnline: health.status === 'fulfilled' && health.value.data && health.value.data.status === 'healthy',
                    databaseReady: ready.status === 'fulfilled' && ready.value.data && ready.value.data.status === 'ready',
                    checking: false,
                })
            }
            if (!cancelled) timer = window.setTimeout(check, 15000)
        }
        const onVisibilityChange = () => { if (document.visibilityState === 'visible') check() }
        check()
        document.addEventListener('visibilitychange', onVisibilityChange)
        return () => {
            cancelled = true;
            window.clearTimeout(timer);
            document.removeEventListener('visibilitychange', onVisibilityChange)
        }
    }, [])

    return status
}