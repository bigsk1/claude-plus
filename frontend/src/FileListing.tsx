import React, { useState } from 'react';
import {
  Box, VStack, Text, IconButton, Switch, Flex, SimpleGrid, Table, Thead, Tbody, Tr, Th, Td, Checkbox
} from '@chakra-ui/react';
import { FaFolder, FaFile, FaList, FaTh } from 'react-icons/fa';
import { FileItem } from './types';

interface FileListingProps {
  files: FileItem[];
  onFileClick: (file: FileItem) => void;
  currentDirectory: string;
  selectedFile: string | null;
  onSelectFile: (fileName: string) => void;
}

function FileListing({ files, onFileClick, currentDirectory, selectedFile, onSelectFile }: FileListingProps) {
  const [viewMode, setViewMode] = useState<'list' | 'grid'>('list');

  const toggleViewMode = () => {
    setViewMode(viewMode === 'list' ? 'grid' : 'list');
  };

  const formatSize = (size?: string | number): string => {
    if (size === undefined || size === '-') return '-';
    const numSize = typeof size === 'string' ? parseInt(size, 10) : size;
    if (isNaN(numSize)) return '-';
    if (numSize < 1024) return `${numSize} B`;
    if (numSize < 1024 * 1024) return `${(numSize / 1024).toFixed(2)} KB`;
    if (numSize < 1024 * 1024 * 1024) return `${(numSize / (1024 * 1024)).toFixed(2)} MB`;
    return `${(numSize / (1024 * 1024 * 1024)).toFixed(2)} GB`;
  };

  const ListViewItem = ({ file }: { file: FileItem }) => (
    <Tr>
      <Td onClick={() => onFileClick(file)} style={{ cursor: 'pointer' }}>
        <Flex alignItems="center">
          {file.isDirectory ? <FaFolder color="yellow" /> : <FaFile color="lightblue" />}
          <Text ml={2}>{file.name}</Text>
        </Flex>
      </Td>
      <Td>{formatSize(file.size)}</Td>
      <Td>{file.modifiedDate || '-'}</Td>
      <Td>
        <Checkbox
          isChecked={selectedFile === file.name}
          onChange={() => onSelectFile(file.name)}
        />
      </Td>
    </Tr>
  );

  const ParentDirectoryItem = () => {
    const parentDirFile: FileItem = { name: '..', isDirectory: true, size: '-', modifiedDate: '' };
    return viewMode === 'list' ? (
      <ListViewItem file={parentDirFile} />
    ) : (
      <GridViewItem file={parentDirFile} />
    );
  };

  const GridViewItem = ({ file }: { file: FileItem }) => (
    <VStack
      p={4}
      borderRadius="md"
      borderWidth={1}
      borderColor="gray.600"
      align="center"
      spacing={2}
    >
      <Box onClick={() => onFileClick(file)} style={{ cursor: 'pointer' }}>
        {file.isDirectory ? <FaFolder size={24} color="yellow" /> : <FaFile size={24} color="lightblue" />}
        <Text fontSize="sm" textAlign="center">{file.name}</Text>
      </Box>
      <Checkbox
        isChecked={selectedFile === file.name}
        onChange={() => onSelectFile(file.name)}
      />
    </VStack>
  );


  return (
    <Box>
      <Flex justifyContent="space-between" alignItems="center" mb={4}>
        <Text fontWeight="bold">Current Directory: {currentDirectory === '.' ? 'Root' : currentDirectory}</Text>
        <Flex alignItems="center">
          <IconButton
            aria-label="Toggle view"
            icon={viewMode === 'list' ? <FaTh /> : <FaList />}
            onClick={toggleViewMode}
            mr={2}
          />
          <Switch isChecked={viewMode === 'grid'} onChange={toggleViewMode} />
        </Flex>
      </Flex>

      {viewMode === 'list' ? (
        <Table variant="simple">
          <Thead>
            <Tr>
              <Th>Name</Th>
              <Th>Size</Th>
              <Th>Modified</Th>
              <Th>Select</Th>
            </Tr>
          </Thead>
          <Tbody>
            {currentDirectory !== '.' && <ParentDirectoryItem />}
            {files.map((file) => (
              <ListViewItem key={file.name} file={file} />
            ))}
          </Tbody>
        </Table>
      ) : (
        <SimpleGrid columns={[2, 3, 4, 5]} spacing={4}>
          {currentDirectory !== '.' && <ParentDirectoryItem />}
          {files.map((file) => (
            <GridViewItem key={file.name} file={file} />
          ))}
        </SimpleGrid>
      )}
    </Box>
  );
}

export default FileListing;