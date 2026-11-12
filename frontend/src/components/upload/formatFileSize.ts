export function formatFileSize(bytes: number): string {
  if (bytes < 1024) return bytes + (bytes === 1 ? ' byte' : ' bytes');
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}
