import { useRef, useState } from 'react';
import { Paperclip, X, FileText, Image, Film, Music, File } from 'lucide-react';
import type { CreateAttachmentData } from '../../services/messageService';

export interface PendingAttachment extends CreateAttachmentData {
  name: string;
  previewUrl?: string;
}

function getFileIcon(fileType: string) {
  if (fileType.startsWith('image/')) return Image;
  if (fileType.startsWith('video/')) return Film;
  if (fileType.startsWith('audio/')) return Music;
  if (fileType === 'application/pdf' || fileType.startsWith('text/')) return FileText;
  return File;
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

interface AttachmentChipProps {
  attachment: PendingAttachment;
  onRemove: () => void;
}

function AttachmentChip({ attachment, onRemove }: AttachmentChipProps) {
  const Icon = getFileIcon(attachment.file_type);
  const isImage = attachment.file_type.startsWith('image/');

  return (
    <div className="flex items-center gap-2 bg-gray-100 rounded-xl px-3 py-2 max-w-[200px]">
      {isImage && attachment.previewUrl ? (
        <img
          src={attachment.previewUrl}
          alt={attachment.name}
          className="w-8 h-8 rounded-lg object-cover shrink-0"
        />
      ) : (
        <div className="w-8 h-8 rounded-lg bg-white flex items-center justify-center shrink-0">
          <Icon className="w-4 h-4 text-gray-500" />
        </div>
      )}
      <div className="min-w-0 flex-1">
        <p className="text-xs font-medium text-gray-700 truncate">{attachment.name}</p>
        <p className="text-xs text-gray-400">{formatBytes(attachment.file_size)}</p>
      </div>
      <button
        onClick={onRemove}
        className="w-5 h-5 flex items-center justify-center rounded-full text-gray-400 hover:text-red-500 hover:bg-white transition-colors shrink-0"
      >
        <X className="w-3 h-3" />
      </button>
    </div>
  );
}

interface AttachmentUploaderProps {
  attachments: PendingAttachment[];
  onChange: (attachments: PendingAttachment[]) => void;
  disabled?: boolean;
  maxFiles?: number;
  maxSizeBytes?: number;
}

const DEFAULT_MAX_SIZE = 10 * 1024 * 1024;

export default function AttachmentUploader({
  attachments,
  onChange,
  disabled,
  maxFiles = 5,
  maxSizeBytes = DEFAULT_MAX_SIZE,
}: AttachmentUploaderProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [error, setError] = useState<string | null>(null);

  function handleClick() {
    if (disabled || attachments.length >= maxFiles) return;
    inputRef.current?.click();
  }

  function handleFiles(files: FileList | null) {
    if (!files) return;
    setError(null);

    const newAttachments: PendingAttachment[] = [];

    for (let i = 0; i < files.length; i++) {
      const file = files[i];

      if (attachments.length + newAttachments.length >= maxFiles) {
        setError(`Maximum ${maxFiles} files allowed`);
        break;
      }

      if (file.size > maxSizeBytes) {
        setError(`File "${file.name}" exceeds ${formatBytes(maxSizeBytes)} limit`);
        continue;
      }

      const isImage = file.type.startsWith('image/');
      const previewUrl = isImage ? URL.createObjectURL(file) : undefined;

      newAttachments.push({
        name: file.name,
        file_url: previewUrl || '',
        file_type: file.type || 'application/octet-stream',
        file_size: file.size,
        previewUrl,
      });
    }

    if (newAttachments.length > 0) {
      onChange([...attachments, ...newAttachments]);
    }

    if (inputRef.current) {
      inputRef.current.value = '';
    }
  }

  function removeAttachment(index: number) {
    const removed = attachments[index];
    if (removed.previewUrl) {
      URL.revokeObjectURL(removed.previewUrl);
    }
    const updated = attachments.filter((_, i) => i !== index);
    onChange(updated);
    setError(null);
  }

  const canAdd = !disabled && attachments.length < maxFiles;

  return (
    <div>
      <input
        ref={inputRef}
        type="file"
        multiple
        className="hidden"
        onChange={(e) => handleFiles(e.target.files)}
        disabled={disabled}
      />

      {attachments.length > 0 && (
        <div className="flex flex-wrap gap-2 px-4 pt-3 pb-1">
          {attachments.map((att, i) => (
            <AttachmentChip
              key={i}
              attachment={att}
              onRemove={() => removeAttachment(i)}
            />
          ))}
        </div>
      )}

      {error && (
        <p className="text-xs text-red-500 px-4 pt-1">{error}</p>
      )}

      <button
        type="button"
        onClick={handleClick}
        disabled={!canAdd}
        className={`w-7 h-7 flex items-center justify-center rounded-lg transition-colors ${
          canAdd
            ? 'text-gray-400 hover:text-gray-600 hover:bg-gray-200'
            : 'text-gray-300 cursor-not-allowed'
        }`}
        title={canAdd ? 'Attach file' : `Maximum ${maxFiles} files`}
      >
        <Paperclip className="w-4 h-4" />
      </button>
    </div>
  );
}
