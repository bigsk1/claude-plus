export interface FileItem {
  name: string;
  isDirectory: boolean;
  size?: string | number;
  modifiedDate?: string;
}
