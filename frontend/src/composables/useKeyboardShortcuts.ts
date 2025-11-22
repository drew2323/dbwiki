import { onMounted, onBeforeUnmount } from 'vue';

interface KeyboardShortcut {
    key: string;
    ctrl?: boolean;
    shift?: boolean;
    alt?: boolean;
    meta?: boolean;
    handler: (event: KeyboardEvent) => void;
    description?: string;
}

export function useKeyboardShortcuts(shortcuts: KeyboardShortcut[]) {
    const handleKeyDown = (event: KeyboardEvent) => {
        for (const shortcut of shortcuts) {
            const keyMatches = event.key.toLowerCase() === shortcut.key.toLowerCase();
            const ctrlMatches = shortcut.ctrl === undefined || event.ctrlKey === shortcut.ctrl;
            const shiftMatches = shortcut.shift === undefined || event.shiftKey === shortcut.shift;
            const altMatches = shortcut.alt === undefined || event.altKey === shortcut.alt;
            const metaMatches = shortcut.meta === undefined || event.metaKey === shortcut.meta;

            if (keyMatches && ctrlMatches && shiftMatches && altMatches && metaMatches) {
                event.preventDefault();
                shortcut.handler(event);
                break;
            }
        }
    };

    onMounted(() => {
        window.addEventListener('keydown', handleKeyDown);
    });

    onBeforeUnmount(() => {
        window.removeEventListener('keydown', handleKeyDown);
    });

    return {
        shortcuts
    };
}
