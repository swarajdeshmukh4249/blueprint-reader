import React from 'react';

export default function ThemeToggle() {
    const toggleTheme = () => {
        const html = document.documentElement;
        html.classList.toggle('dark');
    };

    return (
        <button
            onClick={toggleTheme}
            className="fixed top-4 right-4 z-30 rounded-full bg-ink px-4 py-2 text-paper shadow-lg hover:bg-accent transition-colors"
        >
            Toggle Light/Dark
        </button>
    );
}
