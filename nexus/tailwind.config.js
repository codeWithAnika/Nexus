/** @type {import('tailwindcss').Config} */
export default {
    content: ['./index.html', './src/**/*.{js,jsx}'],

    theme: {
        extend: {
            colors: {
                base: {
                    950: '#080B16',
                    900: '#0D1020',
                    850: '#11142A',
                    800: '#181C35',
                    700: '#23284A',
                    600: '#343A63',
                    border: '#292E52',
                },

                ink: {
                    100: '#F8FAFC',
                    300: '#B8C0D9',
                    500: '#7D86A8',
                },

                accent: {
                    DEFAULT: '#8B5CF6',
                    soft: '#A78BFA',
                    dim: '#5B3FA3',
                },

                risk: {
                    high: '#F43F5E',
                    highSoft: '#3B1724',

                    medium: '#F59E0B',
                    mediumSoft: '#3D2A12',

                    low: '#10B981',
                    lowSoft: '#12352D',
                },
            },

            fontFamily: {
                display: ['"Sora"', 'sans-serif'],
                sans: ['"Inter"', 'sans-serif'],
                mono: ['"JetBrains Mono"', 'monospace'],
            },

            boxShadow: {
                panel: '0 1px 0 0 rgba(255,255,255,0.04) inset, 0 12px 32px -12px rgba(0,0,0,0.65)',
            },
        },
    },

    plugins: [],
}