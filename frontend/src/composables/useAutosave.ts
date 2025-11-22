import { ref, watch, onBeforeUnmount, unref, type Ref, type ComputedRef } from 'vue';
import { pageService } from '@/services/pageService';
import { useToast } from 'primevue/usetoast';

interface AutosaveOptions {
    pageId: string | Ref<string | null> | ComputedRef<string | null>;
    content: any;  // Tiptap JSON
    etag: string | null;
    debounceMs?: number;
    onConflict?: (currentEtag: string) => void;
    onEtagUpdate?: (newEtag: string) => void;
}

export function useAutosave(options: AutosaveOptions) {
    const toast = useToast();

    const {
        pageId: pageIdRef,
        content,
        etag,
        debounceMs = 5000, // Default 5 seconds
        onConflict,
        onEtagUpdate
    } = options;

    const isSaving = ref(false);
    const lastSaved = ref<Date | null>(null);
    const hasUnsavedChanges = ref(false);
    const saveError = ref<string | null>(null);

    let saveTimeout: ReturnType<typeof setTimeout> | null = null;
    let lastSavedContent: string | null = null;

    // Extract plain text from Tiptap JSON for search indexing
    const extractPlainText = (json: any): string => {
        if (!json || !json.content) return '';

        const extractFromNode = (node: any): string => {
            let text = '';

            if (node.text) {
                text += node.text;
            }

            if (node.content && Array.isArray(node.content)) {
                for (const child of node.content) {
                    text += extractFromNode(child);
                    // Add space between blocks
                    if (child.type === 'paragraph' || child.type === 'heading') {
                        text += ' ';
                    }
                }
            }

            return text;
        };

        return extractFromNode(json).trim();
    };

    // Save draft to backend
    const saveDraft = async (force = false) => {
        const pageId = unref(pageIdRef);
        if (!pageId || !content.value || isSaving.value) return;

        const currentContent = JSON.stringify(content.value);

        // Check if content actually changed
        if (!force && currentContent === lastSavedContent) {
            hasUnsavedChanges.value = false;
            return;
        }

        try {
            isSaving.value = true;
            saveError.value = null;

            const plainText = extractPlainText(content.value);

            const response = await pageService.updateDraft(
                pageId,
                content.value,
                plainText,
                etag.value || undefined
            );

            // Update etag and last saved time
            if (onEtagUpdate && response.draft_etag) {
                onEtagUpdate(response.draft_etag);
            }

            lastSaved.value = new Date();
            lastSavedContent = currentContent;
            hasUnsavedChanges.value = false;

        } catch (err: any) {
            if (err.response?.status === 409) {
                // Conflict - another user edited the page
                console.warn('Draft conflict detected');
                saveError.value = 'Editing conflict detected';

                const currentEtag = err.response.headers['etag'];
                if (onConflict && currentEtag) {
                    onConflict(currentEtag);
                } else {
                    toast.add({
                        severity: 'warn',
                        summary: 'Editing Conflict',
                        detail: 'Someone else modified this page. Please refresh.',
                        life: 5000
                    });
                }
            } else {
                console.error('Autosave failed:', err);
                saveError.value = err.message || 'Failed to save';
                toast.add({
                    severity: 'error',
                    summary: 'Save Failed',
                    detail: 'Could not save your changes. Please try again.',
                    life: 5000
                });
            }
        } finally {
            isSaving.value = false;
        }
    };

    // Debounced save function
    const debouncedSave = () => {
        hasUnsavedChanges.value = true;

        if (saveTimeout) {
            clearTimeout(saveTimeout);
        }

        saveTimeout = setTimeout(() => {
            saveDraft();
        }, debounceMs);
    };

    // Watch for content changes
    watch(
        () => content.value,
        () => {
            debouncedSave();
        },
        { deep: true }
    );

    // Save before unload if there are unsaved changes
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
        if (hasUnsavedChanges.value) {
            e.preventDefault();
            e.returnValue = '';
            // Try to save one last time
            saveDraft(true);
        }
    };

    // Add beforeunload listener
    if (typeof window !== 'undefined') {
        window.addEventListener('beforeunload', handleBeforeUnload);
    }

    // Cleanup
    onBeforeUnmount(() => {
        if (saveTimeout) {
            clearTimeout(saveTimeout);
        }

        // Final save if there are unsaved changes
        if (hasUnsavedChanges.value) {
            saveDraft(true);
        }

        if (typeof window !== 'undefined') {
            window.removeEventListener('beforeunload', handleBeforeUnload);
        }
    });

    // Manual save function (for publish, etc.)
    const saveNow = async () => {
        if (saveTimeout) {
            clearTimeout(saveTimeout);
            saveTimeout = null;
        }
        await saveDraft(true);
    };

    return {
        isSaving,
        lastSaved,
        hasUnsavedChanges,
        saveError,
        saveDraft,
        saveNow
    };
}
