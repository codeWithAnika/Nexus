import {
    User,
    Phone,
    Landmark,
    MapPin,
    Building2,
    Truck,
    Smartphone,
    CalendarClock,
    CalendarDays,
    FileWarning,
} from 'lucide-react'
import { ENTITY_TYPES } from '../data/mockData'

export const ENTITY_ICONS = {
    person: User,
    phone: Phone,
    account: Landmark,
    location: MapPin,
    organization: Building2,
    vehicle: Truck,
    device: Smartphone,
    event: CalendarClock,
    date: CalendarDays,
    crime_type: FileWarning,
}

export function entityColor(type) {
    if (type === 'date') return '#60a5fa'
    if (type === 'crime_type') return '#fb7185'
    return (ENTITY_TYPES[type] && ENTITY_TYPES[type].color) || '#7c869c'
}

export function entityLabel(type) {
    if (type === 'date') return 'Date'
    if (type === 'crime_type') return 'Crime Type'
    return (ENTITY_TYPES[type] && ENTITY_TYPES[type].label) || type
}

export function riskColor(level) {
    if (level === 'high') return '#e5484d'
    if (level === 'medium') return '#e8a13a'
    return '#3ecf8e'
}