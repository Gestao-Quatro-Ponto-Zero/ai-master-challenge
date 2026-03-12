<script lang="ts">
    import { marked } from 'marked';
    import DOMPurify from 'dompurify';

    let { content } = $props<{ content: string }>();

    // Configurar o marked para ser o mais fiel possível ao Github Flavored Markdown (que o usuário usou no exemplo)
    marked.setOptions({
        gfm: true,
        breaks: true
    });

    const parsedContent = $derived.by(() => {
        if (!content) return '';
        const html = marked.parse(content) as string;
        // Sanitizar para evitar XSS
        return typeof window !== 'undefined' ? DOMPurify.sanitize(html) : html;
    });
</script>

<div class="markdown-body">
    {@html parsedContent}
</div>

<style>
    .markdown-body :global(table) {
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        margin-block: 1rem;
        border: 1px solid var(--border);
        border-radius: 0.75rem;
        overflow: hidden;
        background: color-mix(in srgb, var(--secondary) 10%, transparent);
    }

    .markdown-body :global(th) {
        background: color-mix(in srgb, var(--secondary) 40%, transparent);
        padding: 0.75rem 1rem;
        text-align: left;
        font-size: 0.85rem;
        font-weight: 600;
        color: var(--primary);
        border-bottom: 1px solid var(--border);
    }

    .markdown-body :global(td) {
        padding: 0.75rem 1rem;
        font-size: 0.85rem;
        border-bottom: 1px solid color-mix(in srgb, var(--border) 40%, transparent);
        color: var(--foreground);
    }

    .markdown-body :global(tr:last-child td) {
        border-bottom: none;
    }

    .markdown-body :global(tr:hover td) {
        background: color-mix(in srgb, var(--primary) 5%, transparent);
    }

    .markdown-body :global(p) {
        margin-bottom: 0.75rem;
        line-height: 1.6;
    }

    .markdown-body :global(p:last-child) {
        margin-bottom: 0;
    }

    .markdown-body :global(code) {
        background: var(--secondary);
        padding: 0.2rem 0.4rem;
        border-radius: 0.4rem;
        font-family: inherit;
        font-weight: 500;
        color: var(--primary);
    }

    .markdown-body :global(strong) {
        font-weight: 600;
        color: var(--foreground);
    }
</style>
