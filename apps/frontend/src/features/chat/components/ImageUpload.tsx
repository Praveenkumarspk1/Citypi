interface ImageUploadProps {
  onImages: (files: File[]) => void;
  disabled?: boolean;
}

export function ImageUpload({ onImages, disabled = false }: ImageUploadProps) {
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    if (files.length > 0) {
      onImages(files);
    }
    e.target.value = '';
  };

  return (
    <label className={`p-2 rounded-lg cursor-pointer transition-colors ${disabled ? 'opacity-50' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}>
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
      </svg>
      <input
        type="file"
        accept="image/*"
        multiple
        onChange={handleFileChange}
        disabled={disabled}
        className="hidden"
      />
    </label>
  );
}
